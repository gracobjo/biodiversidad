from contextlib import contextmanager
from typing import Iterator
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from db_config import DB_CONFIG


def construir_url_mysql(config: dict = DB_CONFIG) -> str:
    usuario = quote_plus(str(config["user"]))
    password = quote_plus(str(config["password"]))
    host = config.get("host", "localhost")
    port = config.get("port", 3306)
    database = config["database"]
    return f"mysql+mysqlconnector://{usuario}:{password}@{host}:{port}/{database}?charset=utf8mb4"


engine: Engine = create_engine(
    construir_url_mysql(),
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


@contextmanager
def get_session() -> Iterator[Session]:
    """Proporciona una sesión transaccional con commit/rollback automático."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()