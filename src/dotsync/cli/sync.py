import logging
from pathlib import Path
from typing import Annotated, cast

import questionary
import typer
import yaml

from dotsync.console import console
from dotsync.models.app_state import AppState
from dotsync.models.sync_config.single_sync_config import SymlinkSingleSyncConfig
from dotsync.models.sync_config.sync_config import SyncConfig

logger = logging.getLogger(__name__)

sync_app = typer.Typer()


@sync_app.command("sync")
def sync_command(
    ctx: typer.Context,
    *,
    path: Annotated[Path, typer.Argument(..., help="Path to sync from")],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", "-n", help="Perform a dry run without making changes"
        ),
    ] = False,
):
    app_state = cast(AppState, ctx.obj)

    sync_config = SyncConfig.load_path(
        path, patterns=app_state.app_settings.sync_config_patterns
    )
    sync_results = sync_config.sync(dry_run=dry_run)

    console.print(sync_results.render_results())
    console.print(sync_results.render_summary())
    # typer.echo(f"Syncing using method one at {path}...")


@sync_app.command("unsync")
def unsync_command(
    ctx: typer.Context,
    *,
    path: Annotated[Path, typer.Argument(..., help="Path to unsync from")],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", "-n", help="Perform a dry run without making changes"
        ),
    ] = False,
):
    app_state = cast(AppState, ctx.obj)

    sync_config = SyncConfig.load_path(
        path, patterns=app_state.app_settings.sync_config_patterns
    )
    unsync_results = sync_config.unsync(dry_run=dry_run)

    console.print(unsync_results.render_results())
    console.print(unsync_results.render_summary())


@sync_app.command("init")
def sync_init_command(
    ctx: typer.Context,
    path: Annotated[
        Path,
        typer.Argument(..., help="Path to initialize sync"),
    ],
    *,
    render_unsync: Annotated[
        bool,
        typer.Option(
            "--render-unsync",
            "-r",
            help="Render the unsync operations that would be performed if a sync config already exists",
        ),
    ] = True,
):
    app_state = cast(AppState, ctx.obj)
    path = path.resolve()

    # Check if any sync config exists using patterns
    existing_configs = []
    for pattern in app_state.app_settings.sync_config_patterns:
        existing_configs.extend(path.glob(pattern))

    if existing_configs:
        if not questionary.confirm("Sync config already exists. Overwrite?").ask():
            raise typer.Exit()

        # Always unsync existing configs before overwriting
        existing_config = SyncConfig.load_path(
            path, app_state.app_settings.sync_config_patterns
        )
        unsync_results = existing_config.unsync(dry_run=False)

        if render_unsync:
            console.print(
                "[bold yellow]Rendered unsync operations for existing config:[/bold yellow]"
            )
            console.print(unsync_results.render_results())
            console.print(unsync_results.render_summary())

        for file in existing_configs:
            logger.info("Removing existing config file: %s", file)
            file.unlink()

    config_path = path / app_state.app_settings.default_sync_config_filename

    sync_config = SyncConfig(
        root={
            "my-file": SymlinkSingleSyncConfig(
                action="symlink",
                src=Path("./my-file.txt"),
                dest=Path.home() / "my-file.txt",
            )
        }
    )

    with config_path.open("w") as f:
        f.write(
            f"# yaml-language-server: $schema={app_state.app_settings.sync_config_schema_url}\n"
        )
        yaml.dump(sync_config.model_dump(mode="json"), f)
