import logging
from typing import Annotated, cast

import typer

from dotsync.console import console
from dotsync.models.app_settings import AppSettings
from dotsync.models.app_state import AppState

logger = logging.getLogger(__name__)

sync_app = typer.Typer(name="sync", invoke_without_command=True)


@sync_app.callback()
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

    logger.info("Starting sync operation (dry_run=%s)", dry_run)

    with AppSettings.use(app_state, save_on_exit=False) as app_settings:
        logger.info(
            "Found %d config sources to sync", len(app_settings.user_config_sources)
        )

        for config_source_id, config_source in app_settings.user_config_sources.items():
            logger.info(
                "Syncing config source '%s' (%s)",
                config_source_id,
                config_source.root.source,
            )

            config = config_source.root.load(app_settings)

            results = config.sync(dry_run=dry_run)

            console.print(results.render_results())
            console.print(results.render_summary())
