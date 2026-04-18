---
name: sdlc-doc
description: |
  Use as the **fallback** document scaffolder when the user wants to create a
  markdown artifact from a per-phase template under
  `assets/vault-tree/<phase>/_templates/` and no dedicated skill exists for
  that template. Typical triggers are `/sdlc-kit:doc`, "create a doc from
  template", "scaffold a runbook", "new tech memo", "ad-hoc document from
  template", or in pt-BR: "criar documento a partir de template", "gerar
  documento customizado", "novo documento genérico a partir de template",
  "scaffoldar um runbook". Accepts `--template <file.md>`, `--phase <NN>`,
  `--title "<title>"`, slugifies the title, and writes
  `<vault>/<phase_folder>/<slug>.md`. Substitutes `{{TITLE}}`, `{{DATE}}`,
  `{{FEATURE_NAME}}`, `{{INITIATIVE_NAME}}` placeholders. **Always prefer a
  dedicated skill when one exists** — dedicated skills interview the user,
  enforce sub-folders (e.g. `02-architecture/trd/<slug>.md`,
  `03-domain/aggregates/<slug>.md`), link back to MOCs, and run sync. This
  skill is the generic fallback for templates that don't have one
  (runbooks, tech memos, release checklists, experiment logs — anything
  ad-hoc). Do not invoke for templates that have a dedicated skill; route to
  that skill instead.
---

# sdlc-kit:doc

Generic fallback: scaffolds a new markdown document from any template under
`assets/vault-tree/<phase>/_templates/` when **no dedicated skill** covers
that template.

Single lens: **Technical Writer / Author**. The author picks the template,
drafts the title, and fills in the body — the skill only runs the
deterministic file op (resolve template → slugify → write once).

---

## Prefer a dedicated skill when one exists

Most vault templates already have a dedicated skill that does more than this
one: it runs an interview, enforces the correct sub-folder, sets the right
frontmatter (`type`, `status: draft`, links, owner), cross-links MOCs, and
invokes `/sdlc-kit:sync`. **Route to the dedicated skill first.**

| Template                                       | Dedicated skill              | Why prefer it                                                          |
|------------------------------------------------|------------------------------|------------------------------------------------------------------------|
| `00-steering/_templates/product.md.tpl`        | `/sdlc-kit:steer`            | Singleton handling, brand voice, stakeholders interview                |
| `00-steering/_templates/standards.md.tpl`      | `/sdlc-kit:steer`            | Singleton handling, organisational policy cross-links                  |
| `00-steering/_templates/tech.md.tpl`           | `/sdlc-kit:steer`            | Singleton handling, tech-radar cross-links                             |
| `01-planning/_templates/prd.md.tpl`            | `/sdlc-kit:prd`              | PRD interview, metrics/OKRs, user-story triage                         |
| `01-planning/_templates/epic.md.tpl`           | `/sdlc-kit:epic`             | Epic decomposition, milestone/PRD links, status lifecycle              |
| `01-planning/_templates/milestone.md.tpl`      | `/sdlc-kit:milestone`        | Milestone scope, acceptance signals                                    |
| `02-architecture/_templates/adr.md.tpl`        | `/sdlc-kit:adr`              | ADR numbering, decision interview, Architect + AppSec duo              |
| `02-architecture/_templates/trd.md.tpl`        | `/sdlc-kit:trd`              | 10-bucket NFR interview, Architect + AppSec + SRE triad                |
| `02-architecture/_templates/c4-*.md.tpl`       | `/sdlc-kit:c4`               | C4 kind selection (context/container/component), mermaid skeleton      |
| `02-architecture/_templates/api/*.md.tpl`      | `/sdlc-kit:api`              | API flavour selection (rest/grpc/async/webhook), contract cross-links  |
| `03-domain/_templates/aggregate.md.tpl`        | `/sdlc-kit:domain`           | DDD kind routing, aggregates/ sub-folder, event cross-link             |
| `03-domain/_templates/domain-event.md.tpl`     | `/sdlc-kit:domain`           | Event payload interview, emitting aggregate link                       |
| `03-domain/_templates/contract.md.tpl`         | `/sdlc-kit:domain`           | ACL/OHS/Conformist/PL pattern selection                                |
| `03-domain/_templates/context-map.md.tpl`      | `/sdlc-kit:domain`           | Singleton, bounded-context enumeration                                 |
| `03-domain/_templates/ubiquitous-language.md.tpl` | `/sdlc-kit:domain`        | Singleton, glossary discipline                                         |
| `04-specs/_templates/requirements.md.tpl`      | `/sdlc-kit:spec`             | Spec triplet (requirements/design/tasks), NFR inheritance from TRD     |
| `04-specs/_templates/design.md.tpl`            | `/sdlc-kit:spec`             | Part of the spec triplet                                               |
| `04-specs/_templates/tasks.md.tpl`             | `/sdlc-kit:spec` / `:task`   | Task breakdown rules                                                   |
| `05-development/_templates/branch.md.tpl`      | `/sdlc-kit:worktree`         | Branch/worktree coupling, git wiring                                   |
| `05-development/_templates/worktree.md.tpl`    | `/sdlc-kit:worktree`         | Branch/worktree coupling, git wiring                                   |
| `06-design-system/_templates/component.md.tpl` | `/sdlc-kit:design-system`    | Design-token cross-links, variant matrix                               |
| `06-design-system/_templates/pattern.md.tpl`   | `/sdlc-kit:design-system`    | Pattern library discipline                                             |
| `06-design-system/_templates/token.md.tpl`     | `/sdlc-kit:design-system`    | Token taxonomy                                                         |
| `07-retrospectives/_templates/incident.md.tpl` | `/sdlc-kit:incident`         | Incident timeline interview, blast radius, lessons                     |
| `07-retrospectives/_templates/incident-lessons.md.tpl` | `/sdlc-kit:incident` | Follow-up lessons record                                               |
| `07-retrospectives/_templates/retro.md.tpl`    | `/sdlc-kit:retro`            | Retro facilitation, action-item tracking                               |
| `07-retrospectives/_templates/review.md.tpl`   | `/sdlc-kit:review`           | PR review duo (Senior Engineer + AppSec), decision + status lifecycles |

If the user's request maps to a row above, **do not invoke `/sdlc-kit:doc`** —
route to the dedicated skill instead. Only fall through to this skill for
templates that genuinely have no dedicated route.

---

## When to invoke

Invoke when:

- The user types `/sdlc-kit:doc --template <file> --phase <NN> --title "<t>"`
  for a template **without** a dedicated skill.
- The user says "scaffold a runbook", "new tech memo", "ad-hoc document from
  template", "create a release checklist", "create a doc from template", or
  in pt-BR: "criar um documento genérico a partir de template", "gerar
  runbook", "novo memo técnico".
- A team introduces a new `.md.tpl` under `<phase>/_templates/` that doesn't
  (yet) have its own skill, and wants to start consuming it immediately as a
  fallback.

---

## When NOT to invoke

- The user's request maps to one of the dedicated skills listed above →
  route to that skill. Example: `/sdlc-kit:doc --template adr.md --phase 02`
  must become `/sdlc-kit:adr`.
- The template doesn't exist under `assets/vault-tree/<phase>/_templates/` →
  the script exits `1`. Don't invent templates; confirm with the user and
  either reuse an existing template or add a new `.md.tpl` first.
- The user wants to **overwrite** an existing file — the script refuses, and
  correctly so. Pick a different title/slug or edit the existing file.
- cwd is not inside a vault (no `.sdlc-kit/marker.json`) → tell the user to
  run `/sdlc-kit:init` first.

---

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort otherwise
   (exit `2`).
2. **Phase known.** The script accepts only `01`–`07`. If the user asks for
   phase `00` (steering), route to `/sdlc-kit:steer` — see the *Known
   limitations* section.
3. **Template exists** at
   `<plugin_root>/assets/vault-tree/<phase_folder>/_templates/<template>`.
4. **Destination does not exist.** The destination is
   `<vault>/<phase_folder>/<slug>.md`, where `<slug>` is derived from
   `--title` (lowercase, non-word chars stripped, spaces/underscores
   collapsed to `-`).
5. **Dedicated-skill gate.** If the requested template has a dedicated skill,
   pause and propose the switch before running the script.

---

## Flow

1. **Confirm the template has no dedicated skill** (use the table above). If
   it does, stop and propose the dedicated skill instead.
2. **Gather args.** Need `--template`, `--phase`, `--title`. Offer a `--dry-run`
   first to preview template source, destination path, and whether the
   destination already exists.
3. **Scaffold:**
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-doc/scripts/doc.py" \
     --template <file.md> \
     --phase <NN> \
     --title "<Human title>" \
     [--vault-root "<path>"] \
     [--dry-run]
   ```
4. **Fill the body.** Open the created file and walk the template with the
   user via Edit, mirroring their active chat language. The script only
   substitutes `{{TITLE}}`, `{{DATE}}`, `{{FEATURE_NAME}}`,
   `{{INITIATIVE_NAME}}` — every other section still needs the author's
   input.
5. **Frontmatter.** Confirm the template's frontmatter is complete and the
   document is in `draft`. If the template is light on frontmatter, add at
   minimum: `title`, `type`, `status: draft`, `created`, `updated`, `tags`.
6. **Run `/sdlc-kit:sync`** manually after finishing — the script does **not**
   trigger sync itself. This is the most common mistake with this fallback
   skill; the MOC/_INDEX won't know about the new file until sync runs.

---

## Output contract

All runs emit a single JSON object on stdout.

```json
// --action scaffold (implicit — the script has only one action)
{
  "status": "ok",
  "file": "/abs/path/to/.sdlc/04-testing/checkout-test-plan.md"
}

// --dry-run
{
  "status": "dry-run",
  "template": "/abs/path/plugin/assets/vault-tree/04-testing/_templates/test-plan.md",
  "destination": "/abs/path/to/.sdlc/04-testing/checkout-test-plan.md",
  "exists": false
}

// destination already exists (before any write)
{
  "status": "error",
  "message": "file already exists: /abs/path/to/.sdlc/04-testing/checkout-test-plan.md"
}

// unknown phase (not in 01..07)
{
  "status": "error",
  "message": "unknown phase: 00"
}

// template file missing
{
  "status": "error",
  "message": "template not found: /abs/path/plugin/assets/vault-tree/04-testing/_templates/made-up.md"
}

// vault not resolved
{
  "status": "error",
  "message": "vault not found"
}

// cwd is inside a directory without a marker
{
  "status": "error",
  "message": "not a valid vault: /abs/path"
}
```

**Exit codes:**

- `0` — `ok` or `dry-run`.
- `1` — user error (unknown phase, missing template, destination already
  exists).
- `2` — fatal (vault not resolved, marker missing, filesystem failure).

---

## Guardrails

**Never:**

- Use this skill to scaffold a template that has a dedicated skill — always
  route to the dedicated skill first (see the table). Dedicated skills do
  more than file-write: they interview, cross-link, and sync.
- Overwrite an existing file. The script already refuses; don't add `--force`
  from inside the skill. If the user really wants to replace a file, have
  them delete or rename it explicitly first.
- Assume the template is fully filled by the script — only four placeholders
  are substituted (`{{TITLE}}`, `{{DATE}}`, `{{FEATURE_NAME}}`,
  `{{INITIATIVE_NAME}}`). Every other section is the author's job.
- Write the file into an arbitrary sub-folder. The script writes flat at
  `<phase_folder>/<slug>.md`. If the target template belongs in a sub-folder
  (e.g. `aggregates/`, `trd/`, `api/`, `reviews/`), the dedicated skill is
  the correct tool — this skill will land it in the wrong location.
- Invent a template name. The `--template` arg must match an existing file
  under `assets/vault-tree/<phase>/_templates/`.
- Forget to run `/sdlc-kit:sync` afterwards — the MOC and `_INDEX` need to
  know about the new file.

**Always:**

- Mirror the user's active chat language when filling the body; keep the
  frontmatter scaffolding in English.
- Run `--dry-run` first when there's any uncertainty about where the file
  will land or whether the destination collides.
- Surface the generated path in the final report so the user can open it.
- After the body is filled, remind the user to run `/sdlc-kit:sync`.

---

## Examples

> Examples below are in English. In a real session, mirror the user's active
> conversation language in every user-facing line.

**Runbook (no dedicated skill — genuine fallback use):**

```
User: scaffold a runbook for the payments service
AI:   "No dedicated skill for runbooks — /sdlc-kit:doc is the right tool.
       Which phase? Suggest 04 (testing) or 07 (retrospectives/ops)."
User: 04, title "Payments service runbook"
AI:   [doc.py --dry-run → destination=.sdlc/04-testing/payments-service-runbook.md, exists=false]
AI:   [doc.py → status=ok, file=.sdlc/04-testing/payments-service-runbook.md]
AI:   "Created. Let's walk the template — on-call contacts, alert paths,
       rollback steps… [Edit]"
AI:   (after body is filled) "Don't forget /sdlc-kit:sync so the MOC picks it up."
```

**Routing to a dedicated skill (refuse the generic path):**

```
User: /sdlc-kit:doc --template adr.md --phase 02 --title "Adopt gRPC between internal services"
AI:   "ADRs have a dedicated skill that does more than a file scaffold —
       ADR numbering, Architect + AppSec interview, MOC cross-links, sync.
       Switching to /sdlc-kit:adr."
AI:   [/sdlc-kit:adr new "Adopt gRPC between internal services"]
```

**Destination collision:**

```
User: /sdlc-kit:doc --template test-plan.md --phase 04 --title "Checkout test plan"
AI:   [doc.py → status=error, exit=1, "file already exists: .sdlc/04-testing/checkout-test-plan.md"]
AI:   "There's already a `checkout-test-plan.md` in 04-testing. Options:
       (a) open and edit the existing one, (b) pick a more specific title
       like 'Checkout test plan — 2026 Q2 regression'."
```

---

## Known limitations (future work — not fixed by this skill)

These are properties of the current `scripts/doc.py` that diverge from the
canonical SKILL pattern. They are intentionally **documented, not fixed** —
any change belongs in a follow-up PR against the script itself.

- **Phase `00` (steering) is not supported.** The script's `_PHASE_FOLDERS`
  map only covers `01`–`07`, so templates under
  `00-steering/_templates/` cannot be reached via `/sdlc-kit:doc`. Users
  should use `/sdlc-kit:steer` for those templates anyway.
- **Flat destination only.** The script writes
  `<vault>/<phase_folder>/<slug>.md` — it does not honour sub-folders like
  `02-architecture/trd/`, `03-domain/aggregates/`, `03-domain/events/`,
  `02-architecture/api/`, `07-retrospectives/reviews/`. Dedicated skills
  enforce those sub-folders; this fallback does not.
- **No sync invocation.** The script does not call `/sdlc-kit:sync`; the
  user (or the invoking LLM) must run it manually after scaffolding.
- **No `type`/`status` injection.** Only `{{TITLE}}`, `{{DATE}}`,
  `{{FEATURE_NAME}}`, `{{INITIATIVE_NAME}}` are substituted. Any other
  required frontmatter is the template's responsibility (or the author's).
- **No `list` action.** There is no way to enumerate previously-created
  generic docs from this skill alone; use `/sdlc-kit:status` or browse the
  phase folder directly.
