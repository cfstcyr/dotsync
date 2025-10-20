from typing import cast

import typer
from omegaconf import OmegaConf
from pydantic import ValidationError
from pydantic_core import PydanticUndefined
from rich.panel import Panel
from rich.table import Table

from dotsync.console import console
from dotsync.models.app_settings import AppSettings
from dotsync.models.app_state import AppState

settings_app = typer.Typer(help="Manage DotSync settings.", no_args_is_help=True)


@settings_app.command("reset", help="Reset application settings to defaults.")
def reset_settings(
    ctx: typer.Context,
):
    app_state = cast(AppState, ctx.obj)

    new_app_settings = AppSettings()
    new_app_settings.save(app_state.app_settings_path)

    typer.echo(f"Settings reset to default and saved to {app_state.app_settings_path}")


@settings_app.command("set", help="Set application settings.")
def set_settings(
    ctx: typer.Context,
    settings: list[str] = typer.Argument(
        ...,
        help="Settings to set in 'key=value' format. Example: sync_config_patterns='[\"*.yaml\"]' or sync_config_patterns='*.yaml'",
    ),
):
    app_state = cast(AppState, ctx.obj)

    try:
        current_raw = AppSettings.load_raw(app_state.app_settings_path, [])
        merged = OmegaConf.merge(
            OmegaConf.create(current_raw), OmegaConf.from_dotlist(settings)
        )
        new_app_settings = AppSettings.model_validate(OmegaConf.to_container(merged))
        new_app_settings._app_settings_path = app_state.app_settings_path
        new_app_settings.save(app_state.app_settings_path)
        app_state.app_settings = new_app_settings
        typer.echo(f"Settings updated and saved to {app_state.app_settings_path}")
    except ValidationError as e:
        console.print(Panel(f"[red]{e}[/red]", title="Validation Error"))
        raise typer.Exit(1)


@settings_app.command("info", help="Display current application settings.")
def info_settings(
    ctx: typer.Context,
):
    app_state = cast(AppState, ctx.obj)

    table = Table(title="App Settings")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Description", style="magenta")
    table.add_column("Default", style="green")
    table.add_column("Current", style="yellow")

    default_instance = AppSettings()
    for name, field in AppSettings.model_fields.items():
        current = getattr(app_state.app_settings, name)
        default = (
            getattr(default_instance, name)
            if field.default == PydanticUndefined
            else field.default
        )
        desc = field.description or field.title or ""
        table.add_row(name, desc, str(default), str(current))

    console.print(table)
