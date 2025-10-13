import logging
from typing import Annotated, Any, cast

import questionary
import typer
from omegaconf import OmegaConf
from pydantic import SecretStr
from rich.table import Table

from dotsync.console import console
from dotsync.models.app_settings import AppSettings
from dotsync.models.app_state import AppState
from dotsync.models.user_config_source.user_config_source import UserConfigSource
from dotsync.utils.options import ConfigId, prompt_config_id

logger = logging.getLogger(__name__)

config_app = typer.Typer(name="config", no_args_is_help=True)


@config_app.command("add")
def add_config(
    ctx: typer.Context,
    *,
    config_type: Annotated[
        str | None, typer.Option("--type", "-t", help="Type of the config source")
    ] = None,
    values: Annotated[
        list[str],
        typer.Argument(
            help="Field values in the format 'field=value'. Can be specified multiple times."
        ),
    ] = [],
):
    app_state = cast(AppState, ctx.obj)

    prefilled = cast(
        dict[str, Any], OmegaConf.to_container(OmegaConf.from_dotlist(values))
    )

    logger.info(
        "Adding new config source (type: %s, prefilled: %s)",
        config_type,
        list(prefilled.keys()),
    )

    variant = UserConfigSource.prompt_variant(config_type)
    config = variant.prompt_config(prefilled)

    with AppSettings.use(app_state, save_on_exit=True) as app_settings:
        if config.id in app_settings.user_config_sources:
            logger.warning("Config source with ID '%s' already exists", config.id)
            console.print(
                f"[red]Error:[/red] Config source with ID '{config.id}' already exists. Remove it first with 'dotsync config remove -i {config.id}'."
            )
            raise typer.Exit(code=1)

        app_settings.user_config_sources[config.id] = UserConfigSource(root=config)
        logger.info(
            "Successfully added config source '%s' (%s)", config.id, config.source
        )
        console.print(f"[green]Success:[/green] Config source '{config.id}' added.")


@config_app.command("set")
def set_config(
    ctx: typer.Context,
    config_id: ConfigId = None,
    values: Annotated[
        list[str],
        typer.Argument(
            help="Field values in the format 'field=value'. Can be specified multiple times."
        ),
    ] = [],
):
    if not values:
        logger.warning("No values provided to set config")
        console.print("[red]Error:[/red] No values provided to set.")
        raise typer.Exit(code=1)

    app_state = cast(AppState, ctx.obj)
    resolved_config_id = prompt_config_id(config_id, ctx)

    logger.info("Setting config values for '%s': %s", resolved_config_id, values)

    prefilled = cast(
        dict[str, Any], OmegaConf.to_container(OmegaConf.from_dotlist(values))
    )

    with AppSettings.use(app_state, save_on_exit=True) as app_settings:
        existing_config = app_settings.user_config_sources[resolved_config_id]

        fields = {*existing_config.root.__class__.model_fields.keys()}
        secret_fields = {
            *existing_config.root.__class__.__get_secret_attribute_names__()
        }

        update = {}

        for field in prefilled:
            if field == "id":
                logger.warning(
                    "Attempted to change ID field for config '%s'", resolved_config_id
                )
                console.print(
                    "[red]Error:[/red] Cannot change the 'id' of a config source."
                )
                raise typer.Exit(code=1)

            private_field = f"_{field}"

            if field in fields:
                update[field] = prefilled[field]
                logger.debug(
                    "Updating field '%s' for config '%s'", field, resolved_config_id
                )
            elif private_field in secret_fields:
                existing_config.root._set_secret(
                    existing_config.root._get_secret_id(
                        existing_config.root.id, private_field
                    ),
                    SecretStr(prefilled[field]),
                )
                logger.debug(
                    "Updating secret field '%s' for config '%s'",
                    field,
                    resolved_config_id,
                )
            else:
                logger.warning(
                    "Field '%s' does not exist in config '%s'",
                    field,
                    resolved_config_id,
                )
                console.print(
                    f"[red]Error:[/red] Field '{field}' does not exist in config source '{resolved_config_id}'."
                )
                raise typer.Exit(code=1)

        new_config = existing_config.root.model_copy(update=prefilled)

        app_settings.user_config_sources[resolved_config_id] = UserConfigSource(
            root=new_config
        )
        logger.info("Successfully updated config source '%s'", resolved_config_id)
        console.print(
            f"[green]Success:[/green] Config source '{resolved_config_id}' updated."
        )


@config_app.command("remove")
def remove_config(
    ctx: typer.Context,
    config_id: ConfigId = None,
):
    app_state = cast(AppState, ctx.obj)
    resolved_config_id = prompt_config_id(config_id, ctx)

    logger.info("Removing config source '%s'", resolved_config_id)

    if (
        questionary.confirm(
            f"Are you sure you want to remove config source '{resolved_config_id}'?",
            default=False,
        ).ask()
        is False
    ):
        logger.info("User cancelled removal of config source '%s'", resolved_config_id)
        console.print("Aborted.")
        raise typer.Exit(code=0)

    with AppSettings.use(app_state, save_on_exit=True) as app_settings:
        config = app_settings.user_config_sources[resolved_config_id]
        config.root.before_remove()
        del app_settings.user_config_sources[resolved_config_id]
        logger.info("Successfully removed config source '%s'", resolved_config_id)
        console.print(
            f"[green]Success:[/green] Config source '{resolved_config_id}' removed."
        )


@config_app.command("list")
def list_configs(ctx: typer.Context):
    app_state = cast(AppState, ctx.obj)

    logger.debug("Listing config sources")

    with AppSettings.use(app_state, save_on_exit=False) as app_settings:
        if not app_settings.user_config_sources:
            logger.info("No config sources found")
            console.print("No config sources found.")
            return

        logger.info("Found %d config sources", len(app_settings.user_config_sources))

        table = Table(title="Config Sources", show_lines=True)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("Details")

        for config in app_settings.user_config_sources.values():
            table.add_row(
                config.root.id,
                config.root.source,
                config.root.render_info(),
            )

        console.print(table)
