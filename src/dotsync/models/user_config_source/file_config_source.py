from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from pydantic import Field

if TYPE_CHECKING:
    from dotsync.models.app_settings import AppSettings
from dotsync.models.user_config_source.base_user_config_source import (
    BaseUserConfigSource,
)


class FileUserConfigSource(BaseUserConfigSource):
    source: Literal["file"] = "file"
    path: Path = Field(
        title="Configs Path",
        description="Path to the configs directory",
        examples=["~/configs"],
    )

    def render_info(self) -> str:
        return f"{self.path}"

    def load_raw(self, app_settings: "AppSettings") -> dict[str, Any]:
        return self._load_configs_from_path(self.path, app_settings)
