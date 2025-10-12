from typing import Literal

from pydantic import Field, PrivateAttr, SecretStr
from rich.console import RenderableType
from rich.text import Text

from dotsync.models.user_config_source.base_user_config_source import (
    BaseUserConfigSource,
)


class GitHttpUserConfigSource(BaseUserConfigSource):
    source: Literal["git-http"] = "git-http"
    repo_url: str = Field(
        title="Repo URL",
        description="URL of the git repository",
        examples=["https://github.com/user/repo.git"],
    )
    branch: str = Field(
        default="main",
        description="Branch of the git repository",
        examples=["main", "dev"],
    )
    username: str = Field(
        description="Username for accessing the git repository", examples=["gituser"]
    )
    _password: SecretStr = PrivateAttr()

    __private_docs__ = {
        "_password": "Password or token for accessing the git repository",
    }

    def render_info(self) -> RenderableType:
        return Text.assemble(
            ("Repo: ", "bold"),
            (self.repo_url, "cyan"),
            ("\nbranch: ", "bold"),
            (self.branch, "green"),
            (", username: ", "bold"),
            (self.username, "yellow"),
        )
