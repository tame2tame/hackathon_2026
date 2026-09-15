"""Демо-пользователи из app/demo.py и заголовки режима разработки."""

ANNA_KAM = "anna.smirnova@example.com"
MIKHAIL_KAM = "mikhail.volkov@example.com"
ROMAN_MANAGER = "roman.kovalev@example.com"
ALINA_ADMIN = "alina.denisova@example.com"


def as_user(email: str) -> dict[str, str]:
    return {"X-Dev-User": email}
