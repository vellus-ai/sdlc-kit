"""Shared helpers for skill-script tests.

Not a pytest module (name does not start with `test_`), so pytest will not
collect it. Imported by the per-skill test files.

Each helper:
- builds a minimal vault rooted at `tmp_path`
- writes the `.sdlc-kit/marker.json` marker
- copies the phase folders + templates from the real `assets/vault-tree/`
  tree so tests never hand-maintain duplicate template copies

Scripts are invoked via `subprocess.run` with the current `sys.executable`,
matching the plugin's stdlib-only policy (no pytest plugins required).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGINS_ROOT = REPO_ROOT / "plugins"
CORE_PLUGIN = PLUGINS_ROOT / "core"
EXTENDED_PLUGIN = PLUGINS_ROOT / "extended"
# Both plugins expose `skills/`. Helpers below resolve a script path by
# searching both, so tests passing `"sdlc-prd/scripts/prd.py"` keep working
# without knowing which plugin owns the skill.
SKILLS_DIRS = (CORE_PLUGIN / "skills", EXTENDED_PLUGIN / "skills")
# Templates and dashboard live with the core plugin (extended doesn't ship them).
VAULT_TREE = CORE_PLUGIN / "assets" / "vault-tree"
TESTS_DIR = Path(__file__).resolve().parent


def _subprocess_env() -> dict[str, str]:
    """Environment for subprocess calls that propagates coverage-of-subprocess.

    Adds `tests/` to PYTHONPATH so `tests/sitecustomize.py` is auto-loaded in
    the child interpreter. When `COVERAGE_PROCESS_START` is set in the parent
    (done automatically by pytest-cov), `coverage.process_startup()` fires in
    the child and writes a `.coverage.<pid>` data file that `coverage combine`
    stitches into the parent report.

    Also forces PYTHONIOENCODING=utf-8 so Unicode characters in script output
    (e.g. arrows `→`, dashes `—`, em-spaces) round-trip correctly on Windows,
    where the default stdout codec is cp1252.
    """
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    parts = [str(TESTS_DIR)]
    if existing:
        parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _write_marker(vault: Path, *, owner: str = "team-alpha", project_name: str = "Acme") -> None:
    kit = vault / ".sdlc-kit"
    kit.mkdir(parents=True, exist_ok=True)
    (kit / "marker.json").write_text(
        json.dumps({"version": "0.1.0", "owner": owner, "project_name": project_name}),
        encoding="utf-8",
    )


def _copy_phase(vault: Path, phase: str) -> None:
    """Copy a whole phase folder (including `_templates/`) from the canonical
    vault-tree into the test vault. Safe to call multiple times — uses
    `dirs_exist_ok=True`.
    """
    src = VAULT_TREE / phase
    dst = vault / phase
    if src.exists():
        shutil.copytree(src, dst, dirs_exist_ok=True)


def make_vault(tmp_path: Path, *phases: str, owner: str = "team-alpha",
               project_name: str = "Acme") -> Path:
    """Build a minimal vault containing the requested `phases`.

    Example:
        vault = make_vault(tmp_path, "03-domain")
    """
    _write_marker(tmp_path, owner=owner, project_name=project_name)
    for phase in phases:
        _copy_phase(tmp_path, phase)
    return tmp_path


def _resolve_script(script_rel: str) -> Path:
    """Find a skill script in either plugin (core or extended)."""
    for skills_dir in SKILLS_DIRS:
        candidate = skills_dir / script_rel
        if candidate.exists():
            return candidate
    raise AssertionError(
        f"skill script missing: {script_rel} (searched {SKILLS_DIRS})"
    )


def run_script(script_rel: str, args: list[str]) -> subprocess.CompletedProcess:
    """Invoke a skill script (auto-resolves between core/extended plugins).

    `script_rel` is relative to either `plugins/core/skills/` or
    `plugins/extended/skills/`, e.g. `"sdlc-domain/scripts/domain.py"`.
    """
    script = _resolve_script(script_rel)
    return subprocess.run(
        [sys.executable, str(script)] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_subprocess_env(),
    )


def parse_json(cp: subprocess.CompletedProcess) -> dict:
    """Parse the last JSON object printed on stdout.

    Helpful because argparse may print error lines on stderr, but the script
    contract is a single JSON object on stdout for the happy or user-error
    paths. For argparse exit-2 errors there is no stdout JSON — callers that
    expect argparse rejection must not call this.
    """
    stdout = cp.stdout.strip()
    assert stdout, f"empty stdout; stderr={cp.stderr!r}"
    # The contract is one JSON object on stdout; still handle a pathological
    # trailing newline split.
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        # Fallback: take the last non-empty line.
        last = [line for line in stdout.splitlines() if line.strip()][-1]
        return json.loads(last)


def read_frontmatter(path: Path) -> dict:
    """Minimal frontmatter parser — mirrors the script-side parser but is
    independent so assertions don't depend on the SUT's own regex.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    # Close-fence detection: first `---` line after the opening, on its own.
    lines = text.splitlines()
    assert lines[0].rstrip() == "---", "expected opening frontmatter fence"
    out: dict[str, str] = {}
    for line in lines[1:]:
        if line.rstrip() == "---":
            break
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"') and len(value) >= 2:
            value = value[1:-1]
        out[key] = value
    return out
