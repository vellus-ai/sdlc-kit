from pathlib import Path

MARKER_FILE = ".sdlc-kit/marker.json"


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
