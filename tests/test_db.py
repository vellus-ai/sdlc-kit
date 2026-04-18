"""
Test suite para core/db.py
TDD: testes antes da implementação
"""

import pytest

from core.db import connect, run_migrations


@pytest.fixture
def db(tmp_path):
    """Fixture que retorna uma conexão SQLite em modo de testes."""
    db_path = tmp_path / "test.sqlite"
    conn = connect(db_path)
    run_migrations(conn)
    return conn


def test_connect_creates_file(tmp_path):
    """Verifica se connect() cria o arquivo do banco de dados."""
    db_path = tmp_path / "test.sqlite"
    conn = connect(db_path)
    assert db_path.exists()
    conn.close()


def test_migrations_create_all_tables(db):
    """Verifica se as migrações criam todas as tabelas esperadas."""
    tables = {row[0] for row in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    expected = {"notes", "events", "links", "tasks", "decisions", "worktrees", "schema_version"}
    assert expected.issubset(tables)


def test_migrations_idempotent(tmp_path):
    """Verifica se as migrações são idempotentes (seguro executar múltiplas vezes)."""
    db_path = tmp_path / "test.sqlite"
    conn = connect(db_path)
    run_migrations(conn)
    run_migrations(conn)  # segunda chamada não deve falhar
    count = conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0]
    assert count == 1  # apenas uma migração deve estar aplicada


def test_wal_mode_enabled(tmp_path):
    """Verifica se o modo WAL está ativado."""
    db_path = tmp_path / "test.sqlite"
    conn = connect(db_path)
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode == "wal"


def test_foreign_keys_enabled(db):
    """Verifica se as constraint de chave estrangeira estão ativadas."""
    result = db.execute("PRAGMA foreign_keys").fetchone()[0]
    assert result == 1
