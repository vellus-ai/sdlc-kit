"""Tests for sdlc-status — vault health summary.

Covers the three return paths of ``skills/sdlc-status/scripts/status.py``:

- exit 0 + JSON with counts when the vault has a fully migrated SQLite DB
- exit 1 when the vault is valid but the DB file is absent
- exit 2 when the given vault directory has no ``.sdlc-kit/marker.json``

The DB is populated via the same ``core.db`` migrations used in production so
the counts exercise both the "empty" case and a seeded case with notes,
tasks and decisions across the ``phase`` groupings.
"""
from __future__ import annotations

from pathlib import Path

from core.db import connect, run_migrations
from tests._skill_helpers import make_vault, parse_json, run_script


SCRIPT = "sdlc-status/scripts/status.py"


def _init_db(vault: Path):
    """Initialise the SQLite DB inside ``vault/.sdlc-kit/`` and return the
    open connection. Callers are responsible for closing it before the
    subprocess test invocation so Windows does not keep the file locked.
    """
    db_path = vault / ".sdlc-kit" / "db.sqlite"
    conn = connect(db_path)
    run_migrations(conn)
    return conn


class TestStatusSkill:
    # ------------------------------------------------------------------
    # Happy path — empty DB
    # ------------------------------------------------------------------
    def test_empty_db_returns_zeroed_counts(self, tmp_path):
        vault = make_vault(tmp_path)
        conn = _init_db(vault)
        conn.close()

        cp = run_script(SCRIPT, ["--vault-root", str(vault)])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["status"] == "ok"
        assert data["vault"] == str(vault)
        assert data["notes_total"] == 0
        assert data["notes_by_phase"] == {}
        assert data["tasks"] == {"open": 0, "done": 0}
        assert data["adrs"] == {"accepted": 0, "proposed": 0}

    # ------------------------------------------------------------------
    # Happy path — seeded DB exercises every count + phase grouping
    # ------------------------------------------------------------------
    def test_seeded_db_returns_correct_counts(self, tmp_path):
        vault = make_vault(tmp_path)
        conn = _init_db(vault)
        # Seed notes across two phases + one with phase=NULL to prove the
        # `phase or "unknown"` fallback path is exercised.
        conn.executemany(
            "INSERT INTO notes (path, title, phase) VALUES (?, ?, ?)",
            [
                ("01-planning/prd-a.md", "PRD A", "01"),
                ("01-planning/prd-b.md", "PRD B", "01"),
                ("02-architecture/adr-01.md", "ADR 1", "02"),
                ("orphan.md", "Orphan", None),
            ],
        )
        # Tasks: 2 open, 1 done — plus one with a status the query ignores.
        conn.executemany(
            "INSERT INTO tasks (title, status) VALUES (?, ?)",
            [
                ("t-open-1", "open"),
                ("t-open-2", "open"),
                ("t-done-1", "done"),
                ("t-blocked", "blocked"),
            ],
        )
        # Decisions: 1 accepted, 2 proposed, 1 irrelevant status.
        conn.executemany(
            "INSERT INTO decisions (title, status) VALUES (?, ?)",
            [
                ("d-1", "accepted"),
                ("d-2", "proposed"),
                ("d-3", "proposed"),
                ("d-4", "rejected"),
            ],
        )
        conn.commit()
        conn.close()

        cp = run_script(SCRIPT, ["--vault-root", str(vault)])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["status"] == "ok"
        assert data["notes_total"] == 4
        # phase grouping with NULL bucketed as "unknown"
        assert data["notes_by_phase"] == {"01": 2, "02": 1, "unknown": 1}
        assert data["tasks"] == {"open": 2, "done": 1}
        assert data["adrs"] == {"accepted": 1, "proposed": 2}

    # ------------------------------------------------------------------
    # DB not initialised — the marker exists but db.sqlite does not
    # ------------------------------------------------------------------
    def test_exits_1_when_db_missing(self, tmp_path):
        vault = make_vault(tmp_path)  # marker written, no DB
        cp = run_script(SCRIPT, ["--vault-root", str(vault)])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert data["status"] == "error"
        assert "db not initialized" in data["message"]

    # ------------------------------------------------------------------
    # Vault missing — directory has no marker file
    # ------------------------------------------------------------------
    def test_exits_2_when_vault_root_has_no_marker(self, tmp_path):
        # Explicitly create a directory with NO .sdlc-kit marker.
        not_a_vault = tmp_path / "elsewhere"
        not_a_vault.mkdir()
        cp = run_script(SCRIPT, ["--vault-root", str(not_a_vault)])
        assert cp.returncode == 2
        data = parse_json(cp)
        assert data["status"] == "error"
        assert "not a valid vault" in data["message"]

    # ------------------------------------------------------------------
    # --dry-run flag is accepted (no-op for this script — but argparse
    # must not reject it and the happy path must still emit JSON)
    # ------------------------------------------------------------------
    def test_dry_run_flag_accepted(self, tmp_path):
        vault = make_vault(tmp_path)
        conn = _init_db(vault)
        conn.close()
        cp = run_script(SCRIPT, ["--vault-root", str(vault), "--dry-run"])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["status"] == "ok"
