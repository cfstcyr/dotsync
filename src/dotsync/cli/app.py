from pathlib import Path
from typing import Annotated

import typer

from dotsync.cli.config import config_app
from dotsync.cli.settings import settings_app
from dotsync.constants import APP_NAME
from dotsync.models.app_state import AppState
from dotsync.utils.setup_logs import setup_logs

app = typer.Typer(no_args_is_help=True)

app.add_typer(settings_app)
app.add_typer(settings_app, name="setting", hidden=True)
app.add_typer(config_app)


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
    app_settings_schema_url: Annotated[
        str,
        typer.Option(
            "--app-settings-schema-url",
            help="URL to the application settings schema.",
            envvar="DOTSYNC_APP_SETTINGS_SCHEMA_URL",
            show_envvar=True,
            show_default=True,
        ),
    ] = "https://raw.githubusercontent.com/cfstcyr/dotsync/refs/heads/main/schemas/app_settings.schema.json",
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
        app_settings_schema_url=app_settings_schema_url,
    )
    setup_logs(verbose_level=verbose)
