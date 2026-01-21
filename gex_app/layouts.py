"""
Layout management for saving and loading dashboard configurations.

This module provides functionality to save, load, and delete named dashboard layouts
that persist across application restarts via JSON storage.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class Layout:
    """
    Represents a saved dashboard configuration layout.

    Attributes:
        name: Human-readable name for the layout
        symbol: Ticker symbol to analyze
        max_dte: Maximum days to expiration
        strike_range_pct: Strike range percentage from spot
        major_threshold: Major level threshold in millions
        data_wait: Data collection time in seconds
        auto_update: Whether to auto-update every 60 seconds
    """

    name: str
    symbol: str
    max_dte: int
    strike_count: int
    major_threshold: float
    data_wait: int
    auto_update: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert layout to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Layout:
        """Create layout instance from dictionary."""
        # Migration: strike_range_pct -> strike_count
        if "strike_range_pct" in data:
            # We ignore the old percentage value and default to 20 strikes
            # or we could try to approximate, but 20 is safe.
            data.pop("strike_range_pct")
            if "strike_count" not in data:
                data["strike_count"] = 20
        return cls(**data)


# Path to layouts.json file within the package
_LAYOUTS_PATH = Path(__file__).resolve().parent / "data" / "layouts.json"


def _ensure_layouts_dir() -> None:
    """Ensure the data directory exists for layouts storage."""
    _LAYOUTS_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_layouts() -> list[Layout]:
    """
    Load all saved layouts from JSON file.

    Returns:
        List of Layout objects, empty list if file doesn't exist
    """
    if not _LAYOUTS_PATH.exists():
        return []

    try:
        with _LAYOUTS_PATH.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        return [Layout.from_dict(item) for item in raw]
    except (json.JSONDecodeError, KeyError, TypeError):
        # If file is corrupted, start fresh
        return []


def save_layouts(layouts: list[Layout]) -> None:
    """
    Save all layouts to JSON file.

    Args:
        layouts: List of Layout objects to save
    """
    _ensure_layouts_dir()
    with _LAYOUTS_PATH.open("w", encoding="utf-8") as f:
        json.dump([layout.to_dict() for layout in layouts], f, indent=2)


def upsert_layout(new_layout: Layout) -> None:
    """
    Save a new layout or update an existing one by name.

    Args:
        new_layout: Layout to save or update
    """
    layouts = load_layouts()
    # Remove existing layout with same name, then add new one
    filtered = [l for l in layouts if l.name != new_layout.name]
    filtered.append(new_layout)
    save_layouts(filtered)


def delete_layout(name: str) -> None:
    """
    Delete a layout by name.

    Args:
        name: Name of the layout to delete
    """
    layouts = load_layouts()
    filtered = [l for l in layouts if l.name != name]
    save_layouts(filtered)


def get_layout_names() -> list[str]:
    """
    Get list of all layout names.

    Returns:
        List of layout names in alphabetical order
    """
    layouts = load_layouts()
    return sorted([layout.name for layout in layouts])


def get_layout_by_name(name: str) -> Layout | None:
    """
    Get a layout by name.

    Args:
        name: Name of the layout to retrieve

    Returns:
        Layout object if found, None otherwise
    """
    layouts = load_layouts()
    for layout in layouts:
        if layout.name == name:
            return layout
    return None
