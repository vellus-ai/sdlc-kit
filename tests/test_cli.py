"""
Test suite para core/cli.py
Tests the command-line interface and command handlers.
"""

import json
import sys
from io import StringIO
from pathlib import Path
import pytest
from core.db import connect, run_migrations
from core.cli import main, _init_db, _scan, _status, _require_vault


@pytest.fixture
def vault_with_db(tmp_path, monkeypatch):
    """Creates a vault with initialized database and changes to it."""
    kit_dir = tmp_path / ".sdlc-kit"
    kit_dir.mkdir()
    (kit_dir / "marker.json").write_text(json.dumps({"version": "0.1.0"}))
    db_path = kit_dir / "db.sqlite"
    conn = connect(db_path)
    run_migrations(conn)
    conn.close()
    monkeypatch.chdir(tmp_path)
    yield tmp_path


def test_require_vault_no_vault(tmp_path, monkeypatch, capsys):
    """Test that _require_vault exits with error when no vault is found."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        _require_vault()
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "No vault found" in captured.err


def test_require_vault_success(vault_with_db):
    """Test that _require_vault returns vault and connection."""
    vault, conn = _require_vault()
    assert vault.exists()
    assert conn is not None
    conn.close()


def test_init_db_success(vault_with_db, capsys):
    """Test successful database initialization."""
    _init_db()
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["status"] == "ok"
    assert "db.sqlite" in output["db"]


def test_init_db_no_vault(tmp_path, monkeypatch, capsys):
    """Test init_db exits when no vault is found."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        _init_db()
    assert exc.value.code == 2


def test_scan_command(vault_with_db, capsys):
    """Test scan command output."""
    # Create a markdown file
    md = vault_with_db / "test.md"
    md.write_text("---\ntitle: Test\n---\nBody", encoding="utf-8")

    _scan()
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["created"] == 1
    assert output["skipped"] == 0
    assert output["updated"] == 0


def test_status_command(vault_with_db, capsys):
    """Test status command output."""
    # Create a note in the database
    from core.db import connect
    from core.paths import get_db_path
    conn = connect(get_db_path(vault_with_db))
    conn.execute(
        "INSERT INTO notes (path, title) VALUES (?, ?)",
        ("test.md", "Test Note")
    )
    conn.execute(
        "INSERT INTO tasks (note_id, title, status) VALUES (?, ?, ?)",
        (1, "Task 1", "open")
    )
    conn.execute(
        "INSERT INTO tasks (note_id, title, status) VALUES (?, ?, ?)",
        (1, "Task 2", "done")
    )
    conn.execute(
        "INSERT INTO decisions (note_id, title) VALUES (?, ?)",
        (1, "Decision 1")
    )
    conn.commit()
    conn.close()

    _status()
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["notes"] == 1
    assert output["tasks"]["open"] == 1
    assert output["tasks"]["done"] == 1
    assert output["adrs"] == 1
    assert "vault" in output


def test_main_no_args(capsys):
    """Test main() with no arguments."""
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Usage" in captured.out or "Commands" in captured.out


def test_main_invalid_command(capsys):
    """Test main() with invalid command."""
    sys.argv = ["sdlc-kit", "invalid-cmd"]
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_main_init_db_command(vault_with_db, capsys):
    """Test main() with init-db command."""
    sys.argv = ["sdlc-kit", "init-db"]
    main()
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["status"] == "ok"


def test_main_scan_command(vault_with_db, capsys):
    """Test main() with scan command."""
    md = vault_with_db / "note.md"
    md.write_text("---\ntitle: N\n---\nB", encoding="utf-8")

    sys.argv = ["sdlc-kit", "scan"]
    main()
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["created"] >= 0


def test_main_status_command(vault_with_db, capsys):
    """Test main() with status command."""
    sys.argv = ["sdlc-kit", "status"]
    main()
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert "notes" in output
    assert "tasks" in output
    assert "adrs" in output
