# sdlc-kit:domain — full flow

## Kinds, paths and templates

| Kind                  | Type slug | Cardinality           | Path                                | Template                                |
|-----------------------|-----------|-----------------------|-------------------------------------|-----------------------------------------|
| `aggregate`           | `domain-aggregate`           | Collection | `03-domain/aggregates/<slug>.md`    | `_templates/aggregate.md.tpl`           |
| `event`               | `domain-event`               | Collection | `03-domain/events/<slug>.md`        | `_templates/domain-event.md.tpl`        |
| `contract`            | `domain-contract`            | Collection | `03-domain/contracts/<slug>.md`     | `_templates/contract.md.tpl`            |
| `context-map`         | `domain-context-map`         | Singleton  | `03-domain/context-map.md`          | `_templates/context-map.md.tpl`         |
| `ubiquitous-language` | `domain-ubiquitous-language` | Singleton  | `03-domain/ubiquitous-language.md`  | `_templates/ubiquitous-language.md.tpl` |

## Flow

### 1. Pre-flight
- Read the vault's `CLAUDE.md` — domain vocabulary is project-specific.
- Run `list` first. **Never scaffold over an existing file without `--force`**.

### 2. Scaffold
Run `scripts/domain.py --action scaffold` with:
- `--kind {aggregate|event|contract|context-map|ubiquitous-language}`
- `--title "<human title>"` (required for collections)
- `--slug <slug>` (required for collections, forbidden for singletons)
- `--owner <handle>` (optional)

The script validates slug, refuses to overwrite without `--force`, substitutes
template placeholders.

### 3. Interview

| Kind                  | Must-fill sections |
|-----------------------|--------------------|
| `aggregate`           | Root, invariants, commands, emitted events, consistency policy |
| `event`               | When-emitted, payload schema, consumers, ordering/delivery, schema evolution |
| `contract`            | Upstream + downstream contexts, pattern (ACL/OHS/Conformist/PL), translation rules |
| `context-map`         | Each bounded context (name, responsibility, owner), relationships, strategic classification |
| `ubiquitous-language` | Glossary (term → definition → banned synonyms), domain rules, references |

Every missing field is filled or explicitly marked `— N/A —` with a 1-line justification.

### 4. Cross-link
- Aggregates ↔ events: `[[aggregate-slug]]` in event's *emitting aggregate* row, `[[event-slug]]` in aggregate's *emitted events*.
- Contracts wikilink both contexts in the context map.
- Ubiquitous language is referenced from every aggregate/event introducing a new term.

### 5. Decide
```
scripts/domain.py --action transition --kind <kind> [--slug <slug>] --to approved
```
Use `--to deprecated` when replaced; cite successor in body.

## Pre-approval checklist

Block `--to approved` unless **all** apply:

- [ ] Every section filled or explicitly `— N/A —` with justification.
- [ ] For `aggregate`: ≥ 1 invariant (INV-*) and ≥ 1 command documented; every emitted event scaffolded and linked.
- [ ] For `event`: payload schema precise, consumers table non-empty, ordering/delivery explicit.
- [ ] For `contract`: pattern is one of the classic strategic DDD options; translation rules written out.
- [ ] For `context-map`: every bounded context has owner + strategic classification (Core / Supporting / Generic).
- [ ] For `ubiquitous-language`: no term defined twice; every domain rule uses only glossary vocabulary.
- [ ] Both lenses (Domain Modeler + Senior Engineer) reviewed.

## Output contract

- `list`: `artifacts[]` (`kind`, `slug`, `path`, `title`, `status`, `owner`, `updated`), `count`.
- `scaffold`: `kind`, `slug`, `artifact_path`, `was_new`.
- `transition`: `kind`, `slug`, `artifact_path`, `previous_status`, `new_status`.

Exit codes: `0` ok/dry-run, `1` user error, `2` fatal.

## Guardrails

**Never:**
- Scaffold a singleton with `--slug`.
- Approve an aggregate that emits an event without a matching `event` file.
- Delete or rename a domain file — breaks wikilinks. Use `deprecated` instead.
- Promote without both lenses signing off.
- Mix multiple bounded contexts into one aggregate; suggest splitting.

**Always:**
- Keep `updated` honest — `transition` refreshes it.
- Cross-link new events into emitting aggregate and context-map.
- Mirror user's chat language in body; keep frontmatter and template scaffolding in English.

## Examples

### Bootstrap a brand-new domain

```
scripts/domain.py --action scaffold --kind context-map
scripts/domain.py --action scaffold --kind ubiquitous-language
scripts/domain.py --action scaffold --kind aggregate --slug order --title "Order"
scripts/domain.py --action scaffold --kind event --slug order-placed --title "OrderPlaced"
```
Interview through each template, cross-link, then transition to `approved`.

### List by kind

```
scripts/domain.py --action list --kind event
```

### Retire an obsolete contract

```
scripts/domain.py --action transition --kind contract --slug billing-to-invoicing --to deprecated
```
Edit body: `Superseded by [[billing-to-finance-acl]]`.

### Smell: approving a bare aggregate

If an `aggregate`'s *Invariants* or *Commands* sections still contain
`<placeholder>` text, refuse. Approval is permission for other artifacts to depend on this one.
