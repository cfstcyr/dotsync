import logging
from contextlib import contextmanager
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from dotsync.models.app_state import AppState
from dotsync.models.user_config_source.user_config_source import UserConfigSource
from dotsync.utils.load_file import load_file

logger = logging.getLogger(__name__)


class AppSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_config_sources: dict[str, UserConfigSource] = Field(default_factory=dict)
    config_patterns: list[str] = Field(
        default_factory=lambda: [".dotsync*", "dotsync*", ".sync*"],
    )
    app_settings_schema_url: str = Field(
        default="https://raw.githubusercontent.com/cfstcyr/dotsync/refs/heads/main/schemas/app_settings.schema.json",
        title="App Settings Schema URL",
        description="URL to the JSON schema for app settings",
    )
    user_config_schema_url: str = Field(
        default="https://raw.githubusercontent.com/cfstcyr/dotsync/refs/heads/main/schemas/user_config.schema.json",
        title="User Config Schema URL",
        description="URL to the JSON schema for user configs",
    )

    @classmethod
    @contextmanager
    def use(cls, app_state: AppState, *, save_on_exit: bool):
        path = Path(app_state.app_settings).expanduser().resolve()
        app_settings = cls.load(path)

        try:
            yield app_settings
        finally:
            if save_on_exit:
                app_settings.save(app_state)

    @classmethod
    def load_raw(cls, path: Path) -> dict:
        if not path.exists():
            logger.debug(
                "Settings file %s does not exist. Using default settings.", path
            )
            return {}

        logger.debug("Loading settings from %s", path)

        try:
            return load_file(path)
        except Exception as e:
            raise ValueError(f"Failed to load settings from {path}: {e}") from e

    @classmethod
    def load(cls, path: Path) -> "AppSettings":
        return cls.model_validate(cls.load_raw(path))

    def save(self, app_state: AppState) -> None:
        app_state.app_settings.parent.mkdir(parents=True, exist_ok=True)
        with app_state.app_settings.open("w", encoding="utf-8") as f:
            f.write(f"# yaml-language-server: $schema={self.app_settings_schema_url}\n")
            yaml.dump(self.model_dump(mode="json"), f)
        logger.debug("Settings saved to %s", app_state.app_settings)
