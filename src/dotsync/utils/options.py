import logging
from typing import Annotated

import questionary
import typer

from dotsync.console import console
from dotsync.models.app_settings import AppSettings
from dotsync.models.app_state import AppState

logger = logging.getLogger(__name__)

ConfigId = Annotated[
    str | None, typer.Option("--id", "-i", help="Unique identifier for the config")
]


def prompt_config_id(config_id: str | None, ctx: typer.Context) -> str:
    app_state: AppState = ctx.obj

    logger.debug("Resolving config ID: %s", config_id)

    with AppSettings.use(app_state, save_on_exit=False) as app_settings:
        if config_id is not None and config_id not in app_settings.user_config_sources:
            logger.warning(
                "Config ID '%s' not found in available sources: %s",
                config_id,
                list(app_settings.user_config_sources.keys()),
            )
            console.print(
                f"[red]Error:[/red] No config source found with ID '{config_id}'."
            )
            raise typer.Exit(code=1)

        if config_id is None:
            logger.debug("No config ID provided, prompting user to select")
            try:
                while config_id is None:
                    config_id = questionary.select(
                        "Select a config",
                        choices=list(app_settings.user_config_sources),
                    ).unsafe_ask()

                    if config_id is None:
                        logger.warning("User did not select a config")
                        console.print("[red]Error:[/red] You must select a config.")
            except KeyboardInterrupt:
                logger.info("User cancelled config selection")
                raise typer.Abort()

    logger.debug("Resolved config ID: %s", config_id)
    return config_id

    # if project_id is None:
    #     choices = list(config.projects)
    #     if not choices:
    #         raise typer.BadParameter(
    #             "No projects configured. Run 'jira-export projects add' first.",
    #         )

    #     selected_project_id = questionary.select(
    #         "Select a project",
    #         choices=choices,
    #     ).ask()

    #     if selected_project_id is None:
    #         raise typer.Abort()

    #     return selected_project_id

    # return project_id
