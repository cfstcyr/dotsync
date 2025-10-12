from abc import ABC, abstractmethod
from pathlib import Path
from typing import Annotated, Any, Literal, get_args

import keyring
import questionary
import typer
from pydantic import BaseModel, Discriminator, Field, RootModel, SecretStr
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from rich.console import RenderableType
from rich.text import Text

from dotsync.console import console
from dotsync.constants import APP_NAME

USER_CONFIG_SOURCE_DISCRIMINATOR = "source"


class BaseUserConfigSource(BaseModel, ABC):
    id: str = Field(
        title="Config Source ID",
        description="Unique identifier for the config source",
        examples=["my_config_source"],
    )

    def before_remove(self):
        pass

    @abstractmethod
    def render_info(self) -> RenderableType: ...

    @classmethod
    def _get_secret_id(cls, item_id: str, field_id: str) -> str:
        return f"{cls.__name__}-{item_id}-{field_id}"

    @classmethod
    def _save_secret(cls, secret_id: str, secret: SecretStr | str):
        keyring.set_password(
            APP_NAME,
            secret_id,
            secret.get_secret_value() if isinstance(secret, SecretStr) else secret,
        )

    @classmethod
    def _get_secret(cls, secret_id: str) -> SecretStr:
        value = keyring.get_password(APP_NAME, secret_id)

        if value is None:
            raise ValueError(
                f"No secret found for ID '{secret_id}' in '{cls.__name__}'"
            )

        return SecretStr(value)

    @classmethod
    def _get_variants(cls) -> "dict[str, type[UserConfigSourceType]]":
        return {
            t.model_fields[USER_CONFIG_SOURCE_DISCRIMINATOR].default: t
            for t in get_args(UserConfigSource.model_fields["root"].annotation)
        }

    @classmethod
    def _prompt_variant(cls, config_type: str | None):
        variants = cls._get_variants()

        while not config_type:
            config_type = questionary.select(
                "Config source type:",
                choices=list(variants.keys()),
            ).ask()

        variant = variants.get(config_type, None)

        if not variant:
            console.print(
                f"[red]Error:[/red] Unknown config source type '{config_type}'"
            )
            raise typer.Exit(code=1)

        return variant

    @classmethod
    def _prompt_field_from_name(cls, field_name: str) -> str:
        field = cls.model_fields.get(field_name)
        if not field:
            raise ValueError(f"Field '{field_name}' does not exist in {cls.__name__}")
        return cls._prompt_field(field_name, field)

    @classmethod
    def _prompt_field(cls, field_name: str, field: FieldInfo) -> str:
        query = f"{field.title or field_name.replace('_', ' ').title()}"
        instructions = ""
        args = {}

        if field.description:
            instructions = field.description
        if field.examples:
            instructions += f" (e.g., {', '.join(map(str, field.examples))})"
        if field.default != PydanticUndefined:
            args["default"] = str(field.default)

        value = None

        while True:
            try:
                if field.annotation == Path:
                    if instructions:
                        query += f" [{instructions}]"
                    value = questionary.path(query, **args).unsafe_ask()
                elif field.annotation == SecretStr:
                    if instructions:
                        query += f" [{instructions}]"
                    value = questionary.password(query, **args).unsafe_ask()
                else:
                    value = questionary.text(
                        query, instruction=instructions, **args
                    ).unsafe_ask()

                if not value:
                    if field.default == PydanticUndefined and field.is_required():
                        console.print(f"[red]Error:[/red] '{field_name}' is required")
                        # raise typer.Exit(code=1)
                    else:
                        break
                else:
                    break
            except KeyboardInterrupt:
                typer.Abort()

        return value

    @classmethod
    def _prompt_fields(cls, prefilled: dict[str, Any]):
        field_values = {}
        for name in cls.model_fields:
            if name == USER_CONFIG_SOURCE_DISCRIMINATOR:
                continue

            field_values[name] = (
                prefilled[name]
                if name in prefilled
                else cls._prompt_field_from_name(name)
            )

        return field_values

    @classmethod
    def prompt_config(cls, config_type: str | None, prefilled: dict[str, Any]):
        variant = cls._prompt_variant(config_type)
        raw_config = {
            USER_CONFIG_SOURCE_DISCRIMINATOR: variant.model_fields[
                USER_CONFIG_SOURCE_DISCRIMINATOR
            ].default,
            **variant._prompt_fields(prefilled),
        }
        return variant.model_validate(raw_config)


class FileUserConfigSource(BaseUserConfigSource):
    source: Literal["file"] = "file"
    path: Path = Field(
        title="Configs Path",
        description="Path to the configs directory",
        examples=["~/configs"],
    )

    def render_info(self) -> str:
        return f"{self.path}"


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


UserConfigSourceType = Annotated[
    FileUserConfigSource | GitHttpUserConfigSource,
    Discriminator(USER_CONFIG_SOURCE_DISCRIMINATOR),
]


class UserConfigSource(RootModel):
    root: UserConfigSourceType
