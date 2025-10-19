from enum import Enum
from pathlib import Path
from typing import Annotated, cast

import toml
import typer
import yaml

from dotsync.console import console
from dotsync.models.app_state import AppState
from dotsync.models.sync_config.single_sync_config import SymlinkSingleSyncConfig
from dotsync.models.sync_config.sync_config import SyncConfig

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


class InitFileFormat(Enum):
    YAML = "yaml"
    TOML = "toml"
    JSON = "json"


@sync_app.command("init")
def sync_init_command(
    ctx: typer.Context,
    path: Path = typer.Argument(..., help="Path to initialize sync"),
    file_format: InitFileFormat = typer.Option(
        InitFileFormat.YAML,
        "--format",
        "-f",
        help="File format for the sync configuration",
    ),
):
    app_state = cast(AppState, ctx.obj)
    path = path.resolve()

    sync_config = SyncConfig(
        root={
            "my-file": SymlinkSingleSyncConfig(
                action="symlink",
                src=Path("./my-file.txt"),
                dest=Path.home() / "my-file.txt",
            )
        }
    )

    match file_format:
        case InitFileFormat.YAML:
            config_path = path / (
                app_state.app_settings.default_sync_config_filename + ".yaml"
            )
            with config_path.open("w") as f:
                f.write(
                    f"# yaml-language-server: $schema={app_state.app_settings.sync_config_schema_url}\n"
                )
                yaml.dump(sync_config.model_dump(mode="json"), f)
        case InitFileFormat.TOML:
            config_path = path / (
                app_state.app_settings.default_sync_config_filename + ".toml"
            )
            with config_path.open("w") as f:
                toml.dump(sync_config.model_dump(mode="json"), f)
        case InitFileFormat.JSON:
            config_path = path / (
                app_state.app_settings.default_sync_config_filename + ".json"
            )
            with config_path.open("w") as f:
                f.write(sync_config.model_dump_json(indent=4))
        case _:
            typer.echo(f"File format {file_format} not yet implemented.")
            raise typer.Exit(code=1)
