from __future__ import annotations

import json
from pathlib import Path

MARKER_FILE = ".sdlc-kit/marker.json"
DEFAULT_LOCALE = "pt-br"


def find_vault_root(start: Path | None = None) -> Path | None:
    """
    Find the root of an SDLC Kit vault by walking up the directory tree
    looking for the .sdlc-kit/marker.json file.

    Args:
        start: Starting directory. Defaults to current working directory.

    Returns:
        Path to the vault root, or None if not found.
    """
    if start is None:
        start = Path.cwd()
    current = start.resolve()
    while True:
        if (current / MARKER_FILE).exists():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def get_db_path(vault_root: Path) -> Path:
    """
    Get the path to the SQLite database for a vault.

    Args:
        vault_root: Root directory of the vault.

    Returns:
        Path to the database file.
    """
    return vault_root / ".sdlc-kit" / "db.sqlite"


def get_marker_path(vault_root: Path) -> Path:
    """
    Get the path to the marker file for a vault.

    Args:
        vault_root: Root directory of the vault.

    Returns:
        Path to the marker file.
    """
    return vault_root / ".sdlc-kit" / "marker.json"


def read_locale(vault_root: Path) -> str:
    """
    Read the locale from the vault's `.sdlc-kit/marker.json`.

    Returns `pt-br` (the default) when the marker is missing, unreadable,
    or has no `locale` field. Normalizes hyphens and lowercases (so
    `pt_BR` / `pt-BR` / `PT-BR` → `pt-br`).

    Args:
        vault_root: Root directory of the vault.

    Returns:
        The locale string (e.g. `"pt-br"`, `"en"`).
    """
    marker = get_marker_path(vault_root)
    if not marker.exists():
        return DEFAULT_LOCALE
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_LOCALE
    locale = data.get("locale", DEFAULT_LOCALE)
    if not isinstance(locale, str) or not locale.strip():
        return DEFAULT_LOCALE
    return locale.strip().replace("_", "-").lower()
