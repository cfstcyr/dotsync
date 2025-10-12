from pathlib import Path
from typing import Literal

from pydantic import Field

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
