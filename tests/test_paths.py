import json
from pathlib import Path
import pytest
from core.paths import find_vault_root, get_db_path, get_marker_path


@pytest.fixture
def vault(tmp_path):
    marker_dir = tmp_path / ".sdlc-kit"
    marker_dir.mkdir()
    (marker_dir / "marker.json").write_text(json.dumps({"version": "0.1.0"}))
    return tmp_path


def test_find_vault_root_from_root(vault):
    assert find_vault_root(vault) == vault


def test_find_vault_root_from_subdir(vault):
    subdir = vault / "deep" / "nested"
    subdir.mkdir(parents=True)
    assert find_vault_root(subdir) == vault


def test_find_vault_root_missing(tmp_path):
    assert find_vault_root(tmp_path) is None


def test_get_db_path(vault):
    assert get_db_path(vault) == vault / ".sdlc-kit" / "db.sqlite"


def test_get_marker_path(vault):
    assert get_marker_path(vault) == vault / ".sdlc-kit" / "marker.json"


def test_find_vault_root_from_cwd_default(vault, monkeypatch):
    """Test that find_vault_root uses cwd when no start path is given."""
    monkeypatch.chdir(vault)
    assert find_vault_root() == vault


def test_find_vault_root_from_deeply_nested_subdir(vault):
    """Test discovery from deeply nested directory."""
    deep = vault / "a" / "b" / "c" / "d" / "e"
    deep.mkdir(parents=True)
    assert find_vault_root(deep) == vault
