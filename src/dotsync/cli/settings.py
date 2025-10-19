from typing import cast

import typer

from dotsync.models.app_settings import AppSettings
from dotsync.models.app_state import AppState

settings_app = typer.Typer(help="Manage DotSync settings.")


@settings_app.command("reset")
def reset_settings(
    ctx: typer.Context,
):
    app_state = cast(AppState, ctx.obj)

    new_app_settings = AppSettings()
    new_app_settings.save(app_state.app_settings_path)

    typer.echo(f"Settings reset to default and saved to {app_state.app_settings_path}")
