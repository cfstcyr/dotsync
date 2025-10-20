import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, cast

import yaml
from omegaconf import OmegaConf
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, PrivateAttr

logger = logging.getLogger(__name__)


class AppSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    _app_settings_path: Path = PrivateAttr()

    default_sync_config_filename: str = Field(
        default=".sync.yaml",
        title="Default Sync Config Filename",
        description="Default filename for sync configuration files",
    )
    sync_config_patterns: list[str] = Field(
        default_factory=lambda: [".dotsync*", "dotsync*", ".sync*"],
    )
    app_settings_schema_url: HttpUrl = Field(
        default=HttpUrl(
            "https://raw.githubusercontent.com/cfstcyr/dotsync/refs/heads/main/schemas/app_settings.schema.json"
        ),
        title="App Settings Schema URL",
        description="URL to the JSON schema for app settings",
    )
    sync_config_schema_url: HttpUrl = Field(
        default=HttpUrl(
            "https://raw.githubusercontent.com/cfstcyr/dotsync/refs/heads/main/schemas/sync_config.schema.json"
        ),
        title="Sync Config Schema URL",
        description="URL to the JSON schema for sync configs",
    )

    @contextmanager
    def edit(self):
        self.model_config["frozen"] = False
        yield None
        self.model_config["frozen"] = True
        self.save(self._app_settings_path)

    @classmethod
    def load_raw(
        cls,
        app_settings_path: Path,
        overrides: list[str],
    ) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            OmegaConf.to_container(
                OmegaConf.merge(
                    OmegaConf.load(app_settings_path)
                    if app_settings_path.exists()
                    else OmegaConf.create(),
                    OmegaConf.from_dotlist(overrides),
                )
            ),
        )

    @classmethod
    def load(
        cls,
        app_settings_path: Path,
        overrides: list[str],
    ) -> "AppSettings":
        app_settings = cls.model_validate(
            cls.load_raw(
                app_settings_path,
                overrides,
            )
        )
        app_settings._app_settings_path = app_settings_path

        if not app_settings_path.exists():
            app_settings.save(app_settings_path)

        return app_settings

    def save(self, app_settings_path: Path) -> None:
        app_settings_path.parent.mkdir(parents=True, exist_ok=True)
        with app_settings_path.open("w", encoding="utf-8") as f:
            f.write(f"# yaml-language-server: $schema={self.app_settings_schema_url}\n")
            yaml.dump(self.model_dump(mode="json", exclude_defaults=True), f)
        logger.debug("Settings saved to %s", app_settings_path)
