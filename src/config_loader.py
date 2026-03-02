from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


def load_settings(config_path: str = "config/settings.yaml") -> Dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)
