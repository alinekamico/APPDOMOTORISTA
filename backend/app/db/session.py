from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

connect_args = {"ssl": {"ca": settings.database_ssl_ca}} if settings.database_ssl_ca else {}
engine = create_engine(
    settings.database_url, pool_pre_ping=True, pool_recycle=3600, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
