# Testing Guide

> 📖 **Também disponível em [Português (Brasil)](#guia-de-testes--português-brasil) abaixo.**

This document explains how the SDLC Kit plugin is tested and how to write tests for new code.

## Philosophy

- **Behavior over implementation.** A test asserts what the user observes, not which private function was called. If you can refactor freely without changing any test, the tests are doing their job.
- **TDD is the default.** Red → green → refactor, every time. A commit that adds production code without an accompanying test is a smell.
- **Property-based where invariants exist.** Enumerating examples is fine for a handful of cases; when the rule is algebraic (idempotence, round-trip, monotonicity), write a property.
- **Fast by default.** The default `pytest` run skips model loads (`-m "not slow"` in CI-fast mode). Expensive tests are explicit.
- **Scripts are tested as subprocesses.** Skill scripts expose a JSON contract on stdout — we test them by running the real interpreter, not by importing internals. This catches argparse regressions, import cycles, and I/O bugs.

## The `tests/_skill_helpers.py` helper

This module is the single entry point for skill-script tests. It is not a pytest module (the filename does not start with `test_`), so pytest does not collect it. Import it from individual test files.

Key helpers:

- `make_vault(tmp_path, *phases)` — builds a minimal vault at `tmp_path`, writes `.sdlc-kit/marker.json`, and copies the requested phase folders (including their `_templates/`) from the real `assets/vault-tree/`. This guarantees the test and the scaffolded vault stay in lockstep.
- `run_script(script_rel, args)` — runs `skills/<script_rel>` as a subprocess with the current `sys.executable`. Returns a `subprocess.CompletedProcess` with captured stdout/stderr.
- `parse_json(cp)` — parses the last JSON object on stdout. Tolerates a trailing newline split.
- `read_frontmatter(path)` — independent frontmatter parser; use it in assertions so the test does not depend on the SUT's own regex.

Example usage:

```python
from pathlib import Path
from tests._skill_helpers import make_vault, run_script, parse_json, read_frontmatter


def test_adr_scaffold_creates_numbered_file(tmp_path: Path):
    vault = make_vault(tmp_path, "02-architecture")

    cp = run_script(
        "sdlc-adr/scripts/adr.py",
        ["--vault-root", str(vault), "--action", "new",
         "--title", "Adopt gRPC", "--slug", "adopt-grpc"],
    )

    assert cp.returncode == 0
    result = parse_json(cp)
    assert result["status"] == "ok"
    assert result["adr_id"] == "ADR-0001"

    created = vault / result["adr_path"]
    assert created.exists()
    fm = read_frontmatter(created)
    assert fm["status"] == "proposed"
```

## Anatomy of a `test_<skill>_skill.py`

Each skill test file typically covers:

1. **Happy path — list.** Empty vault returns `count: 0` with an empty list.
2. **Happy path — scaffold/new.** Creates the expected file at the expected path; frontmatter carries the right defaults.
3. **Idempotence.** Re-running a transition with the current status writes nothing (`previous_status == new_status`).
4. **Collision handling.** Scaffolding over an existing file refuses without `--force` and returns exit code 1.
5. **Invalid input.** Bad slug/status/id exits 1 with a structured error in the JSON.
6. **Dry-run.** When supported, `--dry-run` prints the plan without mutating the filesystem.

Keep each test focused — one assertion family per function. Use `pytest.fixture` for shared setup, never global state.

## Property-based tests with Hypothesis

Property-based tests (PBT) cover rules that are awkward to enumerate. Mark them with `@pytest.mark.pbt` so they can be filtered in CI.

Good candidates in this codebase:

- **Slug validator round-trip.** For every string accepted by the slug regex, the generated filename round-trips through the parser.
- **Idempotent transitions.** `transition(transition(x, s), s) == transition(x, s)` for every status `s` in the lifecycle.
- **MOC regeneration is deterministic.** Running the regenerator twice on the same vault produces byte-identical output.
- **Frontmatter parser survives fuzzing.** Any input with a valid YAML fence does not raise.

Example:

```python
import pytest
from hypothesis import given, strategies as st

from core.regexes import SLUG_RE


@pytest.mark.pbt
@given(st.from_regex(SLUG_RE, fullmatch=True))
def test_valid_slug_passes_validator(slug: str):
    from skills.sdlc_adr.scripts.adr import is_valid_slug
    assert is_valid_slug(slug)
```

## Measuring coverage

We target **≥ 90% branch coverage on any package touched by a PR**. The project-wide floor is informational; the gate is per-package.

Run locally:

```bash
# Terminal report with missing lines
pytest --cov=core --cov=skills --cov=hooks --cov-branch --cov-report=term-missing

# HTML report
pytest --cov=core --cov=skills --cov=hooks --cov-report=html
# open htmlcov/index.html in your browser
```

Filter fast vs slow tests:

```bash
pytest -m "not slow"      # fast path — no ML model loads
pytest -m slow            # only the slow ones
pytest -m pbt             # only property-based tests
```

Run a single file or test:

```bash
pytest tests/test_adr_skill.py
pytest tests/test_adr_skill.py::test_adr_scaffold_creates_numbered_file
```

## Common pitfalls

- **Don't import `skills/**/scripts/*.py` directly.** Those are executable entry points, not a library. Run them as subprocesses via `run_script`.
- **Don't assert on log messages.** Logs go to stderr and are not part of the contract. Assert on the JSON payload on stdout.
- **Don't hand-maintain template copies.** `make_vault` copies from the real `assets/vault-tree/` — if the template changes, the test picks it up for free.
- **Don't leave `.hypothesis/` databases in commits.** That directory is in `.gitignore`; if it shows up in `git status`, something is off.
- **Platform line endings.** On Windows, `text=True` with UTF-8 encoding handles CRLF conversions. When asserting on file content, prefer `path.read_text(encoding="utf-8")` over comparing raw bytes.

## CI expectations

Every PR must satisfy:

- `pytest` passes on `-m "not slow"`
- `pytest -m slow` passes (nightly or on-demand)
- `pytest -m pbt` passes
- Coverage ≥ 90% on any package touched
- `ruff check .` clean
- `mypy core plugins tests` clean

---
---

## Guia de Testes — Português (Brasil)

> A versão canônica é a **inglesa acima**. Esta seção resume o essencial em português.

### Filosofia

- **Comportamento sobre implementação.** Um teste afirma o que o usuário observa, não qual função privada foi chamada.
- **TDD é o default.** Red → green → refactor, sempre.
- **Property-based onde houver invariantes.** Enumerar exemplos serve para poucos casos; quando a regra é algébrica (idempotência, round-trip, monotonicidade), escreva uma property.
- **Rápido por padrão.** A execução default do `pytest` pula testes lentos (`-m "not slow"` no CI-fast).
- **Scripts são testados como subprocessos.** Skills expõem contrato JSON em stdout — testamos rodando o interpretador real, não importando internals.

### Helper `tests/_skill_helpers.py`

- `make_vault(tmp_path, *phases)` — constrói um vault mínimo em `tmp_path`, escreve `.sdlc-kit/marker.json`, copia as fases pedidas (com `_templates/`) do `plugins/core/assets/vault-tree/`.
- `run_script(script_rel, args)` — roda um script de skill como subprocess; resolve automaticamente entre `plugins/core/skills/` e `plugins/extended/skills/`.

### Antes de mergear

- `pytest` passa
- `pytest -m slow` passa (nightly ou on-demand)
- `pytest -m pbt` passa
- Cobertura ≥ 90% em qualquer pacote tocado
- `ruff check .` limpo
- `mypy core plugins tests` limpo
