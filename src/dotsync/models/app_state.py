from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppState:
    app_settings: Path
    app_settings_schema_url: str
