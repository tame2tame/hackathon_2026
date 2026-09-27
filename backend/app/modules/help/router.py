from fastapi import APIRouter, Response

from app.core.errors import ErrorCode, error_responses
from app.core.http_cache import IMMUTABLE
from app.core.security import CurrentUserDep
from app.modules.help.schemas import HelpTopicOut, HelpTopicRef
from app.modules.help.service import get_topic, image_path, list_topics

router = APIRouter(prefix="/api/v1/help", tags=["help"])


@router.get(
    "",
    summary="Разделы встроенной справки",
    description=(
        "Руководство пользователя внутри продукта. Разделы отдаются по роли: то, что настраивает "
        "администратор, КАМу не показывается."
    ),
    responses=error_responses(ErrorCode.AUTH_REQUIRED),
)
async def read_topics(user: CurrentUserDep) -> list[HelpTopicRef]:
    return list_topics(user.role)


@router.get(
    "/images/{name}",
    summary="Картинка из справки",
    description=(
        "Скриншоты экранов, на которые ссылаются разделы руководства. Отдаются без входа: "
        "на них только синтетические демо-данные, а `<img>` не умеет слать токен."
    ),
    response_class=Response,
    responses={
        200: {"content": {"image/png": {}}, "description": "Изображение"},
        **error_responses(ErrorCode.NOT_FOUND),
    },
)
async def read_image(name: str) -> Response:
    # Вход не нужен: это снимки экранов на синтетических данных, а тег <img>, в который
    # превращается Markdown справки, заголовок Authorization не отправляет.
    # Картинка не меняется без нового имени файла: её можно держать в кэше сутки.
    return Response(
        image_path(name).read_bytes(),
        media_type="image/png",
        headers={"Cache-Control": IMMUTABLE},
    )


@router.get(
    "/{slug}",
    summary="Раздел справки",
    description="Текст в Markdown: заголовки, списки и таблицы.",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND),
)
async def read_topic(slug: str, user: CurrentUserDep) -> HelpTopicOut:
    return get_topic(user.role, slug)
