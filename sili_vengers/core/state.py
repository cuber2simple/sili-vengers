"""Core state management for Sili-vengers"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import tomllib
import tomli_w

VENGERS_DIR = ".vengers"
VENGERS_TOML = ".vengers/.vengers.toml"


def get_vengers_dir() -> Path:
    return Path(VENGERS_DIR)


def get_toml_path() -> Path:
    return Path(VENGERS_TOML)


def get_agents_dir() -> Path:
    return Path(VENGERS_DIR) / "agents"


def get_hooks_dir() -> Path:
    return Path(VENGERS_DIR) / "hooks"


def get_feature_dir(feature: str, date: str) -> Path:
    return Path(VENGERS_DIR) / f"{feature}_{date}"


def load_toml() -> dict:
    toml_path = get_toml_path()
    if not toml_path.exists():
        return {}
    with open(toml_path, "rb") as f:
        return tomllib.load(f)


def save_toml(data: dict):
    toml_path = get_toml_path()
    toml_path.parent.mkdir(parents=True, exist_ok=True)
    with open(toml_path, "wb") as f:
        tomli_w.dump(data, f)


def load_task_json(feature: str, date: str) -> dict:
    feature_dir = get_feature_dir(feature, date)
    task_path = feature_dir / "task.json"
    if not task_path.exists():
        return {"tasks": []}
    with open(task_path) as f:
        return json.load(f)


def save_task_json(feature: str, date: str, data: dict):
    feature_dir = get_feature_dir(feature, date)
    feature_dir.mkdir(parents=True, exist_ok=True)
    task_path = feature_dir / "task.json"
    with open(task_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_active_features(toml_data: dict) -> list:
    """Return list of active (non-stopped) features"""
    features = toml_data.get("vengers", {})
    active = []
    for key, val in features.items():
        if isinstance(val, dict) and val.get("status") not in ("stopped", "done"):
            active.append({
                "key": key,
                "feature": val.get("feature", key),
                "prompt_summary": val.get("prompt_summary", ""),
                "created_at": val.get("created_at", ""),
                "status": val.get("status", "unknown"),
                "date": val.get("date", ""),
            })
    return active


def get_sleeping_features(toml_data: dict) -> list:
    """Return stopped/sleeping features"""
    features = toml_data.get("vengers", {})
    sleeping = []
    for key, val in features.items():
        if isinstance(val, dict) and val.get("status") == "stopped":
            sleeping.append({
                "key": key,
                "feature": val.get("feature", key),
                "prompt_summary": val.get("prompt_summary", ""),
                "created_at": val.get("created_at", ""),
                "status": val.get("status", "unknown"),
                "date": val.get("date", ""),
            })
    return sleeping


def register_feature(feature: str, prompt_summary: str) -> str:
    """Register a new feature in .vengers.toml, returns date string"""
    date = datetime.now().strftime("%Y%m%d_%H%M%S")
    toml_data = load_toml()

    if "vengers" not in toml_data:
        toml_data["vengers"] = {}

    key = f"{feature}_{date}"
    toml_data["vengers"][key] = {
        "feature": feature,
        "prompt_summary": prompt_summary,
        "created_at": datetime.now().isoformat(),
        "date": date,
        "status": "active",
    }
    save_toml(toml_data)
    return date


def update_feature_status(feature: str, date: str, status: str):
    toml_data = load_toml()
    key = f"{feature}_{date}"
    if "vengers" in toml_data and key in toml_data["vengers"]:
        toml_data["vengers"][key]["status"] = status
        toml_data["vengers"][key]["updated_at"] = datetime.now().isoformat()
        save_toml(toml_data)


def is_initialized() -> bool:
    return get_toml_path().exists()


def get_task_by_id(tasks: list, task_id: str) -> Optional[dict]:
    for t in tasks:
        if t.get("id") == task_id:
            return t
    return None


def update_task_status(feature: str, date: str, task_id: str, status: str, result: Optional[str] = None):
    data = load_task_json(feature, date)
    for t in data.get("tasks", []):
        if t.get("id") == task_id:
            t["status"] = status
            if result:
                t["result_file"] = result
            t["updated_at"] = datetime.now().isoformat()
    save_task_json(feature, date, data)
