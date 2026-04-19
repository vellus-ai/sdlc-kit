---
name: sdlc-domain
description: |
  Use when the user asks to model the domain, define a bounded context, add an
  aggregate/domain event/context contract, or curate the ubiquitous language —
  or when they invoke `/sdlc-kit:domain`. Mirror triggers such as "modelar o
  domínio", "criar agregado", "novo evento de domínio", "atualizar context
  map", "atualizar linguagem ubíqua", "modelar bounded context". Operates
  under `03-domain/` with five kinds: `aggregate`, `event`, `contract`
  (collections — one file per slug) and `context-map`, `ubiquitous-language`
  (singletons — one file per vault). Lifecycle for every kind is `draft →
  approved → deprecated`. The skill scaffolds the file and records the status
  change; the **Domain Modeler** and **Senior Software Engineer** drive the
  content interview together (Event Storming, aggregate invariants, ACL
  patterns), and the LLM mirrors the user's chat language when filling the
  template.
---

# sdlc-kit:domain

Captures the **Domain-Driven Design artifacts** for a project under
`03-domain/`. The skill is co-authored by two lenses working in tandem:

- **Domain Modeler / Product-side lens** — owns the business vocabulary,
  aggregates, invariants and events. Source of truth for "what the domain
  means" independent of any technology.
- **Senior Software Engineer lens** — owns the context map, anti-corruption
  layer decisions, integration contracts and persistence concerns. Source of
  truth for "how the domain meets the code".

Every scaffolded file lands in `draft`. It only becomes `approved` after both
lenses review the content; `deprecated` preserves history without authority.

## Kinds, paths and templates

| Kind                  | Type slug (frontmatter)          | Cardinality           | Path                                         | Template                               |
|-----------------------|----------------------------------|-----------------------|----------------------------------------------|----------------------------------------|
| `aggregate`           | `domain-aggregate`               | Collection (per slug) | `03-domain/aggregates/<slug>.md`             | `_templates/aggregate.md.tpl`          |
| `event`               | `domain-event`                   | Collection (per slug) | `03-domain/events/<slug>.md`                 | `_templates/domain-event.md.tpl`       |
| `contract`            | `domain-contract`                | Collection (per slug) | `03-domain/contracts/<slug>.md`              | `_templates/contract.md.tpl`           |
| `context-map`         | `domain-context-map`             | **Singleton**         | `03-domain/context-map.md`                   | `_templates/context-map.md.tpl`        |
| `ubiquitous-language` | `domain-ubiquitous-language`     | **Singleton**         | `03-domain/ubiquitous-language.md`           | `_templates/ubiquitous-language.md.tpl`|

Singletons ignore `--slug`; collections require it.

## When to invoke

- User says *"map the domain"*, *"bootstrap DDD for this project"*, *"desenhar
  os bounded contexts"* → scaffold `context-map` + `ubiquitous-language`
  first, then start modelling aggregates.
- User names a concept and asks it to become canonical → scaffold an
  `aggregate` (or the relevant kind) and walk the template with them.
- User adds a new fact the system must emit → scaffold an `event`, link it
  back to the emitting aggregate.
- User introduces an integration between two contexts → scaffold a `contract`
  and describe the pattern (ACL, OHS, Conformist, etc.).
- A record is ready for the team to rely on → `transition --to approved`.
- A concept is retired → `transition --to deprecated` (never delete; rename
  is destructive for backlinks).

## When **not** to invoke

- Purely technical containers/diagrams → that's `/sdlc-kit:c4`.
- API contract schemas → that's `/sdlc-kit:api`.
- Cross-cutting quality requirements → that's `/sdlc-kit:trd`.

## Flow

### 1. Pre-flight
- Read the target vault's `CLAUDE.md` if it exists — domain vocabulary is
  project-specific and the file may override the template's suggestions.
- Run `list` first to see what already exists. **Never scaffold on top of an
  existing file without `--force`**; the script will refuse.

### 2. Scaffold
Run `scripts/domain.py --action scaffold` with:
- `--kind {aggregate|event|contract|context-map|ubiquitous-language}`
- `--title "<human title>"` (required for collections; optional for singletons,
  which use `{{PROJECT_NAME}}`)
- `--slug <slug>` (**required for collections, forbidden for singletons**)
- `--owner <handle>` (optional; falls back to marker.json owner)

The script:
- validates the slug against `[a-z0-9][a-z0-9-]*`
- refuses to overwrite unless `--force` is passed
- substitutes `{{TITLE}}`, `{{SLUG}}`, `{{OWNER}}`, `{{DATE}}`,
  `{{PROJECT_NAME}}` in the template
- emits a JSON report with the final path

### 3. Interview
Walk the user through the template sections. Fill them via Edit/Write using
the user's chat language. Per-kind priorities:

| Kind                  | Must-fill sections                                                                         |
|-----------------------|---------------------------------------------------------------------------------------------|
| `aggregate`           | Root, invariants, commands, emitted events, consistency policy                              |
| `event`               | When-it-is-emitted, payload schema, consumers, ordering/delivery, schema evolution          |
| `contract`            | Upstream & downstream contexts, pattern (ACL/OHS/Conformist/PL), translation rules          |
| `context-map`         | Each bounded context (name, responsibility, owner), relationships, strategic classification |
| `ubiquitous-language` | Glossary (term → definition → banned synonyms), domain rules, references                    |

Every missing field must either be filled or explicitly marked `— N/A —` with
a 1-line justification.

### 4. Cross-link
- Aggregates and events must wikilink each other: `[[aggregate-slug]]` in the
  event's *emitting aggregate* row, `[[event-slug]]` in the aggregate's
  *emitted events* list.
- Contracts must wikilink both contexts' entries in the context map.
- The ubiquitous language should be referenced from every aggregate/event
  introducing a new term.

### 5. Decide
Once the content is complete and the two lenses agree:
```
scripts/domain.py --action transition --kind <kind> [--slug <slug>] --to approved
```
Use `--to deprecated` when the concept is replaced by another record; cite
the successor in the deprecated note's body.

## Pre-approval checklist

Block `--to approved` unless **all** apply:

- [ ] Every section in the template is filled or explicitly marked `— N/A —`
      with justification.
- [ ] For `aggregate`: at least one invariant (INV-*) and one command are
      documented, and every emitted event is scaffolded and linked.
- [ ] For `event`: payload schema is precise, consumers table is non-empty,
      ordering/delivery explicit.
- [ ] For `contract`: pattern is one of the classic strategic DDD options and
      translation rules are written out.
- [ ] For `context-map`: every bounded context has an owner and a strategic
      classification (Core / Supporting / Generic).
- [ ] For `ubiquitous-language`: no term is defined twice; every domain rule
      uses only vocabulary from the glossary.
- [ ] Both lenses (Domain Modeler + Senior Engineer) have reviewed the note.

## Output contract

All actions emit a single JSON object on stdout. Common fields: `status`,
`action`, `vault_root`, `errors`.

- `list`: `artifacts[]` (`kind`, `slug`, `path`, `title`, `status`, `owner`,
  `updated`), `count`.
- `scaffold`: `kind`, `slug`, `artifact_path`, `was_new`.
- `transition`: `kind`, `slug`, `artifact_path`, `previous_status`,
  `new_status` (equal on idempotent re-runs).

Exit codes: `0` ok/dry-run, `1` user error (invalid kind/slug/status, missing
required arg), `2` fatal (template missing, filesystem failure).

## Guardrails

**Never:**
- Scaffold a singleton with `--slug` — the script refuses and so must the
  skill.
- Approve an aggregate that emits an event without a matching `event` file.
- Delete or rename a domain file; renaming breaks wikilinks in every other
  artifact referencing it. Use `deprecated` instead and scaffold a new record
  if the identity really must change.
- Promote a record to `approved` without both lenses signing off.
- Mix multiple bounded contexts into a single aggregate — if the interview
  reveals multiple contexts, suggest splitting before scaffolding.

**Always:**
- Keep the `updated` field honest — the `transition` action refreshes it
  automatically.
- Cross-link new events into their emitting aggregate and the context-map.
- Mirror the user's chat language in the body content; keep frontmatter and
  template scaffolding in English.

## Examples

### Bootstrap a brand-new domain

```
scripts/domain.py --action scaffold --kind context-map
scripts/domain.py --action scaffold --kind ubiquitous-language
scripts/domain.py --action scaffold --kind aggregate --slug order --title "Order"
scripts/domain.py --action scaffold --kind event --slug order-placed --title "OrderPlaced"
```
Then interview the user through each template, cross-link, and only then
transition them to `approved`.

### List everything of a given kind

```
scripts/domain.py --action list --kind event
```

### Retire an obsolete contract

```
scripts/domain.py --action transition --kind contract --slug billing-to-invoicing --to deprecated
```
Edit the body to point at the replacement contract: `Superseded by
[[billing-to-finance-acl]]`.

### Smell: approving a bare aggregate

If the user asks to approve an `aggregate` whose *Invariants* or *Commands*
sections still contain `<placeholder>` text, refuse. List the missing
sections and ask to fill them first. Approval is permission for other
artifacts to depend on this one — the content must be real.
