import json
from pathlib import Path

from deepdiff import DeepDiff

from dotsync.models.app_settings.app_settings import AppSettings


def update_schema(path: Path, model: type[AppSettings]):
    model_json = model.model_json_schema()

    with path.open("r", encoding="utf-8") as f:
        existing_json = json.load(f)

    diff = DeepDiff(existing_json, model_json, ignore_order=True)
    if diff.get("dictionary_item_added") or diff.get("dictionary_item_removed"):
        with path.open("w", encoding="utf-8") as f:
            json.dump(model_json, f, indent=2)
            f.write("\n")


def export_schemas(
    directory: str = "schemas",
    app_settings_filename: str = "app_settings.schema.json",
):
    directory_path = Path(directory).expanduser().resolve()
    directory_path.mkdir(parents=True, exist_ok=True)

    update_schema(directory_path / app_settings_filename, AppSettings)


if __name__ == "__main__":
    export_schemas()
