from pathlib import Path
from typing import Any, Literal, cast

from omegaconf import OmegaConf
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

    def load_raw(self) -> dict[str, Any]:
        cfg = OmegaConf.create()
        path = self.path.expanduser().absolute()

        for file in sorted(f for g in (".config*", "config*") for f in path.glob(g)):
            cfg = OmegaConf.merge(cfg, OmegaConf.load(file))

        return cast(dict[str, Any], OmegaConf.to_container(cfg, resolve=True))
