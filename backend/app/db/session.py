from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    engine = create_engine(
        settings.database_url,
        echo=settings.db_echo,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

    @event.listens_for(engine, "connect")
    def _set_session_options(dbapi_connection, _record):  # type: ignore[no-untyped-def]
        # Datas são gravadas em UTC; NOW() do MySQL também passa a ser UTC.
        with dbapi_connection.cursor() as cursor:
            cursor.execute("SET time_zone = '+00:00'")

    return engine


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False, autoflush=False)


def get_db() -> Iterator[Session]:
    """Dependência do FastAPI: uma sessão por requisição. Os serviços fazem commit;
    qualquer exceção desfaz o que não foi confirmado."""
    session = get_sessionmaker()()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
