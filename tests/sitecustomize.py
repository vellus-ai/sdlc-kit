"""Auto-loaded shim that starts `coverage.process_startup()` in subprocesses.

Python imports `sitecustomize` automatically at interpreter startup when the
module is on `sys.path`. Our test harness injects `tests/` into `PYTHONPATH`
for every subprocess call, so this file runs once in each subprocess and
bootstraps line-level coverage IF the parent test run requested it via the
`COVERAGE_PROCESS_START` environment variable.

Outside of test runs, the shim is a no-op: no env var → no-op.

This is the canonical recipe documented by coverage.py:
https://coverage.readthedocs.io/en/latest/subprocess.html
"""
from __future__ import annotations

import os


def _maybe_start_coverage() -> None:
    if not os.environ.get("COVERAGE_PROCESS_START"):
        return
    try:
        import coverage  # type: ignore[import-not-found]
    except ImportError:
        return
    coverage.process_startup()


_maybe_start_coverage()
