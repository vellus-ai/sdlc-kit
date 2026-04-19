# sdlc-kit:c4 — full flow

## Kinds, paths and templates

| Kind        | Type slug | Cardinality           | Path                                      | Template                         |
|-------------|-----------|-----------------------|-------------------------------------------|----------------------------------|
| `context`   | `c4-context`   | Singleton        | `02-architecture/c4/context.md`           | `_templates/c4-context.md.tpl`   |
| `container` | `c4-container` | Singleton        | `02-architecture/c4/container.md`         | `_templates/c4-container.md.tpl` |
| `component` | `c4-component` | Collection       | `02-architecture/c4/components/<slug>.md` | `_templates/c4-component.md.tpl` |

Component slug = container name the diagram zooms into (e.g., `api`, `web-app`, `worker`).

## Flow

### 1. Pre-flight
- Read the vault's `CLAUDE.md` — may contain project-specific tech stack guidance for the Container diagram.
- Run `list` first. **Never scaffold over an existing file without `--force`**.

### 2. Scaffold
Run `scripts/c4.py --action scaffold` with:
- `--kind {context|container|component}`
- `--slug <container>` (required for `component`, forbidden for singletons)
- `--title "<human title>"` (required for `component`; optional for singletons)
- `--owner <handle>` (optional)

The script validates slug, refuses to overwrite without `--force`, substitutes
`{{TITLE}}`, `{{SLUG}}`, `{{OWNER}}`, `{{DATE}}`, `{{PROJECT_NAME}}`.

### 3. Interview

| Level       | Must-fill sections |
|-------------|--------------------|
| `context`   | Actors (personas, external systems), trust boundaries, primary use-case flows |
| `container` | Every container (purpose, tech, data store, runtime), inter-container relationships |
| `component` | Every major component inside the container, responsibility, boundaries |

Each kind ships a starter Mermaid block in C4-DSL syntax. Every `<External System>`
/ `<Container>` / `<Component>` placeholder must become concrete or be explicitly dropped.

### 4. Cross-link
- `container` wikilinks every ADR explaining a tech choice: `[[ADR-0007-postgres-for-billing]]`.
- Each `component` wikilinks the `[[container]]` singleton.
- If a container maps to a bounded context, wikilink `[[context-map]]` and relevant `[[<aggregate>]]`.

### 5. Decide
```
scripts/c4.py --action transition --kind <kind> [--slug <slug>] --to approved
```
Use `--to deprecated` when reality diverged and a replacement diagram exists; cite successor in the body.

## Pre-approval checklist

Block `--to approved` unless **all** apply:

- [ ] Mermaid block has no `<Placeholder>` tokens.
- [ ] Every external system / container / component has a 1-line purpose.
- [ ] Diagram matches **this-week reality**, not aspiration.
- [ ] Every non-trivial tech choice is backed by an `accepted` ADR, cited via wikilink.
- [ ] For `container`: every container has an owner (team or service account).
- [ ] For `component`: the parent container is itself at least `approved`.
- [ ] Both lenses (Architect + Senior Engineer) reviewed.

## Output contract

- `list`: `diagrams[]` (`kind`, `slug`, `path`, `title`, `status`, `owner`, `updated`), `count`.
- `scaffold`: `kind`, `slug`, `diagram_path`, `was_new`.
- `transition`: `kind`, `slug`, `diagram_path`, `previous_status`, `new_status`.

Exit codes: `0` ok/dry-run, `1` user error, `2` fatal.

## Guardrails

**Never:**
- Scaffold a singleton with `--slug` — the script refuses.
- Approve a diagram with template placeholders.
- Let the `container` diagram and actual `docker-compose.yml` / K8s manifests disagree.
- Create a `component` diagram for a container that doesn't exist in the `container` view.
- Delete a diagram; always `deprecated` with a pointer to the successor.

**Always:**
- Cite ADRs for non-obvious tech choices.
- Keep each diagram strictly at its level — Container shouldn't contain Component detail.
- Mirror user's chat language in narrative; keep frontmatter, ADR refs, Mermaid DSL in English.

## Examples

### Bootstrap C4 for a brand-new service

```
scripts/c4.py --action scaffold --kind context
scripts/c4.py --action scaffold --kind container
scripts/c4.py --action scaffold --kind component --slug api --title "API"
scripts/c4.py --action scaffold --kind component --slug worker --title "Worker"
```
Walk through each Mermaid block and promote to `approved` when signed off.

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
Edit body: `Superseded by [[worker]] after the 2026-Q2 cron migration.`

### Smell: approving a placeholder diagram

If the `container` Mermaid still says `Container(api, "API", "Go/chi", "Handles business logic")`
(template default) without confirming the stack, refuse. Ask for each container's real tech.
