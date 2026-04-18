import json
from pathlib import Path
import pytest
from core.paths import DEFAULT_LOCALE, find_vault_root, get_db_path, get_marker_path, read_locale


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


def test_read_locale_default_when_missing(tmp_path):
    """No marker → default pt-br."""
    assert read_locale(tmp_path) == DEFAULT_LOCALE


def test_read_locale_default_when_absent_in_marker(vault):
    """Marker without locale field → default pt-br."""
    assert read_locale(vault) == DEFAULT_LOCALE


def test_read_locale_returns_en(tmp_path):
    marker = tmp_path / ".sdlc-kit"
    marker.mkdir()
    (marker / "marker.json").write_text(
        json.dumps({"version": "0.2.0", "locale": "en"}), encoding="utf-8"
    )
    assert read_locale(tmp_path) == "en"


def test_read_locale_normalizes_case_and_separator(tmp_path):
    marker = tmp_path / ".sdlc-kit"
    marker.mkdir()
    (marker / "marker.json").write_text(
        json.dumps({"version": "0.2.0", "locale": "PT_BR"}), encoding="utf-8"
    )
    assert read_locale(tmp_path) == "pt-br"


def test_read_locale_ignores_empty_string(tmp_path):
    marker = tmp_path / ".sdlc-kit"
    marker.mkdir()
    (marker / "marker.json").write_text(
        json.dumps({"version": "0.2.0", "locale": "  "}), encoding="utf-8"
    )
    assert read_locale(tmp_path) == DEFAULT_LOCALE


def test_read_locale_ignores_non_string(tmp_path):
    marker = tmp_path / ".sdlc-kit"
    marker.mkdir()
    (marker / "marker.json").write_text(
        json.dumps({"version": "0.2.0", "locale": 42}), encoding="utf-8"
    )
    assert read_locale(tmp_path) == DEFAULT_LOCALE


def test_read_locale_handles_malformed_json(tmp_path):
    marker = tmp_path / ".sdlc-kit"
    marker.mkdir()
    (marker / "marker.json").write_text("{ not valid json", encoding="utf-8")
    assert read_locale(tmp_path) == DEFAULT_LOCALE
