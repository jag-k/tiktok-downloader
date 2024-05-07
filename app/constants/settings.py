import functools
import json
from pathlib import Path
from typing import Self

import pytz
from pydantic import ByteSize, Field, MongoDsn, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .paths import BASE_PATH, CONFIG_PATH
from .types import CONTACT

__all__ = (
    "Settings",
    "settings",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[
            CONFIG_PATH / ".env.local",
            CONFIG_PATH / ".env",
            BASE_PATH / ".env.local",
            BASE_PATH / ".env",
        ],
        env_ignore_empty=True,
        extra="ignore",
    )

    default_locale: str = Field("en")
    domain: str = Field("messages")

    token: SecretStr = Field(alias="TG_TOKEN", description="Telegram Token")
    time_zone: pytz.tzinfo.BaseTzInfo = Field(pytz.timezone("Europe/Moscow"), alias="TZ")

    tg_file_size: ByteSize = Field("20 MiB", description="Telegram file size")

    report_path: Path = Field(CONFIG_PATH / "report.json")
    contacts_path: Path = Field(CONFIG_PATH / "contacts.json")

    @functools.cached_property
    def contacts(self) -> list[CONTACT]:
        if self.contacts_path.exists():
            with self.contacts_path.open() as f:
                return json.load(f)
        return []

    mongo_url: MongoDsn | None = Field(None)
    mongo_db: str | None = Field(None)

    @model_validator(mode="after")
    def mongo_require(self) -> Self:
        if self.mongo_url is None or self.mongo_db is None:
            raise ValueError("Bot requires MongoDB to work. Please, set MONGO_URL and MONGO_DB.")
        self.report_path.parent.mkdir(exist_ok=True, parents=True)
        return self


settings = Settings()

if __name__ == "__main__":
    print(repr(settings))
