---
name: sdlc-c4
description: |
  Use when the user asks to document or update the system architecture using
  the C4 model (levels 1–3), draw a context/container/component diagram, or
  invokes `/sdlc-kit:c4`. Mirror triggers such as "draw the C4 context",
  "desenhar diagrama de containers", "atualizar C4", "documentar arquitetura",
  "bootstrap C4 for this project", "diagrama de componentes do serviço X".
  Operates under `02-architecture/c4/` with three kinds: `context` and
  `container` (singletons — one file per vault) and `component` (collection —
  one file per container). Lifecycle for every kind is `draft → approved →
  deprecated`. The skill scaffolds the file and records the status change;
  the **Software Architect** and **Senior Engineer** drive the Mermaid
  content together, and the LLM mirrors the user's chat language when
  filling narrative sections.
---

# sdlc-kit:c4

Captures the **C4 model architecture diagrams** for a project under
`02-architecture/c4/`. Simon Brown's C4 model is three nested levels of
detail — Context (who uses the system, what it touches), Container (how it
is split into deployable/runnable units), Component (what each container
contains). The skill is co-authored by two lenses:

- **Software Architect lens** — owns strategic decomposition, user journeys,
  trust boundaries, external system contracts. Source of truth for "how the
  system fits into the world".
- **Senior Engineer lens** — owns technology choices, runtime topology,
  deployment targets, component-level seams. Source of truth for "how the
  system fits together at runtime".

Every scaffolded file lands in `draft`. It only becomes `approved` after
both lenses review and the ADRs it cites are themselves `accepted`;
`deprecated` preserves history without authority.

## Kinds, paths and templates

| Kind        | Type slug (frontmatter) | Cardinality           | Path                                              | Template                                 |
|-------------|-------------------------|-----------------------|---------------------------------------------------|------------------------------------------|
| `context`   | `c4-context`            | **Singleton**         | `02-architecture/c4/context.md`                   | `_templates/c4-context.md.tpl`           |
| `container` | `c4-container`          | **Singleton**         | `02-architecture/c4/container.md`                 | `_templates/c4-container.md.tpl`         |
| `component` | `c4-component`          | Collection (per slug) | `02-architecture/c4/components/<slug>.md`         | `_templates/c4-component.md.tpl`         |

Singletons ignore `--slug`; collections require it. Component slug is the
**container name** the diagram zooms into (e.g., `api`, `web-app`,
`worker`). Writing `components/api.md` means "this is the component-level
view of the `api` container".

## When to invoke

- User says *"bootstrap the C4 for this service"*, *"desenhar a arquitetura"*,
  *"document the system"* → scaffold `context` + `container` first.
- User names a specific container and wants to zoom in → scaffold a
  `component` with the container's slug.
- A diagram is ready for the team to rely on → `transition --to approved`.
- Architecture changes (new container added, tech swap) → edit in place while
  still `draft`; if already `approved`, scaffold a replacement and transition
  the old one to `deprecated` with a link to the successor.

## When **not** to invoke

- DDD artifacts (aggregates, events, context map) → that's `/sdlc-kit:domain`.
- Cross-cutting quality requirements (SLOs, security baseline) → that's
  `/sdlc-kit:trd`.
- A single specific decision ("we picked Postgres over Mongo") → that's
  `/sdlc-kit:adr`. A C4 diagram references ADRs, it doesn't replace them.

## Flow

### 1. Pre-flight
- Read the target vault's `CLAUDE.md` — may contain project-specific tech
  stack guidance that should inform the Container diagram.
- Run `list` first. **Never scaffold over an existing file without `--force`**.

### 2. Scaffold
Run `scripts/c4.py --action scaffold` with:
- `--kind {context|container|component}`
- `--slug <container>` (**required for `component`, forbidden for `context` /
  `container`**)
- `--title "<human title>"` (required for `component`; optional for
  singletons, which use `{{PROJECT_NAME}}`)
- `--owner <handle>` (optional; falls back to marker.json owner)

The script:
- validates the slug against `[a-z0-9][a-z0-9-]*`
- refuses to overwrite unless `--force` is passed
- substitutes `{{TITLE}}`, `{{SLUG}}`, `{{OWNER}}`, `{{DATE}}`,
  `{{PROJECT_NAME}}` in the template
- emits a JSON report with the final path

### 3. Interview
Walk the user through the template. For each level, fill:

| Level       | Must-fill sections                                                                  |
|-------------|--------------------------------------------------------------------------------------|
| `context`   | Actors (personas, external systems), trust boundaries, primary use-case flows        |
| `container` | Every container (purpose, tech, data store, runtime), inter-container relationships |
| `component` | Every major component inside the container, their responsibility, their boundaries  |

Each kind's template ships a starter Mermaid block in the C4-DSL syntax the
user can render in Obsidian or copy into Structurizr/IcePanel. Replace the
placeholders — every `<External System>` / `<Container>` / `<Component>`
must become concrete or be explicitly dropped.

### 4. Cross-link
- The `container` diagram should wikilink every relevant ADR that explains a
  tech choice: `[[ADR-0007-postgres-for-billing]]`.
- Each `component` diagram should wikilink the container it zooms into:
  `[[container]]` (the singleton).
- If a container maps to a bounded context, wikilink `[[context-map]]` and
  the relevant `[[<aggregate>]]` notes.

### 5. Decide
Once the diagram is accurate and reviewed:
```
scripts/c4.py --action transition --kind <kind> [--slug <slug>] --to approved
```
Use `--to deprecated` when the reality diverged and a replacement diagram
exists; cite the successor in the deprecated file's body.

## Pre-approval checklist

Block `--to approved` unless **all** apply:

- [ ] The Mermaid block has no `<Placeholder>` tokens left.
- [ ] Every referenced external system / container / component has a 1-line
      purpose next to it.
- [ ] The diagram matches reality (what the code actually does **this
      week**), not an aspirational plan.
- [ ] Every non-trivial tech choice in the diagram is backed by an `accepted`
      ADR, cited via wikilink.
- [ ] For `container`: every container has an owner (team or service account).
- [ ] For `component`: the parent container is itself at least `approved`.
- [ ] Both lenses (Architect + Senior Engineer) have reviewed the diagram.

## Output contract

All actions emit a single JSON object on stdout. Common fields: `status`,
`action`, `vault_root`, `errors`.

- `list`: `diagrams[]` (`kind`, `slug`, `path`, `title`, `status`, `owner`,
  `updated`), `count`.
- `scaffold`: `kind`, `slug`, `diagram_path`, `was_new`.
- `transition`: `kind`, `slug`, `diagram_path`, `previous_status`,
  `new_status` (equal on idempotent re-runs).

Exit codes: `0` ok/dry-run, `1` user error (invalid kind/slug/status,
missing required arg), `2` fatal (template missing, filesystem failure).

## Guardrails

**Never:**
- Scaffold a singleton with `--slug` — the script refuses and so must the
  skill.
- Approve a diagram that still contains template placeholders.
- Let the `container` diagram and the actual `docker-compose.yml` /
  Kubernetes manifests disagree — if they do, the diagram is wrong.
- Create a `component` diagram for a container that doesn't exist in the
  `container` view — the parent must be declared first.
- Delete a diagram; always `deprecated` with a pointer to the successor.

**Always:**
- Cite ADRs for non-obvious tech choices (e.g., *why* Redis over Memcached).
- Keep the diagram strictly at its level. The Container diagram should not
  contain component-level details; the Component diagram should not jump
  across containers.
- Mirror the user's chat language in narrative sections; keep frontmatter,
  ADR references and the Mermaid DSL in English.

## Examples

### Bootstrap C4 for a brand-new service

```
scripts/c4.py --action scaffold --kind context
scripts/c4.py --action scaffold --kind container
scripts/c4.py --action scaffold --kind component --slug api --title "API"
scripts/c4.py --action scaffold --kind component --slug worker --title "Worker"
```
Then walk the user through each Mermaid block and promote to `approved` when
the team signs off.

### List all diagrams

```
scripts/c4.py --action list
```

### Filter by level

```
scripts/c4.py --action list --kind component
```

### Deprecate an obsolete component diagram

```
scripts/c4.py --action transition --kind component --slug legacy-cron --to deprecated
```
Edit the body to point at the replacement: `Superseded by [[worker]] after
the 2026-Q2 cron migration.`

### Smell: approving a placeholder diagram

If the user asks to approve a `container` diagram whose Mermaid block still
says `Container(api, "API", "Go/chi", "Handles business logic")` (the
template default) without having confirmed the stack, refuse. Ask them to
confirm each container's real tech and re-run approval.
