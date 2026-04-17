import json
import time
from pathlib import Path
import pytest
from core.db import connect, run_migrations
from core.scanner import scan


@pytest.fixture
def vault_with_db(tmp_path):
    """Cria um vault temporário com banco de dados inicializado."""
    kit_dir = tmp_path / ".sdlc-kit"
    kit_dir.mkdir()
    (kit_dir / "marker.json").write_text('{"version":"0.1.0"}')
    db_path = kit_dir / "db.sqlite"
    conn = connect(db_path)
    run_migrations(conn)
    return tmp_path, conn


def _write_md(path: Path, content: str) -> None:
    """Helper para escrever markdown."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_scan_creates_note(vault_with_db):
    """Testa criação de nova nota durante scan."""
    vault, conn = vault_with_db
    _write_md(vault / "01-planning" / "test.md", "---\ntitle: Test\n---\nBody")
    result = scan(vault, conn)
    assert result["created"] == 1
    assert result["updated"] == 0
    row = conn.execute("SELECT title FROM notes WHERE path LIKE '%test.md'").fetchone()
    assert row[0] == "Test"


def test_scan_skips_unchanged(vault_with_db):
    """Testa que scan não reprocessa notas inalteradas."""
    vault, conn = vault_with_db
    _write_md(vault / "note.md", "---\ntitle: Stable\n---\nBody")
    scan(vault, conn)
    result = scan(vault, conn)
    assert result["created"] == 0
    assert result["skipped"] == 1


def test_scan_updates_modified(vault_with_db):
    """Testa atualização de nota modificada."""
    vault, conn = vault_with_db
    p = vault / "note.md"
    _write_md(p, "---\ntitle: Old\n---\nBody")
    scan(vault, conn)
    time.sleep(0.05)
    import os
    p.write_text("---\ntitle: New\n---\nUpdated body", encoding="utf-8")
    os.utime(p, None)
    result = scan(vault, conn)
    assert result["updated"] == 1
    row = conn.execute("SELECT title FROM notes WHERE path LIKE '%note.md'").fetchone()
    assert row[0] == "New"


def test_scan_infers_phase(vault_with_db):
    """Testa inferência de phase a partir do caminho."""
    vault, conn = vault_with_db
    _write_md(vault / "02-architecture" / "design.md", "# Design")
    scan(vault, conn)
    row = conn.execute("SELECT phase FROM notes WHERE path LIKE '%design.md'").fetchone()
    assert row[0] == "02"


def test_scan_records_event(vault_with_db):
    """Testa que eventos são registrados corretamente."""
    vault, conn = vault_with_db
    _write_md(vault / "note.md", "# Note")
    scan(vault, conn)
    events = conn.execute("SELECT event_type FROM events").fetchall()
    assert any(e[0] == "note_created" for e in events)
