"""
SQLite database connection and migration management.

Fornece:
- connect(): abre/cria conexão SQLite com WAL mode e FK enabled
- run_migrations(): executa migrações SQL de forma idempotente
"""

import sqlite3
from pathlib import Path

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def connect(db_path: Path) -> sqlite3.Connection:
    """
    Cria ou abre uma conexão SQLite com WAL mode e foreign keys ativadas.

    Args:
        db_path: caminho para o arquivo .sqlite

    Returns:
        sqlite3.Connection: conexão aberta
    """
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def run_migrations(conn: sqlite3.Connection) -> None:
    """
    Executa todas as migrações SQL de forma idempotente.

    Cria a tabela schema_version se não existir, verifica quais
    migrações já foram aplicadas e executa as pendentes na ordem.

    Args:
        conn: conexão SQLite aberta
    """
    # Criar tabela de schema version se não existir
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
    """)
    conn.commit()

    # Ler migrações já aplicadas
    applied = {row[0] for row in conn.execute("SELECT version FROM schema_version")}

    # Executar novas migrações em ordem
    for sql_file in sorted(_MIGRATIONS_DIR.glob("*.sql")):
        # Extrair número de versão do nome do arquivo (ex: 001_initial.sql -> 1)
        version = int(sql_file.stem.split("_")[0])

        if version not in applied:
            # Executar o SQL da migração
            conn.executescript(sql_file.read_text())
            # Registrar na schema_version
            conn.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (?, datetime('now'))",
                (version,)
            )
            conn.commit()
