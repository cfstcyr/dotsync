from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import keyring
import questionary
import typer
from pydantic import BaseModel, Field, SecretStr
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from rich.console import RenderableType

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

        if field.annotation == Path:
            if instructions:
                query += f" [{instructions}]"
            value = questionary.path(query, **args).ask()
        elif field.annotation == SecretStr:
            if instructions:
                query += f" [{instructions}]"
            value = questionary.password(query, **args).ask()
        else:
            value = questionary.text(query, instruction=instructions, **args).ask()

        if not value and field.default == PydanticUndefined and field.is_required():
            console.print(f"[red]Error:[/red] '{field_name}' is required")
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
    def prompt_config(cls, prefilled: dict[str, Any]):
        raw_config = {
            USER_CONFIG_SOURCE_DISCRIMINATOR: cls.model_fields[
                USER_CONFIG_SOURCE_DISCRIMINATOR
            ].default,
            **cls._prompt_fields(prefilled),
        }
        return cls.model_validate(raw_config)
