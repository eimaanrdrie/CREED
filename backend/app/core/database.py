from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.db.session import get_engine


def database_health() -> tuple[str, str | None]:
    settings = get_settings()
    if not settings.database_url:
        return "NOT_CONFIGURED", None
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return "CONNECTED", None
    except (SQLAlchemyError, ModuleNotFoundError, ImportError, RuntimeError) as exc:
        return "UNAVAILABLE", exc.__class__.__name__
