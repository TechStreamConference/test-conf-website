from functools import cached_property
from pathlib import Path
from typing import final

from pydantic import Field
from pydantic import SecretStr
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_ROOT_ENV_FILE = _REPO_ROOT / ".env"


@final
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ROOT_ENV_FILE, extra="ignore")

    environment: str = Field(min_length=1)
    frontend_root_uri: str = Field(min_length=1)
    backend_root_uri: str = Field(min_length=1)

    # Must match the --host / --port args passed to uvicorn.
    server_host: str = Field(min_length=1)
    server_port: int = Field(ge=1, le=65535)

    database_host: str = Field(min_length=1)
    database_port: int = Field(ge=1, le=65535)
    database_name: str = Field(min_length=1)
    database_user: str = Field(min_length=1)
    database_password: SecretStr = Field(min_length=1)
    database_echo: bool

    zitadel_issuer: str = Field(min_length=1)
    zitadel_client_id: str = Field(min_length=1)
    zitadel_client_secret: SecretStr = Field(min_length=1)

    @cached_property
    def zitadel_redirect_uri(self) -> str:
        # Must match a redirect URI registered on the ZITADEL application byte for byte.
        return f"{self.backend_root_uri.rstrip('/')}/v1/auth/callback"

    @cached_property
    def async_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.database_user}:{self.database_password.get_secret_value()}"
            + f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )

    @cached_property
    def sync_database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.database_user}:{self.database_password.get_secret_value()}"
            + f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )


# The ignore comment in the following line is required because Pyright cannot know
# that pydantic-settings will fill in all fields for the `Settings` instance from
# the environment (or raises if a value is missing or malformed).
SETTINGS = Settings()  # type: ignore[reportCallIssue]
