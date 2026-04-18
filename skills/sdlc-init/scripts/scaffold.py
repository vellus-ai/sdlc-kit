#!/usr/bin/env python3
"""Scaffold SDLC vault directory tree from assets/vault-tree/.

Idempotent by default: never overwrites existing files unless --force.
Always emits a JSON report on stdout. Exit codes: 0 ok, 1 user error, 2 fatal.

Placeholders replaced in every .tpl file (renamed dropping the .tpl suffix):
    {{PROJECT_NAME}} {{OWNER}} {{STACK}} {{STACK_DETAILS}} {{REPO_URL}}
    {{DATE}} {{SYNC_TS}} {{TITLE}} {{SLUG}}

Example:
    python scaffold.py --vault-root /repo/.sdlc \\
        --project-name "Meu App" --owner "Milton" --stack "Go + Next.js" \\
        --repo-url "https://github.com/me/repo"
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

_ASSETS = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "vault-tree"
_MARKER_DIR = ".sdlc-kit"
_MARKER_FILE = "marker.json"
_KIT_VERSION = "0.1.0"


@dataclass
class Report:
    status: str = "ok"
    vault_root: str = ""
    files_created: list[str] = field(default_factory=list)
    files_skipped: list[str] = field(default_factory=list)
    files_updated: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "vault_root": self.vault_root,
            "files_created": sorted(self.files_created),
            "files_skipped": sorted(self.files_skipped),
            "files_updated": sorted(self.files_updated),
            "errors": self.errors,
            "summary": {
                "created": len(self.files_created),
                "skipped": len(self.files_skipped),
                "updated": len(self.files_updated),
            },
        }


def die(report: Report, message: str, exit_code: int = 2) -> None:
    report.status = "error"
    report.errors.append(message)
    print(json.dumps(report.as_dict(), ensure_ascii=False))
    sys.exit(exit_code)


def verify_git_repo(vault_root: Path, report: Report) -> Path:
    """Ensure vault-root lives inside a git repository. Returns repo toplevel."""
    try:
        result = subprocess.run(
            ["git", "-C", str(vault_root.parent), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        die(report, "git command not found in PATH", exit_code=1)
    if result.returncode != 0:
        die(
            report,
            f"not a git repository (parent: {vault_root.parent}): {result.stderr.strip()}",
            exit_code=1,
        )
    return Path(result.stdout.strip()).resolve()


def verify_assets_exist(report: Report) -> None:
    if not _ASSETS.exists():
        die(report, f"vault-tree assets not found at {_ASSETS}", exit_code=2)
    if not (_ASSETS / "dashboard.html").exists():
        die(report, "dashboard.html missing from assets/vault-tree/", exit_code=2)


def verify_not_system_path(vault_root: Path, report: Report) -> None:
    """Refuse to scaffold inside system-sensitive locations."""
    home = Path.home().resolve()
    resolved = vault_root.resolve()
    sensitive = {home, home.parent, Path("/"), Path("C:/"), Path("C:/Users")}
    if resolved in sensitive or resolved == home:
        die(report, f"refusing to scaffold vault at sensitive path: {resolved}", exit_code=1)
    # Must be at least 2 levels below HOME
    try:
        rel = resolved.relative_to(home)
        if len(rel.parts) < 2:
            die(
                report,
                f"vault path too close to home ({resolved}); nest at least 2 levels deep",
                exit_code=1,
            )
    except ValueError:
        # Not under home — OK (external drives, /workspace, etc.)
        pass


def apply_placeholders(text: str, replacements: dict[str, str]) -> str:
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)
    return text


def scaffold_file(
    src: Path,
    dest: Path,
    replacements: dict[str, str],
    *,
    dry_run: bool,
    force: bool,
    report: Report,
    rel_label: str,
) -> None:
    """Copy src → dest with placeholder substitution. Respects idempotency."""
    exists = dest.exists()
    if exists and not force:
        report.files_skipped.append(rel_label)
        return

    if dry_run:
        if exists:
            report.files_updated.append(rel_label)
        else:
            report.files_created.append(rel_label)
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    content = src.read_text(encoding="utf-8")
    if src.suffix == ".tpl" or ".md" in src.suffixes:
        content = apply_placeholders(content, replacements)
    dest.write_text(content, encoding="utf-8")
    if exists:
        report.files_updated.append(rel_label)
    else:
        report.files_created.append(rel_label)


def scaffold_binary(
    src: Path, dest: Path, *, dry_run: bool, force: bool, report: Report, rel_label: str
) -> None:
    """Binary/opaque copy (no placeholder substitution)."""
    exists = dest.exists()
    if exists and not force:
        report.files_skipped.append(rel_label)
        return
    if dry_run:
        if exists:
            report.files_updated.append(rel_label)
        else:
            report.files_created.append(rel_label)
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    if exists:
        report.files_updated.append(rel_label)
    else:
        report.files_created.append(rel_label)


_TEXT_SUFFIXES = {".md", ".tpl", ".txt", ".json", ".yml", ".yaml"}


def _is_in_templates_dir(rel: Path) -> bool:
    """Paths under any `_templates/` subdir are verbatim assets for skill consumption."""
    return "_templates" in rel.parts


def walk_assets(
    vault_root: Path, replacements: dict[str, str], *, dry_run: bool, force: bool, report: Report
) -> None:
    for src in _ASSETS.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(_ASSETS)
        in_templates = _is_in_templates_dir(rel)

        # Files under _templates/ keep their .tpl suffix and skip placeholder substitution.
        # They're consumed later by skills (prd, epic, adr...) when materializing artifacts.
        if in_templates:
            dest = vault_root / rel
            rel_label = str(rel).replace("\\", "/")
            scaffold_binary(
                src, dest,
                dry_run=dry_run, force=force, report=report, rel_label=rel_label,
            )
            continue

        # Outside _templates/: strip .tpl suffix and apply placeholders.
        dest_parts = list(rel.parts[:-1])
        dest_name = rel.name[:-4] if rel.name.endswith(".tpl") else rel.name
        dest_parts.append(dest_name)
        dest = vault_root.joinpath(*dest_parts)
        rel_label = "/".join(dest_parts)

        if dest_name == ".gitkeep":
            if dest.exists():
                report.files_skipped.append(rel_label)
                continue
            if dry_run:
                report.files_created.append(rel_label)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text("", encoding="utf-8")
            report.files_created.append(rel_label)
            continue

        if src.suffix.lower() in _TEXT_SUFFIXES or src.name.endswith(".tpl"):
            scaffold_file(
                src, dest, replacements,
                dry_run=dry_run, force=force, report=report, rel_label=rel_label,
            )
        else:
            scaffold_binary(
                src, dest,
                dry_run=dry_run, force=force, report=report, rel_label=rel_label,
            )


def write_marker(vault_root: Path, args: argparse.Namespace, *, dry_run: bool, report: Report) -> None:
    marker_dir = vault_root / _MARKER_DIR
    marker = marker_dir / _MARKER_FILE
    rel_label = f"{_MARKER_DIR}/{_MARKER_FILE}"
    if marker.exists():
        report.files_skipped.append(rel_label)
        return
    if dry_run:
        report.files_created.append(rel_label)
        return
    marker_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": _KIT_VERSION,
        "created": date.today().isoformat(),
        "project_name": args.project_name,
        "owner": args.owner,
        "stack": args.stack,
        "repo_url": args.repo_url,
    }
    marker.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    report.files_created.append(rel_label)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold SDLC Kit vault from canonical templates.",
    )
    parser.add_argument("--vault-root", required=True, help="destination .sdlc/ path")
    parser.add_argument("--project-name", default="Meu Projeto")
    parser.add_argument("--owner", default="")
    parser.add_argument("--stack", default="")
    parser.add_argument("--repo-url", default="")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would be created/skipped without writing anything",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing files (DESTRUCTIVE — require explicit user confirmation)",
    )
    parser.add_argument(
        "--skip-git-check",
        action="store_true",
        help="bypass git-repo verification (use in CI / testing only)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = Report()

    vault_root = Path(args.vault_root).resolve()
    report.vault_root = str(vault_root)

    verify_assets_exist(report)
    verify_not_system_path(vault_root, report)
    if not args.skip_git_check:
        verify_git_repo(vault_root, report)

    today = date.today().isoformat()
    project_name = args.project_name or "Meu Projeto"
    stack_details_default = (
        "_Stack ainda não definida. Rode `/sdlc-kit:steer tech` para registrar "
        "os princípios técnicos e `/sdlc-kit:adr new` para cada decisão de tecnologia._"
    )
    replacements = {
        "{{PROJECT_NAME}}": project_name,
        "{{OWNER}}": args.owner or "_a definir_",
        "{{STACK}}": args.stack or "_a definir — ver `00-steering/tech.md`_",
        "{{STACK_DETAILS}}": args.stack or stack_details_default,
        "{{REPO_URL}}": args.repo_url or "_sem remote configurado_",
        "{{DATE}}": today,
        "{{SYNC_TS}}": today,
        "{{TITLE}}": project_name,
        "{{SLUG}}": "",
    }

    try:
        walk_assets(
            vault_root, replacements,
            dry_run=args.dry_run, force=args.force, report=report,
        )
        write_marker(vault_root, args, dry_run=args.dry_run, report=report)
    except PermissionError as exc:
        die(report, f"permission denied: {exc}", exit_code=2)
    except OSError as exc:
        die(report, f"filesystem error: {exc}", exit_code=2)

    if args.dry_run:
        report.status = "dry-run"

    print(json.dumps(report.as_dict(), ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
