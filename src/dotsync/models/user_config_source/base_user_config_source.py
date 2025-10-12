import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import questionary
import typer
from omegaconf import OmegaConf
from pydantic import BaseModel, Field, SecretStr
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from rich.console import RenderableType

from dotsync.console import console
from dotsync.mixins.has_secrets_model import HasSecretsModel

if TYPE_CHECKING:
    from dotsync.models.app_settings import AppSettings
from dotsync.models.user_config.user_config import UserConfig

USER_CONFIG_SOURCE_DISCRIMINATOR = "source"

logger = logging.getLogger(__name__)


class BaseUserConfigSource(HasSecretsModel, BaseModel, ABC):
    id: str = Field(
        title="Config Source ID",
        description="Unique identifier for the config source",
        examples=["my_config_source"],
    )

    __private_docs__: dict[str, str] = {}

    def model_post_init(self, context: Any) -> None:
        self._load_secrets(self.id)
        return super().model_post_init(context)

    def before_remove(self):
        self._delete_secrets(self.id)

    def load(self, app_settings: "AppSettings") -> UserConfig:
        return UserConfig.model_validate(self.load_raw(app_settings))

    def _load_configs_from_path(
        self, path: Path, app_settings: "AppSettings"
    ) -> dict[str, Any]:
        cfg = OmegaConf.create()
        expanded_path = path.expanduser().absolute()

        for file in sorted(
            f for g in app_settings.config_patterns for f in expanded_path.glob(g)
        ):
            if file.is_file():
                cfg = OmegaConf.merge(cfg, OmegaConf.load(file))
            else:
                logger.debug("Skipping non-file: %s", file)

        return cast(dict[str, Any], OmegaConf.to_container(cfg, resolve=True))

    @abstractmethod
    def load_raw(self, app_settings: "AppSettings") -> dict[str, Any]: ...

    @abstractmethod
    def render_info(self) -> RenderableType: ...

    @classmethod
    def __get_secret_attribute_names__(cls) -> list[str]:
        return list(cls.__private_attributes__.keys())

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

        field_id = field_values["id"]

        for name in cls.__get_secret_attribute_names__():
            field_name = name.lstrip("_")

            field_value = (
                prefilled[field_name]
                if field_name in prefilled
                else cls._prompt_field(
                    field_name,
                    FieldInfo(
                        title=field_name.replace("_", " ").title(),
                        description=cls.__private_docs__.get(name, None),
                        annotation=SecretStr,
                    ),
                )
            )

            cls._set_secret(cls._get_secret_id(field_id, name), field_value)

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
