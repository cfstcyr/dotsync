import logging
from contextlib import contextmanager
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from dotsync.models.app_settings.user_config_source import UserConfigSource
from dotsync.utils.load_file import load_file

logger = logging.getLogger(__name__)


class AppSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_config_sources: dict[str, UserConfigSource] = Field(default_factory=dict)

    @classmethod
    @contextmanager
    def use(cls, path: Path | str, *, save_on_exit: bool = True):
        path = Path(path).expanduser().resolve()
        app_settings = cls.load(path)

        try:
            yield app_settings
        finally:
            if save_on_exit:
                app_settings.save(path)

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

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(mode="json"), f)
        logger.debug("Settings saved to %s", path)
