from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from .base import Base

DATABASE_URL = "sqlite:///database/agent.db"


engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
)


SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def init_db():
    Base.metadata.create_all(bind=engine)

def get_session() -> Generator[Session, None, None]:
    """
    Создаёт SQLAlchemy-сессию для одной операции/запроса.
    После завершения сессия гарантированно закрывается.
    """

    session = SessionLocal()

    try:
        yield session

    finally:
        session.close()