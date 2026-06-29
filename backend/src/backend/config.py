from functools import cached_property
from pathlib import Path
from typing import final

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_ROOT_ENV_FILE = _REPO_ROOT / ".env"


@final
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ROOT_ENV_FILE, extra="ignore")

    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "postgres"
    database_user: str = "postgres"
    database_password: str = "postgres"  # noqa: S105
    database_echo: bool = False

    @cached_property
    def async_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.database_user}:{self.database_password}"
            + f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )

    @cached_property
    def sync_database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.database_user}:{self.database_password}"
            + f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )


SETTINGS = Settings()
