from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppState:
    app_settings: Path
