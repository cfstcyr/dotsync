from pathlib import Path
from typing import Any


def load_file(path: str | Path) -> dict[str, Any]:
    path = Path(path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()
    text = path.read_text(encoding="utf-8")

    try:
        if ext in {".yaml", ".yml"}:
            import yaml

            return yaml.safe_load(text) or {}
        if ext == ".json":
            import json

            return json.loads(text)
        if ext == ".toml":
            import toml

            return toml.loads(text)

        raise ValueError(f"Unsupported file extension: {ext}")
    except Exception as e:
        raise ValueError(f"Error parsing file {path}: {e}") from e
