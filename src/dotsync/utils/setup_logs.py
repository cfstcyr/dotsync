import logging

from rich.console import Console
from rich.logging import RichHandler

VERBOSITY_LEVELS = {
    0: logging.WARNING,
    1: logging.INFO,
    2: logging.DEBUG,
}


def setup_logs(*, verbose_level: int) -> None:
    logging.basicConfig(
        level=VERBOSITY_LEVELS.get(verbose_level, logging.WARNING),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=Console(stderr=True), rich_tracebacks=True)],
    )
