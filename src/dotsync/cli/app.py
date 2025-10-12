from pathlib import Path
from typing import Annotated

import typer

from dotsync.cli.config import config_app
from dotsync.cli.sync import sync_app
from dotsync.constants import APP_NAME
from dotsync.models.app_state import AppState
from dotsync.utils.setup_logs import setup_logs

app = typer.Typer(no_args_is_help=True)

app.add_typer(config_app)
app.add_typer(sync_app)
app.add_typer(sync_app, name="s", hidden=True)  # Alias for sync


@app.callback()
def cli(
    ctx: typer.Context,
    *,
    app_settings_path: Annotated[
        str,
        typer.Option(
            "--app-settings",
            help="Path to the application settings file.",
            envvar="DOTSYNC_APP_SETTINGS",
            show_envvar=True,
            show_default=True,
        ),
    ] = typer.get_app_dir(APP_NAME) + "/settings.yaml",
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        min=0,
        max=2,
        help="Increase verbosity (-v, -vv)",
    ),
):
    ctx.obj = AppState(
        app_settings=Path(app_settings_path),
    )
    setup_logs(verbose_level=verbose)
