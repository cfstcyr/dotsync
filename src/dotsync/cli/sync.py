from typing import Annotated, cast

import typer

from dotsync.console import console
from dotsync.models.app_settings import AppSettings
from dotsync.models.app_state import AppState

sync_app = typer.Typer(name="sync", no_args_is_help=True)


@sync_app.command("all")
def sync_callback(
    ctx: typer.Context,
    *,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", "-n", help="Perform a trial run with no changes made"
        ),
    ] = False,
):
    app_state = cast(AppState, ctx.obj)

    with AppSettings.use(app_state, save_on_exit=False) as app_settings:
        for config_source in app_settings.user_config_sources.values():
            config = config_source.root.load()

            results = config.sync(dry_run=dry_run)

            console.print(results.render_results())
            console.print(results.render_summary())
