from typing import Any, Literal

import keyring
from pydantic import Field, PrivateAttr, SecretStr
from rich.console import RenderableType
from rich.text import Text

from dotsync.constants import APP_NAME
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

    def before_remove(self):
        keyring.delete_password(APP_NAME, self._get_password_id(self.id))

    def set_password(self, password: str | SecretStr):
        self._save_secret(self._get_password_id(self.id), password)

    def get_password(self) -> SecretStr:
        return self._get_secret(self._get_password_id(self.id))

    def render_info(self) -> RenderableType:
        return Text.assemble(
            ("Repo: ", "bold"),
            (self.repo_url, "cyan"),
            ("\nbranch: ", "bold"),
            (self.branch, "green"),
            (", username: ", "bold"),
            (self.username, "yellow"),
        )

    @classmethod
    def _get_password_id(cls, item_id: str) -> str:
        return cls._get_secret_id(item_id, "password")

    @classmethod
    def _prompt_fields(cls, prefilled: dict[str, Any]):
        fields = super()._prompt_fields(prefilled)
        item_id = fields["id"]

        if "password" not in prefilled:
            password = cls._prompt_field(
                "password",
                Field(
                    title="Password",
                    description="Password or token for accessing the git repository",
                    examples=["my_secret_token"],
                ),
            )
        else:
            password = prefilled["password"]

        cls._save_secret(cls._get_password_id(item_id), SecretStr(password))

        return fields


if __name__ == "__main__":
    GitHttpUserConfigSource.prompt_config(
        {
            "id": "my_git_config",
            "repo_url": "",
            "branch": "main",
            "username": "gituser",
        }
    )
