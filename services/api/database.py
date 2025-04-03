import asyncpg
import os
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings
from logging import getLogger
from dotenv import load_dotenv

logger = getLogger(__name__)


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DOTENV_PATH = os.path.join(PROJECT_ROOT, ".env")

logger.info(f"Attempting to load environment variables from: {DOTENV_PATH}")
if not os.path.exists(DOTENV_PATH):
    logger.error(f"CRITICAL: .env file NOT FOUND at calculated path: {DOTENV_PATH}")
    dotenv_loaded = False
else:
    logger.info(f".env file found at {DOTENV_PATH}. Attempting to load...")
    dotenv_loaded = load_dotenv(dotenv_path=DOTENV_PATH, verbose=True, override=True)
    if not dotenv_loaded:
        logger.error(f"python-dotenv reported FAILURE loading file: {DOTENV_PATH}")
    else:
        logger.info(f"Successfully loaded variables from {DOTENV_PATH}")
# ---


class DatabaseSettings(BaseSettings):

    db_name: str = Field(validation_alias="POSTGRES_DB")
    db_user: str = Field(validation_alias="POSTGRES_USER")
    db_password: str = Field(validation_alias="POSTGRES_PASSWORD")
    db_host: str = Field("localhost", validation_alias="DB_HOST")
    db_port: int = Field(5433, validation_alias="DB_PORT")

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file_encoding = "utf-8"
        extra = "ignore"


# --- Instantiate Settings and Handle Validation ---
try:
    settings = DatabaseSettings()
    logger.info("DatabaseSettings loaded successfully.")
    logger.info(
        f"Loaded DB settings: User={settings.db_user}, Host={settings.db_host}, Port={settings.db_port}, DB={settings.db_name}"
    )
except ValidationError as e:
    logger.error(
        f"CRITICAL: Failed to load/validate database settings AFTER loading .env."
    )
    logger.error(
        f"Ensure required variables specified by validation_alias (e.g., POSTGRES_PASSWORD) exist in {DOTENV_PATH}."
    )
    logger.error(f"Validation Error details: {e}")
    raise SystemExit("Failed to load/validate required database configuration.")
# ---

# --- Global pool and DB functions ---
pool = None


async def connect_db():
    global pool
    if pool:
        return
    logger.info(
        f"Attempting to connect to database: postgresql://{settings.db_user}:***@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )
    try:
        pool = await asyncpg.create_pool(settings.database_url, min_size=5, max_size=20)
        logger.info("Database connection pool created successfully.")
        async with pool.acquire() as connection:
            val = await connection.fetchval("SELECT 1")
            if val == 1:
                logger.info("Database connectivity test successful.")
            else:
                logger.warning("Database connectivity test returned unexpected value.")
    except Exception as e:
        logger.exception(f"Failed to create database connection pool. Error: {e}")
        pool = None


async def disconnect_db():
    global pool
    if pool:
        logger.info("Closing database connection pool...")
        try:
            await pool.close()
        except Exception as e:
            logger.exception(f"Error occurred while closing database pool: {e}")
        finally:
            pool = None
            logger.info("Database connection pool closed.")


async def get_db_pool():
    if pool is None:
        logger.error(
            "get_db_pool called when connection pool is None. Check application startup and connection logic."
        )
        raise RuntimeError("Database connection pool is not available.")
    return pool
