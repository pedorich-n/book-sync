import logging
from enum import Enum, IntEnum
from pathlib import Path
from typing import Any, Dict

from pydantic import HttpUrl, PositiveInt, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from book_sync.utils import NonEmptyStr


class LogFormat(str, Enum):
    FULL = "full"  # Timestamp, level, message (for standalone execution)
    SYSTEMD = "systemd"  # Level and message only (systemd adds timestamps)
    SIMPLE = "simple"  # Message only (minimal output)


class LogLevel(IntEnum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LoggingConfig(BaseSettings):
    level: LogLevel = LogLevel.DEBUG
    format: LogFormat = LogFormat.FULL

    @field_validator("level", mode="before")
    @classmethod
    def parse_log_level(cls, v: Any) -> LogLevel:
        if isinstance(v, str):
            try:
                return LogLevel[v.upper()]
            except KeyError:
                raise ValueError(f"Invalid log level: {v}")
        return v


class AbsConfig(BaseSettings):
    token: SecretStr
    base_url: HttpUrl
    user_id: NonEmptyStr


class GristConfig(BaseSettings):
    # The rest of the fields are loaded by pygrister from the environment
    # See https://pygrister.readthedocs.io/en/latest/conf.html#configuration-keys
    model_config = SettingsConfigDict(extra="ignore")

    token: SecretStr
    base_url: HttpUrl
    doc_id: NonEmptyStr

    def get_pygrister_config(self) -> Dict[str, str]:
        # Yeah, I'll just hardcode the pygrister settings for self-hosted version
        return {
            "GRIST_SELF_MANAGED": "Y",
            "GRIST_SELF_MANAGED_HOME": self.base_url.encoded_string(),
            "GRIST_SELF_MANAGED_SINGLE_ORG": "Y",
            "GRIST_API_KEY": self.token.get_secret_value(),
            "GRIST_DOC_ID": self.doc_id,
        }


class StateConfig(BaseSettings):
    file_path: Path


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="_", env_nested_max_split=1)

    logging: LoggingConfig = LoggingConfig()
    abs: AbsConfig
    grist: GristConfig
    state: StateConfig
    default_lookback_minutes: PositiveInt = 60
