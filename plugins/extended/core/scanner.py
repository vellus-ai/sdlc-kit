"""
Incremental scanner for markdown files in a vault.

Implements delta scanning at 3 levels:
1. mtime (modification time) — fast path for unchanged files
2. hash — detect content changes despite mtime updates
3. reparse — extract metadata and store in database

Returns counts: created, updated, skipped.
Records events: note_created, note_updated.
"""

import datetime
import json
import sqlite3
from pathlib import Path

from .parser import parse


def _json_default(obj):
    """JSON serializer for types not handled by default json encoder."""
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def scan(vault_root: Path, conn: sqlite3.Connection) -> dict:
    """
    Scan all markdown files in vault_root and update database.

    Args:
        vault_root: Path to the vault root directory.
        conn: SQLite connection object.

    Returns:
        Dict with keys: created, updated, skipped.
    """
    created = updated = skipped = 0

    for md_file in vault_root.rglob("*.md"):
        # Skip files inside .sdlc-kit directory
        if ".sdlc-kit" in md_file.parts:
            continue

        # Get relative path from vault root
        rel = str(md_file.relative_to(vault_root))

        # Get current mtime
        mtime = md_file.stat().st_mtime

        # Check if file already in database
        row = conn.execute(
            "SELECT id, mtime FROM notes WHERE path = ?", (rel,)
        ).fetchone()

        # Fast path: if mtime unchanged, skip
        if row and abs(row[1] - mtime) < 0.01:
            skipped += 1
            continue

        # Parse markdown file
        parsed = parse(md_file)
        fm = parsed["frontmatter"]

        # Extract metadata
        title = fm.get("title") or md_file.stem
        phase = fm.get("phase") or _infer_phase(rel)
        doc_type = fm.get("type", "note")
        status = fm.get("status", "")
        created_at = fm.get("created", "")
        updated_at = fm.get("updated", "")
        # Convert date/datetime objects to ISO strings for SQLite storage
        if isinstance(created_at, (datetime.date, datetime.datetime)):
            created_at = created_at.isoformat()
        if isinstance(updated_at, (datetime.date, datetime.datetime)):
            updated_at = updated_at.isoformat()
        fm_json = json.dumps(fm, default=_json_default)

        # Update or insert
        if row:
            # Update existing note
            conn.execute(
                """UPDATE notes SET title=?, phase=?, type=?, status=?,
                   updated=?, mtime=?, frontmatter_json=? WHERE id=?""",
                (title, phase, doc_type, status, updated_at, mtime, fm_json, row[0]),
            )
            conn.execute(
                "INSERT INTO events (note_id, event_type) VALUES (?, 'note_updated')",
                (row[0],),
            )
            updated += 1
        else:
            # Insert new note
            cur = conn.execute(
                """INSERT INTO notes
                   (path, title, phase, type, status, created, updated, mtime, frontmatter_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (rel, title, phase, doc_type, status, created_at, updated_at, mtime, fm_json),
            )
            conn.execute(
                "INSERT INTO events (note_id, event_type) VALUES (?, 'note_created')",
                (cur.lastrowid,),
            )
            created += 1

    # Commit all changes
    conn.commit()

    return {"created": created, "updated": updated, "skipped": skipped}


def _infer_phase(rel_path: str) -> str:
    """
    Infer phase from relative path.

    Looks for patterns: 01-, 02-, ..., 07- at the start or after /.

    Args:
        rel_path: Relative path from vault root (e.g., "02-architecture/design.md").

    Returns:
        Phase number as string (e.g., "02") or empty string if not found.
    """
    for prefix in ("01-", "02-", "03-", "04-", "05-", "06-", "07-"):
        if rel_path.startswith(prefix) or f"/{prefix}" in rel_path:
            return prefix[:2]
    return ""
