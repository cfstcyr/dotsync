from dataclasses import dataclass, field
from pathlib import Path

from dotsync.models.app_settings import AppSettings


@dataclass
class AppState:
    app_settings_path: Path
    app_settings_overrides: list[str]
    app_settings: AppSettings = field(init=False)

    def __post_init__(self):
        self.app_settings = AppSettings.load(
            app_settings_path=self.app_settings_path,
            overrides=self.app_settings_overrides,
        )
