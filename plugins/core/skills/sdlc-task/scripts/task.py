#!/usr/bin/env python3
"""Manage TASK-NNN Kiro markers inside a feature's `04-specs/<slug>/tasks.md`.

This script is the deterministic operator over the spec trio's `tasks.md`
file. It never creates a standalone `task` document — the spec-tasks file is
the single source of truth, authored by `/sdlc-kit:spec` and executed by the
engineer via `/sdlc-kit:task`.

Kiro marker convention:

    - [ ]   queued           (planned, not started)
    - [-]   in_progress      (actively being worked on — ONE at a time)
    - [x]   completed        (delivered, merged, worktree cleaned)
    - [~]   needs_attention  (blocked; reason noted on the next line)

Actions:
    list     --feature <slug>
                List every TASK line in the feature's tasks.md with its
                current marker and logical status.
    start    --feature <slug> --id TASK-NNN
                Flip `[ ]` → `[-]`. Refuses if any other task in the same
                file is already `[-]` (enforces the "one in-progress at a
                time" rule); use `--allow-multi-active` to override.
    complete --feature <slug> --id TASK-NNN
                Flip `[-]` or `[ ]` → `[x]`. Accepts an optional `--note`.
    block    --feature <slug> --id TASK-NNN --note "why"
                Flip current marker → `[~]` and write the note on the line
                below (or update an existing blocker note).
    reopen   --feature <slug> --id TASK-NNN
                Flip `[x]` or `[~]` → `[ ]`. Removes any previous blocker
                note written by this script.

Never rewrites task text, IDs, requirements links, indentation, or phase
headings — only the 3-char marker `[ ]` / `[-]` / `[x]` / `[~]` and an
adjacent blocker note. Updates the `updated:` frontmatter field on write.

Emits a single JSON object on stdout. Exit codes: 0 ok/dry-run, 1 user error,
2 fatal.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from core.regexes import FRONTMATTER_RE, SLUG_RE, UPDATED_LINE  # noqa: E402

SPECS_DIR = "04-specs"
TASKS_FILE = "tasks.md"

MARKER_QUEUED = "[ ]"
MARKER_IN_PROGRESS = "[-]"
MARKER_COMPLETED = "[x]"
MARKER_BLOCKED = "[~]"

ALL_MARKERS = (MARKER_QUEUED, MARKER_IN_PROGRESS, MARKER_COMPLETED, MARKER_BLOCKED)

MARKER_TO_STATUS: dict[str, str] = {
    MARKER_QUEUED: "queued",
    MARKER_IN_PROGRESS: "in_progress",
    MARKER_COMPLETED: "completed",
    MARKER_BLOCKED: "needs_attention",
}

BLOCKED_NOTE_PREFIX = "      > blocked: "

# Matches a task line: optional indent, "- [", marker char, "] " prefix,
# then the TASK-NNN id bolded, then the rest of the title.
#   indent      marker_char           id
#   (^\s*)- \[([ \-x~])\]\s+\*\*(TASK-\d+)\*\*
_TASK_LINE_RE = re.compile(
    r"^(?P<indent>\s*)- \[(?P<marker>[ \-x~])\]\s+\*\*(?P<id>TASK-\d+)\*\*(?P<rest>.*)$"
)

_TASK_ID_RE = re.compile(r"^TASK-\d+$")


# ---------------------------------------------------------------------------
# data classes
# ---------------------------------------------------------------------------

@dataclass
class TaskLine:
    id: str
    line: int
    marker: str
    status: str
    title: str
    has_blocker_note: bool = False
    blocker_note: str = ""


@dataclass
class Report:
    status: str = "ok"
    action: str = ""
    vault_root: str = ""
    feature: str = ""
    tasks_path: str = ""
    task_id: str = ""
    previous_marker: str = ""
    new_marker: str = ""
    previous_status: str = ""
    new_status: str = ""
    tasks: list[TaskLine] = field(default_factory=list)
    count: int = 0
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        d: dict = {
            "status": self.status,
            "action": self.action,
            "vault_root": self.vault_root,
            "feature": self.feature,
            "tasks_path": self.tasks_path,
            "errors": self.errors,
        }
        if self.action == "list":
            d["tasks"] = [vars(t) for t in self.tasks]
            d["count"] = self.count
        else:
            d["task_id"] = self.task_id
            d["previous_marker"] = self.previous_marker
            d["new_marker"] = self.new_marker
            d["previous_status"] = self.previous_status
            d["new_status"] = self.new_status
        return d


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def die(report: Report, message: str, code: int = 2) -> None:
    report.status = "error"
    report.errors.append(message)
    print(json.dumps(report.as_dict(), ensure_ascii=False))
    sys.exit(code)


def resolve_vault(arg: str, report: Report) -> Path:
    vault = Path(arg).resolve()
    if not vault.exists():
        die(report, f"vault root does not exist: {vault}", code=1)
    if not (vault / ".sdlc-kit").exists():
        die(report, f"not a vault (missing .sdlc-kit marker): {vault}", code=1)
    return vault


def rel(vault: Path, path: Path) -> str:
    return str(path.relative_to(vault)).replace("\\", "/")


def _marker_char_to_marker(ch: str) -> str:
    return f"[{ch}]"


def parse_task_lines(text: str) -> list[TaskLine]:
    out: list[TaskLine] = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        m = _TASK_LINE_RE.match(line)
        if not m:
            continue
        marker = _marker_char_to_marker(m.group("marker"))
        title = m.group("rest").strip(" —-")
        has_note = False
        note = ""
        if i < len(lines):
            nxt = lines[i]  # 0-indexed next line
            if nxt.startswith(BLOCKED_NOTE_PREFIX.rstrip()):
                has_note = True
                note = nxt[len(BLOCKED_NOTE_PREFIX):].strip() if nxt.startswith(BLOCKED_NOTE_PREFIX) else nxt.split(":", 1)[-1].strip()
        out.append(TaskLine(
            id=m.group("id"),
            line=i,
            marker=marker,
            status=MARKER_TO_STATUS[marker],
            title=title,
            has_blocker_note=has_note,
            blocker_note=note,
        ))
    return out


def update_frontmatter_updated(text: str, today: str) -> str:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return text
    fm_text = m.group(1)
    rest = text[m.end():]
    if UPDATED_LINE.search(fm_text):
        new_fm = UPDATED_LINE.sub(rf"\g<1>{today}", fm_text, count=1)
    else:
        new_fm = fm_text + f"\nupdated: {today}"
    return f"---\n{new_fm}\n---\n{rest}"


def resolve_tasks_path(vault: Path, feature: str, report: Report) -> Path:
    if not SLUG_RE.match(feature):
        die(report, f"invalid --feature slug `{feature}`: must match [a-z0-9][a-z0-9-]*", code=1)
    path = vault / SPECS_DIR / feature / TASKS_FILE
    report.tasks_path = rel(vault, path)
    if not path.exists():
        die(report, f"tasks file not found: {report.tasks_path} (scaffold the spec trio first)", code=1)
    return path


# ---------------------------------------------------------------------------
# action: list
# ---------------------------------------------------------------------------

def action_list(vault: Path, *, feature: str, report: Report) -> None:
    report.action = "list"
    report.feature = feature
    path = resolve_tasks_path(vault, feature, report)
    text = path.read_text(encoding="utf-8", errors="replace")
    report.tasks = parse_task_lines(text)
    report.count = len(report.tasks)


# ---------------------------------------------------------------------------
# transition logic
# ---------------------------------------------------------------------------

def _find_task(tasks: list[TaskLine], task_id: str) -> TaskLine | None:
    for t in tasks:
        if t.id == task_id:
            return t
    return None


def _replace_marker_on_line(lines: list[str], zero_idx: int, new_marker: str) -> None:
    line = lines[zero_idx]
    m = _TASK_LINE_RE.match(line)
    if not m:
        return
    start = m.start() + len(m.group("indent")) + 2  # "- "
    end = start + 3  # "[x]"
    lines[zero_idx] = line[:start] + new_marker + line[end:]


def _strip_existing_note(lines: list[str], after_zero_idx: int) -> bool:
    """Remove a blocker note immediately following the task line, if present."""
    nxt_idx = after_zero_idx + 1
    if nxt_idx >= len(lines):
        return False
    if lines[nxt_idx].startswith(BLOCKED_NOTE_PREFIX.rstrip()):
        del lines[nxt_idx]
        return True
    return False


def _insert_blocker_note(lines: list[str], after_zero_idx: int, note: str) -> None:
    note_line = f"{BLOCKED_NOTE_PREFIX}{note.strip()}"
    lines.insert(after_zero_idx + 1, note_line)


def _write_transition(
    vault: Path,
    *,
    feature: str,
    task_id: str,
    target_marker: str,
    note: str | None,
    allow_multi_active: bool,
    dry_run: bool,
    report: Report,
) -> None:
    if target_marker not in ALL_MARKERS:
        die(report, f"internal error: invalid target marker `{target_marker}`", code=2)
    report.feature = feature
    report.task_id = task_id

    if not _TASK_ID_RE.match(task_id):
        die(report, f"invalid --id `{task_id}`: expected TASK-<digits>", code=1)

    path = resolve_tasks_path(vault, feature, report)
    text = path.read_text(encoding="utf-8", errors="replace")
    tasks = parse_task_lines(text)
    target = _find_task(tasks, task_id)
    if target is None:
        die(report, f"{task_id} not found in {report.tasks_path}", code=1)

    report.previous_marker = target.marker
    report.previous_status = target.status

    # Single-active invariant (only when flipping to in-progress).
    if target_marker == MARKER_IN_PROGRESS and not allow_multi_active:
        other_active = [t for t in tasks if t.marker == MARKER_IN_PROGRESS and t.id != task_id]
        if other_active:
            names = ", ".join(t.id for t in other_active)
            die(
                report,
                f"refusing to start {task_id}: already in-progress → {names}. "
                f"Complete or block it first, or pass --allow-multi-active.",
                code=1,
            )

    # Blocker requires a note.
    if target_marker == MARKER_BLOCKED and not (note and note.strip()):
        die(report, "`block` requires --note explaining the blocker", code=1)

    lines = text.splitlines()
    zero_idx = target.line - 1

    # Idempotent: no-op when already at the target marker, with optional note refresh for blocked.
    needs_write = target.marker != target_marker
    if target_marker == MARKER_BLOCKED and note:
        # Refresh the note even if the marker is already [~].
        if _strip_existing_note(lines, zero_idx):
            needs_write = True
        _insert_blocker_note(lines, zero_idx, note)
        needs_write = True

    if target.marker != target_marker:
        _replace_marker_on_line(lines, zero_idx, target_marker)
        # Clean up stale blocker notes when leaving [~] to anything but [~].
        if target.marker == MARKER_BLOCKED and target_marker != MARKER_BLOCKED:
            _strip_existing_note(lines, zero_idx)

    report.new_marker = target_marker
    report.new_status = MARKER_TO_STATUS[target_marker]

    if not needs_write:
        return  # idempotent

    new_text = "\n".join(lines)
    if text.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"
    today = _dt.date.today().isoformat()
    new_text = update_frontmatter_updated(new_text, today)

    if dry_run:
        report.status = "dry-run"
        return
    path.write_text(new_text, encoding="utf-8")


# ---------------------------------------------------------------------------
# action wrappers
# ---------------------------------------------------------------------------

def action_start(vault: Path, *, feature: str, task_id: str, allow_multi_active: bool, dry_run: bool, report: Report) -> None:
    report.action = "start"
    _write_transition(
        vault,
        feature=feature,
        task_id=task_id,
        target_marker=MARKER_IN_PROGRESS,
        note=None,
        allow_multi_active=allow_multi_active,
        dry_run=dry_run,
        report=report,
    )


def action_complete(vault: Path, *, feature: str, task_id: str, dry_run: bool, report: Report) -> None:
    report.action = "complete"
    _write_transition(
        vault,
        feature=feature,
        task_id=task_id,
        target_marker=MARKER_COMPLETED,
        note=None,
        allow_multi_active=True,
        dry_run=dry_run,
        report=report,
    )


def action_block(vault: Path, *, feature: str, task_id: str, note: str, dry_run: bool, report: Report) -> None:
    report.action = "block"
    _write_transition(
        vault,
        feature=feature,
        task_id=task_id,
        target_marker=MARKER_BLOCKED,
        note=note,
        allow_multi_active=True,
        dry_run=dry_run,
        report=report,
    )


def action_reopen(vault: Path, *, feature: str, task_id: str, dry_run: bool, report: Report) -> None:
    report.action = "reopen"
    _write_transition(
        vault,
        feature=feature,
        task_id=task_id,
        target_marker=MARKER_QUEUED,
        note=None,
        allow_multi_active=True,
        dry_run=dry_run,
        report=report,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SDLC Kit task-marker manager (Kiro convention).")
    p.add_argument("--vault-root", required=True, help="absolute path to the `.sdlc/` vault")
    p.add_argument(
        "--action",
        required=True,
        choices=["list", "start", "complete", "block", "reopen"],
        help="list | start (queued→in_progress) | complete (→completed) | block (→needs_attention) | reopen (→queued)",
    )
    p.add_argument("--feature", required=True, help="feature slug — the folder under 04-specs/")
    p.add_argument("--id", dest="task_id", help="task id (TASK-NNN) — required for start/complete/block/reopen")
    p.add_argument("--note", help="blocker reason — required for `block`")
    p.add_argument(
        "--allow-multi-active",
        action="store_true",
        help="bypass the single-[-]-at-a-time invariant (use sparingly)",
    )
    p.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    report = Report()
    vault = resolve_vault(args.vault_root, report)
    report.vault_root = str(vault)

    if args.action != "list" and not args.task_id:
        die(report, "--id is required for start/complete/block/reopen", code=1)

    try:
        if args.action == "list":
            action_list(vault, feature=args.feature, report=report)
        elif args.action == "start":
            action_start(
                vault,
                feature=args.feature,
                task_id=args.task_id,
                allow_multi_active=args.allow_multi_active,
                dry_run=args.dry_run,
                report=report,
            )
        elif args.action == "complete":
            action_complete(
                vault,
                feature=args.feature,
                task_id=args.task_id,
                dry_run=args.dry_run,
                report=report,
            )
        elif args.action == "block":
            action_block(
                vault,
                feature=args.feature,
                task_id=args.task_id,
                note=args.note or "",
                dry_run=args.dry_run,
                report=report,
            )
        elif args.action == "reopen":
            action_reopen(
                vault,
                feature=args.feature,
                task_id=args.task_id,
                dry_run=args.dry_run,
                report=report,
            )
    except PermissionError as exc:
        die(report, f"permission denied: {exc}", code=2)
    except OSError as exc:
        die(report, f"filesystem error: {exc}", code=2)

    if report.status == "ok" and args.dry_run:
        report.status = "dry-run"
    print(json.dumps(report.as_dict(), ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
