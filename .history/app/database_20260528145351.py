"""Database Configuration and Session Management"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)

Base = declarative_base()


class DatabaseManager:
    """Manage database connections"""

    def __init__(self):
        self.settings = get_settings()
        self._engine = None
        self._session_factory = None

    def get_engine(self, db_type: str = "sqlite"):
        """Get database engine"""

        if db_type == "sqlite":

            engine = create_engine(
                "sqlite:///./expense_splitter.db",
                connect_args={"check_same_thread": False},
                echo=self.settings.debug
            )

        elif db_type == "postgres":

            connection_string = self.settings.database_url

            engine = create_engine(
                connection_string,
                echo=self.settings.debug,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True
            )

        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        return engine

    def init_postgres(self):
        """Initialize SQLite database"""

        try:

            self._engine = self.get_engine("sqlite")

            self._session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine
            )

            logger.info("SQLite initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize SQLite: {e}")
            raise

    def create_tables(self):
        """Create all tables"""

        Base.metadata.create_all(bind=self._engine)
        logger.info("Database tables created")

    def drop_tables(self):
        """Drop all tables"""

        Base.metadata.drop_all(bind=self._engine)
        logger.info("Database tables dropped")

    def get_session(self):
        """Get database session"""

        if not self._session_factory:
            raise RuntimeError("Database not initialized")

        return self._session_factory()


db_manager = DatabaseManager()


def get_db():
    """Dependency for database session"""

    db = db_manager.get_session()

    try:
        yield db

    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise

    finally:
        db.close()