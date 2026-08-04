from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

VALID_MODES = {"dark", "light"}


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise TypeError("The YAML root must be a mapping.")
    return config


def resolve_path(value, base: Path) -> Path:
    path = Path(os.path.expandvars(str(value))).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def normalize_config(raw: dict[str, Any], config_path: Path, project_root: Path) -> dict[str, Any]:
    dataset = raw.get("dataset", {})
    mode = str(dataset.get("mode", "")).lower()
    if mode not in VALID_MODES:
        raise ValueError("dataset.mode must be 'dark' or 'light'.")
    inputs = dict(raw.get("inputs", {}))
    output = dict(raw.get("output", {}))
    if "directory" not in output:
        raise KeyError("Missing output.directory")
    output["directory"] = resolve_path(output["directory"], project_root)
    output["directory"].mkdir(parents=True, exist_ok=True)
    for key, value in list(inputs.items()):
        if value is not None and ("file" in key or "directory" in key or key in {"stream", "params", "delays"}):
            inputs[key] = resolve_path(value, project_root)
    config = dict(raw)
    config["dataset"] = {**dataset, "mode": mode, "name": dataset.get("name", mode)}
    config["inputs"] = inputs
    config["output"] = output
    config["project_root"] = project_root
    config["config_path"] = config_path
    return config
