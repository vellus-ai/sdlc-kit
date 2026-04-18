---
id: ADR-0003
title: Test strategy — TDD + PBT + coverage ≥ 90%
status: accepted
date: 2026-04-18
author: Milton Silva Jr.
tags: [testing, quality, tdd, pbt, coverage]
supersedes: []
---

# ADR-0003 — Test strategy: TDD + PBT + coverage ≥ 90%

## Status

Accepted.

## Context

The SDLC Kit plugin is a developer tool. Its users — other developers — are unforgiving about regressions: a broken `/sdlc-kit:sync` silently corrupting `_INDEX.md`, a scaffolder overwriting a handcrafted ADR, or an idempotence bug flipping a `status` on a no-op transition would erode trust fast. The cost of a bug reaching users is disproportionately high compared to the cost of writing a test up front.

Early in the project we had no explicit test contract. Tests appeared ad hoc, some skills had zero coverage, and bugs found in review were repeatedly the same shapes:

1. **Regressions on idempotence** — transitions that wrote even when target == current.
2. **Collision handling** — scaffolders that overwrote existing files without `--force`.
3. **Slug validation** — regex edits that silently broadened or narrowed the accepted set.
4. **MOC non-determinism** — regenerators that produced different whitespace on successive runs.

These are all properties, not examples. Enumerating them test-by-test is tedious and incomplete; stating them as invariants is precise.

A second pressure: the scripts are subprocess-based, so traditional unit-test mocking does not apply cleanly. We need to run the real interpreter and assert on the JSON contract. That is slow if done naively — fast feedback requires discipline about what to run when.

## Decision

We adopt a three-part test strategy and enforce it in CI:

### 1. TDD is the default

Every PR that adds production code is expected to follow red → green → refactor. Reviewers check that:

- The test came in the same PR as the code.
- Test commits precede or accompany implementation commits (not appear after).
- The test asserts behavior, not implementation details.

A PR without tests is not merged unless the change is itself a test-only change or a pure documentation update.

### 2. Property-based testing (PBT) with Hypothesis where invariants exist

We reach for [Hypothesis](https://hypothesis.readthedocs.io/) when the rule is algebraic:

- **Idempotence:** `transition(transition(x, s), s) == transition(x, s)` for every status `s`.
- **Round-trip:** any string produced by the slug generator must parse back through the validator.
- **Determinism:** `regenerate(v)` twice produces byte-identical output.
- **Robustness:** any input with a valid YAML fence does not raise.

PBT tests are tagged `@pytest.mark.pbt` so they can be filtered in CI and run as their own stage.

### 3. Branch coverage ≥ 90% on any package a PR touches

CI measures branch coverage (`--cov-branch`) on `core/`, `skills/`, and `hooks/`. The gate is **per-package, per-PR**: any package whose files changed in the PR must show branch coverage ≥ 90% on the final commit. This replaces a flat project-wide floor, which encouraged improving uncovered legacy code to meet a number rather than ensuring new code is thoroughly tested.

Test tiers:

- **Fast tier** (`pytest -m "not slow"`) — runs on every push. No model loads, no network. Must finish in under 30 s on a developer laptop.
- **Slow tier** (`pytest -m slow`) — runs nightly and on-demand. Covers ML model loads and long integration cases.
- **PBT tier** (`pytest -m pbt`) — runs on every push. Hypothesis examples are deterministic via a seeded database committed to `.hypothesis/` (which is gitignored; CI regenerates).

## Consequences

### Positive

- **Regressions on idempotence and collision handling disappear.** Properties catch entire classes of bugs the first time.
- **Refactors are cheap.** Behavior-focused tests survive implementation changes; the test suite is an asset, not a tax.
- **Reviewers have a consistent bar.** "90% branch coverage on touched packages" is objective. "Are tests good?" is not.
- **New contributors learn the conventions quickly.** Every skill has a `test_<skill>_skill.py` following the same anatomy, so newcomers copy a template rather than invent one.

### Negative

- **Writing properties is harder than writing examples.** Contributors must learn Hypothesis strategies. We mitigate this by documenting idiomatic strategies in `docs/TESTING.md` and by pair-programming the first PBT on each new skill.
- **Coverage targets can nudge toward shallow tests.** We counter this with the "behavior over implementation" guideline and by rejecting tests that only exercise happy paths to hit a number.
- **PBT can be flaky if strategies are under-constrained.** We mitigate by committing seeds for known failures and by preferring `st.from_regex` over broad `st.text` when the input space is known.

### Neutral

- Some packages (e.g., `core/migrations/`) are excluded from coverage because they are effectively SQL DDL wrapped in a Python loader. Exclusions are listed explicitly in `pyproject.toml` under `[tool.coverage.run].omit` and reviewed quarterly.

## Implementation plan

- [x] Add `hypothesis` to `[project.optional-dependencies].dev` in `pyproject.toml`.
- [x] Register the `slow` and `pbt` markers in `[tool.pytest.ini_options]`.
- [x] Create `tests/_skill_helpers.py` with `make_vault`, `run_script`, `parse_json`, `read_frontmatter`.
- [x] Write `docs/TESTING.md` with anatomy, helpers, and PBT examples.
- [ ] Add a CI job that fails when branch coverage on any touched package drops below 90%.
- [ ] Port the first PBT to `test_adr_skill.py` (slug round-trip) and `test_spec_skill.py` (idempotent transitions).

## References

- [[CONTRIBUTING]]
- [[TESTING]]
- [[ADR-0001-estrutura-canonica]]
- [[ADR-0002-skills-inventory]]
- [Hypothesis documentation](https://hypothesis.readthedocs.io/)
