from typing import Annotated, cast

import typer
import yaml
from omegaconf import OmegaConf
from rich.panel import Panel
from rich.syntax import Syntax

from dotsync.console import console
from dotsync.models.app_settings.app_settings import AppSettings
from dotsync.models.app_state import AppState

settings_app = typer.Typer(name="settings", no_args_is_help=True)


@settings_app.command("dump")
def dump_settings(
    ctx: typer.Context,
    *,
    raw: Annotated[
        bool,
        typer.Option("--raw", "-r", help="Dump raw settings without defaults applied."),
    ] = False,
    resolve: Annotated[
        bool, typer.Option("--resolve", help="Resolve settings.")
    ] = True,
):
    app_state = cast(AppState, ctx.obj)

    if resolve:
        app_settings = AppSettings.load(app_state.app_settings).model_dump(mode="json")
    else:
        app_settings = AppSettings.load_raw(app_state.app_settings)

    if raw:
        console.print(yaml.dump(app_settings, indent=2).strip())
    else:
        panel = Panel(
            Syntax(
                yaml.dump(app_settings, indent=2).strip(),
                lexer="yaml",
                theme="monokai",
            ),
            title="App Settings",
            expand=False,
        )
        console.print(panel)


@settings_app.command("set")
def set_setting(
    ctx: typer.Context,
    set_attrs: Annotated[
        list[str],
        typer.Argument(
            ...,
            help="Attribute to set, e.g., 'app_name=MyApp'. Can be specified multiple times.",
        ),
    ],
):
    app_state = cast(AppState, ctx.obj)

    AppSettings.model_validate(
        OmegaConf.merge(
            OmegaConf.create(AppSettings.load_raw(app_state.app_settings)),
            OmegaConf.from_dotlist(set_attrs),
        )
    ).save(app_state.app_settings)
