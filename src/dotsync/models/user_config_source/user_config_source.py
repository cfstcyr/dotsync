from typing import Annotated, get_args

import questionary
import typer
from pydantic import Discriminator, RootModel

from dotsync.console import console
from dotsync.models.user_config_source.base_user_config_source import (
    USER_CONFIG_SOURCE_DISCRIMINATOR,
)
from dotsync.models.user_config_source.file_config_source import FileUserConfigSource
from dotsync.models.user_config_source.git_config_source import GitHttpUserConfigSource

UserConfigSourceType = Annotated[
    FileUserConfigSource | GitHttpUserConfigSource,
    Discriminator(USER_CONFIG_SOURCE_DISCRIMINATOR),
]


class UserConfigSource(RootModel):
    root: UserConfigSourceType

    @classmethod
    def get_variants(cls) -> "dict[str, type[UserConfigSourceType]]":
        return {
            t.model_fields[USER_CONFIG_SOURCE_DISCRIMINATOR].default: t
            for t in get_args(cls.model_fields["root"].annotation)
        }

    @classmethod
    def prompt_variant(cls, config_type: str | None):
        variants = cls.get_variants()

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
