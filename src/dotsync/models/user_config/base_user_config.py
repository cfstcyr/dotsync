import logging
from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel, RootModel

from dotsync.console import console

logger = logging.getLogger(__name__)


class BaseUserConfig(ABC):
    @abstractmethod
    def sync(self) -> None: ...


class SingleUserConfig(BaseModel, BaseUserConfig):
    src: Path
    dest: Path

    def sync(self) -> None:
        console.print(f"Syncing [bold]{self.src}[/] to [bold]{self.dest}[/]")


class UserConfig(RootModel, BaseUserConfig):
    root: dict[str, "UserConfigType"]

    def sync(self) -> None:
        for config in self.root.values():
            config.sync()


UserConfigType = SingleUserConfig | UserConfig
