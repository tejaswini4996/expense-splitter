"""Database Configuration and Session Management"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool, QueuePool
from typing import Optional
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)

Base = declarative_base()

class DatabaseManager:
    """Manage database connections for PostgreSQL and MSSQL"""
    
    def __init__(self):
        self.settings = get_settings()
        self._engine = None
        self._session_factory = None
    
    def get_engine(self, db_type: str = "sqlite"):
    """Get database engine"""

    if db_type == "sqlite":
        connection_string = "sqlite:///./expense_splitter.db"

        engine = create_engine(
            connection_string,
            echo=self.settings.debug,
            connect_args={"check_same_thread": False}
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

    elif db_type == "mssql":
        if not self.settings.mssql_database_url:
            raise ValueError("MSSQL_DATABASE_URL not configured")

        connection_string = self.settings.mssql_database_url

        engine = create_engine(
            connection_string,
            echo=self.settings.debug,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20
        )

    else:
        raise ValueError(f"Unsupported database type: {db_type}")

    return engine
    
    def init_postgres(self):
    """Initialize SQLite"""

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
        """Drop all tables (use with caution)"""
        Base.metadata.drop_all(bind=self._engine)
        logger.info("Database tables dropped")
    
    def get_session(self):
        """Get database session"""
        if not self._session_factory:
            raise RuntimeError("Database not initialized")
        return self._session_factory()

# Global database manager
db_manager = DatabaseManager()

def get_db():
    """Dependency for getting database session in FastAPI routes"""
    db = db_manager.get_session()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()