import json
from pathlib import Path

from deepdiff import DeepDiff
from pydantic import BaseModel

from dotsync.models.app_settings import AppSettings
from dotsync.models.sync_config.sync_config import SyncConfig


def update_schema(path: Path, model: type[BaseModel]):
    model_json = model.model_json_schema()

    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            existing_json = json.load(f)
    else:
        existing_json = None

    diff = DeepDiff(existing_json, model_json, ignore_order=True)

    if bool(diff):
        with path.open("w", encoding="utf-8") as f:
            json.dump(model_json, f, indent=2)
            f.write("\n")


def export_schemas(
    directory: str = "schemas",
    app_settings_filename: str = "app_settings.schema.json",
    sync_config_filename: str = "sync_config.schema.json",
):
    directory_path = Path(directory).expanduser().resolve()
    directory_path.mkdir(parents=True, exist_ok=True)

    update_schema(directory_path / app_settings_filename, AppSettings)
    update_schema(directory_path / sync_config_filename, SyncConfig)


if __name__ == "__main__":
    export_schemas()
