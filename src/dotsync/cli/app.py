from pathlib import Path
from typing import Annotated

import typer

from dotsync.cli.sync import sync_app
from dotsync.constants import APP_NAME
from dotsync.models.app_state import AppState
from dotsync.utils.setup_logs import setup_logs

app = typer.Typer(no_args_is_help=True)

app.add_typer(sync_app, name=None)


@app.callback()
def setup_app(
    ctx: typer.Context,
    *,
    app_settings_path: Annotated[
        Path,
        typer.Option(
            "--app-settings",
            help="Path to the application settings file.",
            envvar="DOTSYNC_APP_SETTINGS",
            show_envvar=True,
            show_default=True,
        ),
    ] = Path(typer.get_app_dir(APP_NAME)) / "settings.yaml",
    app_settings_overrides: Annotated[
        list[str],
        typer.Option(
            "--with-setting",
            help="Override application settings (in 'key=value' format). Can be specified multiple times.",
        ),
    ] = [],
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        min=0,
        max=3,
        help="Increase verbosity (-v, -vv)",
    ),
):
    setup_logs(verbose_level=verbose)
    ctx.obj = AppState(
        app_settings_path=app_settings_path.resolve(),
        app_settings_overrides=app_settings_overrides,
    )
