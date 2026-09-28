"""Справочник кейсодержателя на демо-стенде: вендоры с контактами и курсы из выгрузки оплат.

Вендоры, продукты и контакты — из таблицы «Вендоры», которую прислал кейсодержатель: люди
в ней вымышленные (домен example.ru), поэтому им место в демо-данных. Курсы — названия из его
выгрузки оплат; самих оплат здесь нет: в них почта людей, и загружаются они на стенде через
`POST /api/v1/payments/import`, как и настоящая выгрузка платёжной системы.

Повторный запуск ничего не дублирует.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import crypto
from app.modules.catalogs.models import Direction, Product, Program, ProgramProduct, Vendor
from app.modules.imports.mapping import normalize
from app.modules.vendors import service as vendors_service

# Компания, продукты, ФИО, телефон, почта, способы связи — строка таблицы «Вендоры».
CASE_VENDORS: tuple[tuple[str, tuple[str, ...], str, str, str, tuple[str, ...]], ...] = (
    ("ООО «Базис»", ("Базис Dynamix",), "Иванов Иван Иванович",
     "+7 (900) 111-22-33", "ivanov.ii@example.ru", ("email", "telegram")),
    ("ООО «ТДата»", ("RT.DataLake", "RT.Warehouse"), "Смирнова Анна Петровна",
     "+7 (911) 222-33-44", "smirnova.ap@example.ru", ("telegram",)),
    ("ПАО «Ростелеком»", ("RT.DataVision",), "Кузнецов Дмитрий Сергеевич",
     "+7 (922) 333-44-55", "kuznetsov.ds@example.ru", ("telegram",)),
    ("ООО «РТК ИТ Плюс»", ("AKOLA",), "Попова Мария Владимировна",
     "+7 (933) 444-55-66", "popova.mv@example.ru", ("telegram",)),
    ("ООО «РТК ИТ Плюс»", ("Яга",), "Соколов Алексей Андреевич",
     "+7 (944) 555-66-77", "sokolov.aa@example.ru", ("telegram",)),
    ("ООО «РТК ИТ»", ("Web3Gate",), "Лебедева Елена Дмитриевна",
     "+7 (955) 666-77-88", "lebedeva.ed@example.ru", ("telegram",)),
    ("ООО «РТК ИТ»", ("Аврора SDK",), "Козлов Максим Игоревич",
     "+7 (966) 777-88-99", "kozlov.mi@example.ru", ("telegram",)),
    ("ООО «РТК ИТ»", ("Нейрошлюз",), "Новикова Ольга Александровна",
     "+7 (977) 888-99-00", "novikova.oa@example.ru", ("email",)),
)  # fmt: skip

CASE_DIRECTIONS: tuple[tuple[str, str], ...] = (("testing", "Тестирование ПО"),)

# Курсы из выгрузки оплат → направление и продукт. Управление проектами идёт с «Ягой»,
# остальные курсы продуктонезависимые.
CASE_COURSES: tuple[tuple[str, str, tuple[str, str] | None], ...] = (
    ("Анализ данных без программирования", "data_analysis", None),
    ("Инженер-тестировщик", "testing", None),
    (
        "Управление ИТ-проектами на базе программного продукта ПАО «Ростелеком»",
        "project_management",
        ("ООО «РТК ИТ Плюс»", "Яга"),
    ),
    ("Промпт-инжиниринг", "ai", None),
    ("Python-разработчик с использованием инструментов ИИ", "ai", None),
)


async def seed_case_catalog(session: AsyncSession) -> None:
    vendors = {normalize(item.name): item for item in await session.scalars(select(Vendor))}
    products = {
        (item.vendor_id, normalize(item.name)): item
        for item in await session.scalars(select(Product))
    }

    async def product_of(vendor_name: str, name: str) -> Product:
        vendor = vendors.get(normalize(vendor_name))
        if vendor is None:
            vendor = Vendor(name=vendor_name)
            session.add(vendor)
            await session.flush()
            vendors[normalize(vendor_name)] = vendor
        product = products.get((vendor.id, normalize(name)))
        if product is None:
            product = Product(vendor_id=vendor.id, name=name)
            session.add(product)
            await session.flush()
            products[(vendor.id, normalize(name))] = product
        return product

    # Без ключа шифрования демо-данные грузятся без почты и телефонов, как и остальные ПДн стенда.
    encrypt = crypto.is_configured()
    for company, names, full_name, phone, email, channels in CASE_VENDORS:
        linked = [await product_of(company, name) for name in names]
        await vendors_service.upsert_contact(
            session,
            vendors[normalize(company)],
            linked,
            full_name,
            email if encrypt else None,
            phone if encrypt else None,
            list(channels),
        )

    directions = {item.code: item for item in await session.scalars(select(Direction))}
    for code, name in CASE_DIRECTIONS:
        if code not in directions:
            directions[code] = Direction(code=code, name=name)
            session.add(directions[code])
    await session.flush()

    programs = {normalize(item.name): item for item in await session.scalars(select(Program))}
    for course, direction_code, product_ref in CASE_COURSES:
        program = programs.get(normalize(course))
        if program is None:
            program = Program(direction_id=directions[direction_code].id, name=course)
            session.add(program)
            await session.flush()
            programs[normalize(course)] = program
        if product_ref is None:
            continue
        product = await product_of(*product_ref)
        if await session.get(ProgramProduct, (program.id, product.id)) is None:
            # Единственная связь курса и так основная для него; основной парой продукта
            # остаётся прежняя программа, поэтому флаг не ставим.
            session.add(ProgramProduct(program_id=program.id, product_id=product.id))
    await session.flush()
