import os
import logging
from typing import Dict, Any, Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from urllib.parse import quote_plus, unquote_plus

load_dotenv()

logger = logging.getLogger(__name__)

Base = declarative_base()

_engine = None
_SessionLocal = None


def get_db_config() -> Dict[str, Any]:
    """Retrieve MySQL configuration parameters from environment variables."""
    load_dotenv(override=True)
    return {
        "host": os.getenv("MYSQL_HOST", "localhost").strip(),
        "port": int(os.getenv("MYSQL_PORT", 3306)),
        "user": os.getenv("MYSQL_USER", "root").strip(),
        "password": os.getenv("MYSQL_PASSWORD", "").strip(),
        "database": os.getenv("MYSQL_DATABASE", "color_extractor_db").strip(),
        "custom_url": os.getenv("DATABASE_URL", "").strip(),
    }


def build_database_url(include_db: bool = True) -> str:
    """Constructs SQLAlchemy database connection URL."""
    config = get_db_config()
    if config["custom_url"]:
        return config["custom_url"]

    user = quote_plus(unquote_plus(config["user"]))
    raw_pass = config["password"]
    normalized_pass = unquote_plus(raw_pass) if raw_pass else ""
    password = quote_plus(normalized_pass) if normalized_pass else ""
    host = config["host"]
    port = config["port"]
    database = config["database"] if include_db else ""

    if password:
        auth_str = f"{user}:{password}"
    else:
        auth_str = user

    db_path = f"/{database}" if database else ""
    return f"mysql+pymysql://{auth_str}@{host}:{port}{db_path}?charset=utf8mb4"


def ensure_database_exists() -> bool:
    """
    Attempts to create the MySQL database if it does not already exist.
    """
    config = get_db_config()
    if config["custom_url"] and not config["custom_url"].startswith("mysql"):
        return True

    db_name = config["database"]
    server_url = build_database_url(include_db=False)

    try:
        server_engine = create_engine(server_url, isolation_level="AUTOCOMMIT")
        with server_engine.connect() as conn:
            conn.execute(
                text(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            )
        server_engine.dispose()
        logger.info(f"Database `{db_name}` verified/created successfully.")
        return True
    except Exception as e:
        logger.warning(f"Could not automatically create database `{db_name}`: {e}")
        return False


def get_engine():
    """Initializes and returns the singleton SQLAlchemy engine."""
    global _engine, _SessionLocal
    if _engine is None:
        db_url = build_database_url(include_db=True)
        try:
            if db_url.startswith("sqlite"):
                _engine = create_engine(
                    db_url,
                    connect_args={"check_same_thread": False},
                )
            else:
                _engine = create_engine(
                    db_url,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    pool_size=10,
                    max_overflow=20,
                )
            _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        except Exception as e:
            logger.error(f"Failed to create SQLAlchemy engine: {e}")
            raise
    return _engine


def reset_engine():
    """Resets the singleton engine to force reconnection with fresh config."""
    global _engine, _SessionLocal
    if _engine is not None:
        try:
            _engine.dispose()
        except Exception:
            pass
    _engine = None
    _SessionLocal = None


def get_session_maker():
    """Returns sessionmaker instance."""
    global _SessionLocal
    if _SessionLocal is None:
        get_engine()
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database sessions."""
    session_factory = get_session_maker()
    db: Session = session_factory()
    try:
        yield db
    finally:
        db.close()


def check_db_status() -> Dict[str, Any]:
    """Inspects database connectivity and returns a status dictionary."""
    config = get_db_config()
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "connected": True,
            "type": "mysql",
            "host": config["host"],
            "port": config["port"],
            "database": config["database"],
            "error": None,
        }
    except Exception as e:
        # Retry with freshly reset engine
        try:
            reset_engine()
            engine = get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {
                "connected": True,
                "type": "mysql",
                "host": config["host"],
                "port": config["port"],
                "database": config["database"],
                "error": None,
            }
        except Exception as retry_err:
            return {
                "connected": False,
                "type": "mysql",
                "host": config["host"],
                "port": config["port"],
                "database": config["database"],
                "error": str(retry_err),
            }


def init_db():
    """Initializes tables in the MySQL database."""
    try:
        ensure_database_exists()
        reset_engine()
        engine = get_engine()
        import models.palette  # noqa: F401
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.warning(f"Database initialization warning (MySQL may not be running yet): {e}")
