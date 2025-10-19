from pathlib import Path
from textwrap import indent
from typing import Annotated

import questionary
import toml
import typer

from dotsync.console import console
from dotsync.constants import EXEC_SCRIPT

utils_app = typer.Typer(help="Utility commands for DotSync.", no_args_is_help=True)


@utils_app.command("create-script")
def create_script(
    path: Annotated[
        Path, typer.Argument(..., help="Path where the new script will be created.")
    ] = Path("./sync"),
    *,
    git_source: Annotated[
        str | None,
        typer.Option(
            "--git-source",
            help="Git source URL for dotsync (e.g., git+https://github.com/cfstcyr/dotsync)",
        ),
    ] = "git+https://github.com/cfstcyr/dotsync",
):
    path = path.resolve()

    if (
        path.exists()
        and not questionary.confirm(f"File {path} already exists. Overwrite?").ask()
    ):
        raise typer.Exit()

    config = {
        "requires-python": ">=3.12",
        "dependencies": ["dotsync"],
    }

    if git_source:
        config["tool"] = {"uv": {"sources": {"dotsync": {"git": git_source}}}}

    content = EXEC_SCRIPT.format(
        config_block=indent(
            toml.dumps(config).strip(), "# ", predicate=lambda line: True
        ),
    )

    try:
        with path.open("w") as f:
            f.write(content)
        path.chmod(0o755)  # Make it executable
        console.print(f"[green]Script created at {path}[/green]")
    except Exception as e:
        console.print(f"[red]Error creating script: {e}[/red]")
        raise typer.Exit(1)
