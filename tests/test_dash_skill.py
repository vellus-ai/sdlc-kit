"""Tests for sdlc-dash — opens the vault's ``dashboard.html`` in the OS
default browser.

The script branches on ``platform.system()``; on Windows it calls
``os.startfile``, on Darwin it shells out to ``open`` and on Linux to
``xdg-open``. Because the script is invoked in a subprocess we cannot
monkeypatch in-process, so for the happy path we inject a tiny
``sitecustomize.py`` that neutralises the shell-out behaviour regardless
of the host platform. This keeps the test hermetic and prevents an
actual browser window from being launched on the developer's machine.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from tests._skill_helpers import SKILLS_DIR, make_vault, parse_json, run_script


SCRIPT = "sdlc-dash/scripts/dash.py"
SCRIPT_PATH = SKILLS_DIR / SCRIPT


def _write_dashboard(vault: Path, body: str = "<html></html>") -> Path:
    dash = vault / "dashboard.html"
    dash.write_text(body, encoding="utf-8")
    return dash


def _run_with_shim(vault: Path, tmp_path: Path, *extra_args: str,
                   shim_body: str | None = None) -> subprocess.CompletedProcess:
    """Invoke the dash script with a ``sitecustomize.py`` on PYTHONPATH
    that neutralises OS open-file helpers so the test never actually
    launches a browser window.
    """
    shim_dir = tmp_path / "_shim"
    shim_dir.mkdir(exist_ok=True)
    default_shim = (
        "import os, subprocess\n"
        # No-op replacements — record the call as an env file so the test
        # can inspect it if needed.
        "os.startfile = lambda p, *a, **kw: None\n"
        "subprocess.run = lambda *a, **kw: None\n"
    )
    (shim_dir / "sitecustomize.py").write_text(
        shim_body if shim_body is not None else default_shim,
        encoding="utf-8",
    )
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        str(shim_dir) + (os.pathsep + existing if existing else "")
    )
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--vault-root", str(vault), *extra_args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


class TestDashSkill:
    # ------------------------------------------------------------------
    # Happy path — marker + dashboard.html present, OS call neutralised
    # ------------------------------------------------------------------
    def test_success_with_mocked_os_open(self, tmp_path):
        vault = make_vault(tmp_path)
        dash = _write_dashboard(vault)
        cp = _run_with_shim(vault, tmp_path)
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["status"] == "ok"
        # The path in the response is resolved to absolute.
        assert Path(data["path"]) == dash.resolve()
        # With the neutralised shim the call succeeded without raising,
        # so ``opened`` must be True.
        assert data["opened"] is True

    def test_success_when_os_open_raises(self, tmp_path):
        """If the OS helper raises, the script's except block must flip
        ``opened`` to False while still exiting 0 with status=ok."""
        vault = make_vault(tmp_path)
        _write_dashboard(vault)
        shim = (
            "import os, subprocess\n"
            "def _boom(*a, **kw):\n"
            "    raise RuntimeError('no display available')\n"
            "os.startfile = _boom\n"
            "subprocess.run = _boom\n"
        )
        cp = _run_with_shim(vault, tmp_path, shim_body=shim)
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["status"] == "ok"
        assert data["opened"] is False

    # ------------------------------------------------------------------
    # dashboard.html missing — marker present but file absent → exit 1
    # ------------------------------------------------------------------
    def test_exits_1_when_dashboard_missing(self, tmp_path):
        vault = make_vault(tmp_path)
        cp = run_script(SCRIPT, ["--vault-root", str(vault)])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert data["status"] == "error"
        assert "dashboard.html not found" in data["message"]

    # ------------------------------------------------------------------
    # --dry-run — never calls the OS, just echoes the resolved path
    # ------------------------------------------------------------------
    def test_dry_run_returns_path_without_opening(self, tmp_path):
        vault = make_vault(tmp_path)
        dash = _write_dashboard(vault)
        cp = run_script(SCRIPT, ["--vault-root", str(vault), "--dry-run"])
        assert cp.returncode == 0, cp.stderr
        data = parse_json(cp)
        assert data["status"] == "dry-run"
        assert Path(data["path"]) == dash.resolve()
        # dry-run response does not carry the "opened" key.
        assert "opened" not in data

    def test_dry_run_still_errors_when_dashboard_missing(self, tmp_path):
        # dry-run short-circuits AFTER the dashboard existence check —
        # so a missing dashboard must still exit 1 even with --dry-run.
        vault = make_vault(tmp_path)
        cp = run_script(SCRIPT, ["--vault-root", str(vault), "--dry-run"])
        assert cp.returncode == 1
        data = parse_json(cp)
        assert "dashboard.html not found" in data["message"]

    # ------------------------------------------------------------------
    # Vault missing — marker absent → exit 2
    # ------------------------------------------------------------------
    def test_exits_2_when_vault_root_has_no_marker(self, tmp_path):
        not_a_vault = tmp_path / "elsewhere"
        not_a_vault.mkdir()
        cp = run_script(SCRIPT, ["--vault-root", str(not_a_vault)])
        assert cp.returncode == 2
        data = parse_json(cp)
        assert data["status"] == "error"
        assert "not a valid vault" in data["message"]
