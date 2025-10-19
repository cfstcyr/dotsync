import logging

from rich.console import Console
from rich.logging import RichHandler

VERBOSITY_LEVELS = {
    0: logging.ERROR,
    1: logging.WARNING,
    2: logging.INFO,
    3: logging.DEBUG,
}


def setup_logs(*, verbose_level: int) -> None:
    # Disable all loggers by setting root logger to CRITICAL
    logging.getLogger().setLevel(logging.CRITICAL)

    # Enable only dotsync app loggers
    app_logger = logging.getLogger("dotsync")
    app_logger.setLevel(VERBOSITY_LEVELS.get(verbose_level, logging.WARNING))
    app_logger.addHandler(
        RichHandler(console=Console(stderr=True), rich_tracebacks=True)
    )
