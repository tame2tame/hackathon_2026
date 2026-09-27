"""Справочники файлом: загрузка JSON, CSV, XLSX или XLS с предпросмотром и выгрузка обратно.

Данные готовятся заранее и подгружаются в закрытом контуре, без обогащения из интернета: так жюри
описало работу со справочниками. Строка находит запись по естественному ключу (название вуза, код
направления, программа в направлении, вендор и продукт), поэтому повторная загрузка того же файла
ничего не дублирует, а пустая ячейка не стирает уже заполненное поле.
"""

import json
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import UploadFile
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import cache
from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.core.security import CurrentUser
from app.modules.audit.models import AuditLog
from app.modules.catalogs.models import (
    Direction,
    Product,
    Program,
    ProgramProduct,
    University,
    Vendor,
)
from app.modules.imports import files
from app.modules.imports.files import (
    EXPORT_TYPES,
    Action,
    FieldSpec,
    ImportOutcome,
    RowError,
    RowResult,
)
from app.modules.imports.mapping import normalize, short_name
from app.modules.reports import renderers

TRUE_VALUES = {"да", "true", "1", "yes", "+", "истина"}
FALSE_VALUES = {"нет", "false", "0", "no", "-", "ложь", ""}


SPECS: dict[str, tuple[FieldSpec, ...]] = {
    "universities": (
        FieldSpec("name", "Название", True, aliases=("Название вуза", "Вуз", "Наименование")),
        FieldSpec("short_name", "Сокращение", aliases=("Краткое название", "Аббревиатура")),
        FieldSpec("region", "Регион"),
        FieldSpec("city", "Город"),
        FieldSpec("is_priority2030", "Приоритет 2030", is_bool=True),
    ),
    "directions": (
        FieldSpec("code", "Код", True),
        FieldSpec("name", "Название", True, aliases=("Направление",)),
    ),
    "programs": (
        FieldSpec("direction_code", "Код направления", True),
        FieldSpec("name", "Название", True, aliases=("Программа",)),
        FieldSpec("lms_course_ref", "Курс в LMS"),
        FieldSpec("priority", "Приоритет"),
    ),
    "vendors": (FieldSpec("name", "Название", True, aliases=("Вендор", "Правообладатель")),),
    "products": (
        FieldSpec("vendor", "Вендор", True, aliases=("Правообладатель",)),
        FieldSpec("name", "Название", True, aliases=("Продукт", "ПО")),
    ),
    "program-products": (
        FieldSpec("direction_code", "Код направления", True),
        FieldSpec("program", "Программа", True),
        FieldSpec("vendor", "Вендор", True),
        FieldSpec("product", "Продукт", True, aliases=("ПО",)),
        FieldSpec("is_default", "По умолчанию", is_bool=True),
    ),
}


# Естественный ключ записи: по нему загрузка находит существующую запись и дубли внутри файла.
KEY_FIELDS: dict[str, tuple[str, ...]] = {
    "universities": ("name",),
    "directions": ("code",),
    "programs": ("direction_code", "name"),
    "vendors": ("name",),
    "products": ("vendor", "name"),
    "program-products": ("direction_code", "program", "vendor", "product"),
}


def specs_of(kind: str) -> tuple[FieldSpec, ...]:
    specs = SPECS.get(kind)
    if specs is None:
        raise AppError(
            ErrorCode.NOT_FOUND,
            f"Неизвестный справочник: {kind}. Есть: {', '.join(SPECS)}.",
        )
    return specs


def _priority(value: str) -> int:
    if not value.strip():
        return 0
    try:
        priority = int(value.strip())
    except ValueError as error:
        raise RowError(f"Приоритет — число от 0 до 100, а не «{value}»") from error
    if not 0 <= priority <= 100:
        raise RowError("Приоритет — число от 0 до 100")
    return priority


def _bool(value: str) -> bool:
    lowered = value.strip().casefold()
    if lowered in TRUE_VALUES:
        return True
    if lowered in FALSE_VALUES:
        return False
    raise RowError(f"Не понятно, да или нет: «{value}»")


def _set(target: Any, attribute: str, value: Any, changed: list[str]) -> None:
    if getattr(target, attribute) != value:
        setattr(target, attribute, value)
        changed.append(attribute)


def _restore(target: Any, changed: list[str]) -> None:
    if target.archived_at is not None:
        target.archived_at = None
        changed.append("archived_at")


@dataclass(slots=True)
class _Index:
    """Справочники в памяти на одну загрузку: строки не перечитывают таблицы заново."""

    session: AsyncSession
    universities: dict[str, University]
    directions: dict[str, Direction]
    programs: dict[tuple[uuid.UUID, str], Program]
    vendors: dict[str, Vendor]
    products: dict[tuple[uuid.UUID, str], Product]

    @classmethod
    async def load(cls, session: AsyncSession) -> "_Index":
        return cls(
            session=session,
            universities={
                normalize(item.name): item for item in await session.scalars(select(University))
            },
            directions={item.code: item for item in await session.scalars(select(Direction))},
            programs={
                (item.direction_id, normalize(item.name)): item
                for item in await session.scalars(select(Program))
            },
            vendors={normalize(item.name): item for item in await session.scalars(select(Vendor))},
            products={
                (item.vendor_id, normalize(item.name)): item
                for item in await session.scalars(select(Product))
            },
        )

    def direction(self, code: str) -> Direction:
        direction = self.directions.get(code.casefold())
        if direction is None:
            raise RowError(f"Нет направления с кодом «{code}»: загрузите сначала направления")
        return direction


RowHandler = Callable[[_Index, dict[str, str]], Awaitable[tuple[str, Action, str | None]]]


def _outcome(label: str, changed: list[str]) -> tuple[str, Action, str | None]:
    return label, ("updated" if changed else "unchanged"), ", ".join(changed) or None


async def _university(index: _Index, values: dict[str, str]) -> tuple[str, Action, str | None]:
    name = values["name"]
    existing = index.universities.get(normalize(name))
    if existing is None:
        university = University(
            name=name[:300],
            short_name=(values.get("short_name") or short_name(name))[:60],
            region=(values.get("region") or "Не указан")[:120],
            city=values.get("city") or None,
            is_priority2030=_bool(values.get("is_priority2030", "")),
        )
        index.session.add(university)
        index.universities[normalize(name)] = university
        return name, "created", None
    changed: list[str] = []
    for attribute in ("short_name", "region", "city"):
        if values.get(attribute):
            _set(existing, attribute, values[attribute], changed)
    if values.get("is_priority2030"):
        _set(existing, "is_priority2030", _bool(values["is_priority2030"]), changed)
    _restore(existing, changed)
    return _outcome(name, changed)


async def _direction(index: _Index, values: dict[str, str]) -> tuple[str, Action, str | None]:
    code = values["code"].casefold()[:60]
    existing = index.directions.get(code)
    if existing is None:
        direction = Direction(code=code, name=values["name"][:200])
        index.session.add(direction)
        index.directions[code] = direction
        return code, "created", None
    changed: list[str] = []
    _set(existing, "name", values["name"][:200], changed)
    _restore(existing, changed)
    return _outcome(code, changed)


async def _program(index: _Index, values: dict[str, str]) -> tuple[str, Action, str | None]:
    direction = index.direction(values["direction_code"])
    key = f"{direction.code} / {values['name']}"
    existing = index.programs.get((direction.id, normalize(values["name"])))
    if existing is None:
        program = Program(
            direction_id=direction.id,
            name=values["name"][:300],
            lms_course_ref=values.get("lms_course_ref") or None,
            priority=_priority(values.get("priority", "")),
        )
        index.session.add(program)
        index.programs[(direction.id, normalize(values["name"]))] = program
        return key, "created", None
    changed: list[str] = []
    if values.get("lms_course_ref"):
        _set(existing, "lms_course_ref", values["lms_course_ref"][:120], changed)
    if values.get("priority"):
        _set(existing, "priority", _priority(values["priority"]), changed)
    _restore(existing, changed)
    return _outcome(key, changed)


async def _vendor(index: _Index, values: dict[str, str]) -> tuple[str, Action, str | None]:
    existing = index.vendors.get(normalize(values["name"]))
    if existing is None:
        vendor = Vendor(name=values["name"][:200])
        index.session.add(vendor)
        index.vendors[normalize(values["name"])] = vendor
        return values["name"], "created", None
    changed: list[str] = []
    _restore(existing, changed)
    return _outcome(values["name"], changed)


async def _product(index: _Index, values: dict[str, str]) -> tuple[str, Action, str | None]:
    key = f"{values['vendor']} / {values['name']}"
    vendor = index.vendors.get(normalize(values["vendor"]))
    detail = None
    if vendor is None:
        # В таблицах заказчика вендор идёт колонкой рядом с продуктом: заводим его сразу.
        vendor = Vendor(name=values["vendor"][:200])
        index.session.add(vendor)
        await index.session.flush()
        index.vendors[normalize(values["vendor"])] = vendor
        detail = f"добавлен вендор «{vendor.name}»"
    existing = index.products.get((vendor.id, normalize(values["name"])))
    if existing is None:
        product = Product(vendor_id=vendor.id, name=values["name"][:200])
        index.session.add(product)
        index.products[(vendor.id, normalize(values["name"]))] = product
        return key, "created", detail
    changed: list[str] = []
    _restore(existing, changed)
    return _outcome(key, changed)


async def _refuse_second_default(session: AsyncSession, program: Program, product: Product) -> None:
    """Основная пара одна у программы и одна у продукта: иначе выбор по ней случаен."""
    other = (
        await session.execute(
            select(Program.name, Product.name)
            .select_from(ProgramProduct)
            .join(Program, Program.id == ProgramProduct.program_id)
            .join(Product, Product.id == ProgramProduct.product_id)
            .where(
                ProgramProduct.is_default.is_(True),
                or_(
                    ProgramProduct.program_id == program.id,
                    ProgramProduct.product_id == product.id,
                ),
                ~and_(
                    ProgramProduct.program_id == program.id,
                    ProgramProduct.product_id == product.id,
                ),
            )
            .limit(1)
        )
    ).first()
    if other is not None:
        raise RowError(
            f"Основная пара уже задана: «{other[0]}» ← «{other[1]}». Снимите с неё флаг, "
            "у программы и у продукта основная пара одна"
        )


async def _program_product(index: _Index, values: dict[str, str]) -> tuple[str, Action, str | None]:
    key = f"{values['program']} ← {values['vendor']} / {values['product']}"
    direction = index.direction(values["direction_code"])
    program = index.programs.get((direction.id, normalize(values["program"])))
    if program is None:
        raise RowError(f"Нет программы «{values['program']}» в направлении «{direction.code}»")
    vendor = index.vendors.get(normalize(values["vendor"]))
    product = index.products.get((vendor.id, normalize(values["product"]))) if vendor else None
    if product is None:
        raise RowError(f"Нет продукта «{values['vendor']} / {values['product']}»")
    is_default = _bool(values.get("is_default", ""))
    if is_default:
        await _refuse_second_default(index.session, program, product)
    link = await index.session.get(ProgramProduct, (program.id, product.id))
    if link is None:
        index.session.add(
            ProgramProduct(program_id=program.id, product_id=product.id, is_default=is_default)
        )
        return key, "created", None
    changed: list[str] = []
    _set(link, "is_default", is_default, changed)
    return _outcome(key, changed)


HANDLERS: dict[str, RowHandler] = {
    "universities": _university,
    "directions": _direction,
    "programs": _program,
    "vendors": _vendor,
    "products": _product,
    "program-products": _program_product,
}


def _row_key(kind: str, values: dict[str, str]) -> str:
    return "|".join(normalize(values.get(name, "")) for name in KEY_FIELDS[kind])


async def import_catalog(
    session: AsyncSession,
    admin: CurrentUser,
    kind: str,
    upload: UploadFile,
    dry_run: bool,
    encoding: str | None = None,
    trace_id: str | None = None,
) -> ImportOutcome:
    """Разбирает файл и применяет строки; при `dry_run` всё откатывается — это предпросмотр."""
    specs = specs_of(kind)
    content = await upload.read()
    settings = get_settings()
    if len(content) > settings.max_upload_bytes:
        raise AppError(ErrorCode.FILE_TOO_LARGE, f"Файл больше {settings.max_upload_mb} МБ.")
    rows = files.records(upload.filename or "", content, encoding, "Справочник")
    files.check_columns(specs, rows)

    outcome = ImportOutcome(kind=kind, dry_run=dry_run)
    seen: set[str] = set()
    savepoint = await session.begin_nested()
    index = await _Index.load(session)
    for row_no, raw in enumerate(rows, start=1):
        values = files.normalized(specs, raw)
        missing = [spec.label for spec in specs if spec.required and not values.get(spec.name)]
        if missing:
            outcome.rows.append(
                RowResult(row_no, "", "error", f"Не заполнено: {', '.join(missing)}")
            )
            continue
        key = _row_key(kind, values)
        if key in seen:
            outcome.rows.append(
                RowResult(row_no, key, "error", "Та же запись уже есть выше в файле")
            )
            continue
        seen.add(key)
        try:
            async with session.begin_nested():
                label, action, detail = await HANDLERS[kind](index, values)
                await session.flush()
        except RowError as error:
            outcome.rows.append(RowResult(row_no, key, "error", str(error)))
        else:
            outcome.rows.append(RowResult(row_no, label, action, detail))

    if dry_run:
        await savepoint.rollback()
        return outcome
    await savepoint.commit()
    session.add(
        AuditLog(
            actor_user_id=admin.id,
            action="admin.catalog_imported",
            entity_kind=kind,
            after={
                "file": (upload.filename or "")[:200],
                "created": outcome.count("created"),
                "updated": outcome.count("updated"),
                "unchanged": outcome.count("unchanged"),
                "errors": outcome.count("error"),
            },
            trace_id=trace_id,
        )
    )
    await session.commit()
    await cache.invalidate(cache.CATALOGS)
    if kind == "programs":
        # В файле программ есть приоритет, а он виден в рейтинге.
        await cache.invalidate(cache.RATING)
    return outcome


async def _export_rows(
    session: AsyncSession, kind: str, include_archived: bool
) -> list[dict[str, str]]:
    def active(model: Any) -> Any:
        return True if include_archived else model.archived_at.is_(None)

    match kind:
        case "universities":
            return [
                {
                    "name": item.name,
                    "short_name": item.short_name,
                    "region": item.region,
                    "city": item.city or "",
                    "is_priority2030": "да" if item.is_priority2030 else "нет",
                }
                for item in await session.scalars(
                    select(University).where(active(University)).order_by(University.name)
                )
            ]
        case "directions":
            return [
                {"code": item.code, "name": item.name}
                for item in await session.scalars(
                    select(Direction).where(active(Direction)).order_by(Direction.code)
                )
            ]
        case "programs":
            programs = await session.execute(
                select(Program, Direction)
                .join(Direction, Direction.id == Program.direction_id)
                .where(active(Program))
                .order_by(Direction.code, Program.name)
            )
            return [
                {
                    "direction_code": direction.code,
                    "name": program.name,
                    "lms_course_ref": program.lms_course_ref or "",
                    "priority": str(program.priority),
                }
                for program, direction in programs.tuples()
            ]
        case "vendors":
            return [
                {"name": item.name}
                for item in await session.scalars(
                    select(Vendor).where(active(Vendor)).order_by(Vendor.name)
                )
            ]
        case "products":
            products = await session.execute(
                select(Product, Vendor)
                .join(Vendor, Vendor.id == Product.vendor_id)
                .where(active(Product))
                .order_by(Vendor.name, Product.name)
            )
            return [
                {"vendor": vendor.name, "name": product.name}
                for product, vendor in products.tuples()
            ]
        case _:
            links = await session.execute(
                select(ProgramProduct, Program, Direction, Product, Vendor)
                .join(Program, Program.id == ProgramProduct.program_id)
                .join(Direction, Direction.id == Program.direction_id)
                .join(Product, Product.id == ProgramProduct.product_id)
                .join(Vendor, Vendor.id == Product.vendor_id)
                .order_by(Direction.code, Program.name, Vendor.name, Product.name)
            )
            return [
                {
                    "direction_code": direction.code,
                    "program": program.name,
                    "vendor": vendor.name,
                    "product": product.name,
                    "is_default": "да" if link.is_default else "нет",
                }
                for link, program, direction, product, vendor in links.tuples()
            ]


async def export_catalog(
    session: AsyncSession,
    kind: str,
    fmt: Literal["json", "csv", "xlsx"],
    encoding: Literal["utf-8", "windows-1251"] = "utf-8",
    include_archived: bool = False,
) -> tuple[bytes, str, str]:
    """Файл справочника в том виде, в каком его принимает загрузка: байты, тип и имя файла."""
    specs = specs_of(kind)
    rows = await _export_rows(session, kind, include_archived)
    stamp = datetime.now(UTC).strftime("%Y-%m-%d")
    file_name = f"{kind}-{stamp}.{fmt}"
    if fmt == "json":
        items = [
            {
                spec.name: (row[spec.name] == "да" if spec.is_bool else row[spec.name])
                for spec in specs
            }
            for row in rows
        ]
        content = json.dumps({"kind": kind, "items": items}, ensure_ascii=False, indent=2)
        return content.encode("utf-8"), EXPORT_TYPES["json"], file_name
    headers = [spec.label for spec in specs]
    table = [[row[spec.name] for spec in specs] for row in rows]
    if fmt == "csv":
        media = f"{EXPORT_TYPES['csv']}; charset={encoding}"
        return renderers.render("csv", headers, table, kind, encoding), media, file_name
    return renderers.render("xlsx", headers, table, kind), EXPORT_TYPES["xlsx"], file_name
