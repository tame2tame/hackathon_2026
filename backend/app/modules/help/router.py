from fastapi import APIRouter

from app.core.errors import ErrorCode, error_responses
from app.core.security import CurrentUserDep
from app.modules.help.schemas import HelpTopicOut, HelpTopicRef
from app.modules.help.service import get_topic, list_topics

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
    "/{slug}",
    summary="Раздел справки",
    description="Текст в Markdown: заголовки, списки и таблицы.",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND),
)
async def read_topic(slug: str, user: CurrentUserDep) -> HelpTopicOut:
    return get_topic(user.role, slug)
