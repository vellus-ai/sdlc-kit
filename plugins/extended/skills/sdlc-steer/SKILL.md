---
name: sdlc-steer
description: |
  Use when the user wants to define or update the project's steering
  documents — product vision, technical principles, or team standards.
  English triggers: `/sdlc-kit:steer`, `/sdlc-kit:steer product`,
  `/sdlc-kit:steer tech`, `/sdlc-kit:steer standards`,
  "define the product vision", "register the stack",
  "set up team standards", "document our principles". pt-BR triggers:
  "definir a visão de produto", "registrar a stack técnica",
  "configurar os padrões do time", "documentar nossos princípios".
  Co-authored by a triad of personas — a **Product Lead** (owns
  `product.md` vision, KPIs, personas), a **Tech Lead** (owns `tech.md`
  stack, principles, platform shape), and an **Engineering Manager** (owns
  `standards.md` team conventions, review gates, definition of done).
  Manages the three canonical files in `00-steering/` (`product.md`,
  `tech.md`, `standards.md`). The script handles deterministic operations
  only — reporting status, scaffolding a doc from its template in
  `00-steering/_templates/`, and promoting `status: draft` to
  `status: active`. The LLM drives the content interview and
  section-by-section editing via Edit/Write, mirroring the user's chat
  language. NEVER touches `CLAUDE.md` (sovereign, user-owned). After
  edits, invokes `/sdlc-kit:sync` so MOCs and `_INDEX.md` reflect the new
  state. Do not invoke to discuss architecture decisions (`/sdlc-kit:adr`)
  or technical requirements (`/sdlc-kit:trd`).
---

# sdlc-kit:steer

Materializes and matures the three canonical steering documents under `00-steering/`.

---

## The three steering documents

| Doc | Purpose | Template |
|---|---|---|
| `product.md` | Product vision — problem, users, value prop, north-star metrics | `_templates/product.md.tpl` |
| `tech.md` | Technical principles, stack table, accepted trade-offs, founding ADRs | `_templates/tech.md.tpl` |
| `standards.md` | Team norms — commits, branches, PR flow, DoD, code style | `_templates/standards.md.tpl` |

Each starts at `status: draft`, gets promoted to `status: active` once the user confirms it reflects the project.

---

## When to invoke

Invoke when:

- The user types `/sdlc-kit:steer`, `/sdlc-kit:steer product`, `/sdlc-kit:steer tech`, `/sdlc-kit:steer standards`.
- The user says "register the stack", "define the product vision", "establish team standards", "document our principles" — or equivalent phrasing in any other language.
- `/sdlc-kit:init` just finished and the user wants to populate steering docs as suggested in the init report.

**Do not** invoke when:

- The user wants to record a specific decision → use `/sdlc-kit:adr`.
- The user wants technical requirements or NFRs → use `/sdlc-kit:trd`.
- cwd is not inside a vault.

---

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Templates exist** at `<vault>/00-steering/_templates/{product,tech,standards}.md.tpl`. If any are missing (legacy vault), suggest `/sdlc-kit:init` repair.

---

## Flow

### Zero-arg: `/sdlc-kit:steer`

1. Run `steer.py --action status`. Parse the JSON `docs` array.
2. Show the user a one-line summary per doc: `product.md — missing | tech.md — draft | standards.md — active`.
3. Suggest next action based on `next_suggested`:
   - first missing → "Want to start with `/sdlc-kit:steer <name>`?"
   - else first draft → "Want to review and promote `<name>.md`?"
   - none pending → "All three steering docs are active. Nothing to do."

### With arg: `/sdlc-kit:steer {product|tech|standards}`

1. **Status check** first — does the target exist?
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-steer/scripts/steer.py" \
     --vault-root "<vault>" --action status
   ```
2. **Branch A — doc missing:** scaffold it.
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-steer/scripts/steer.py" \
     --vault-root "<vault>" --action scaffold --doc <name>
   ```
   Then begin the interview (see below).
3. **Branch B — doc exists (draft or active):** read the file, ask the user what sections to update. Offer: `[r] review and refine  [s] show diff before edits  [p] promote to active (if already complete)  [x] cancel`.

### The interview (LLM-driven, section by section)

Walk the template's sections in order. For each:

1. Show the user the section name and any placeholder text from the template.
2. Ask a focused question in the user's active conversation language.
3. When the user answers, edit the section in place via the Edit tool.
4. Move to the next section.

Do not rewrite the entire file at once — that risks clobbering manual edits and ignores the careful template structure. Edit section-by-section.

Keep the interview short:
- For `product.md`: problem → target users → value proposition → principles → north-star → non-goals (6 questions max).
- For `tech.md`: stack rows → principles → trade-offs → founding ADRs → quality rules (5 questions max).
- For `standards.md`: most of the template ships with good defaults — only ask about the project-specific rows (code style per language, review thresholds).

### Promotion

When the user says "this is good" / "ship it" / explicitly approves (in any language):

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-steer/scripts/steer.py" \
  --vault-root "<vault>" --action promote --doc <name>
```

This flips `status: draft` → `status: active` and refreshes `updated:`.

### Sync

After any scaffold, edit, or promotion, invoke `/sdlc-kit:sync` so `_INDEX.md` and `00-steering/_MOC.md` reflect the change.

---

## Output contract

```json
// --action status
{
  "status": "ok",
  "action": "status",
  "vault_root": "/abs/path/.sdlc",
  "docs": [
    {"name": "product",   "exists": true,  "path": "00-steering/product.md",   "status": "active", "updated": "2026-04-12", "title": "Product Vision — …"},
    {"name": "tech",      "exists": true,  "path": "00-steering/tech.md",      "status": "draft",  "updated": "2026-04-17", "title": "Technical Principles — …"},
    {"name": "standards", "exists": false, "path": "00-steering/standards.md", "status": "",       "updated": "",           "title": ""}
  ],
  "next_suggested": "standards",
  "errors": []
}

// --action scaffold
{
  "status": "ok",
  "action": "scaffold",
  "vault_root": "/abs/path/.sdlc",
  "doc": "tech",
  "doc_path": "00-steering/tech.md",
  "was_new": true,
  "errors": []
}

// --action promote
{
  "status": "ok",
  "action": "promote",
  "vault_root": "/abs/path/.sdlc",
  "doc": "tech",
  "doc_path": "00-steering/tech.md",
  "previous_status": "draft",
  "new_status": "active",
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error (missing arg, target exists, doc not found) · `2` fatal (permission denied, IO).

---

## Guardrails

**Never:**
- Touch `CLAUDE.md` — it is sovereign. Suggest user edit it manually if needed.
- Overwrite an existing steering doc without `--force` and explicit user confirmation.
- Rewrite the entire doc in one Edit call — section-by-section only.
- Auto-promote to `active` — always require explicit user approval.
- Fabricate content. If the user doesn't have an answer for a section, leave the template placeholder intact and offer to revisit later.

**Always:**
- Match the user's active conversation language.
- Run `--action status` before scaffold/promote so you know the current state.
- Invoke `/sdlc-kit:sync` after edits.
- Surface the generated file path in the final report so the user can open it.

---

## Examples

> Examples below are in English. In a real session, mirror the user's active conversation language in every user-facing line.

**Fresh vault, user starts with product vision:**
```
User: /sdlc-kit:steer product
AI:   [status] product.md — missing. Scaffolding from template…
AI:   [scaffold] created 00-steering/product.md.
AI:   "Let's fill this in section by section. Starting with **Problem** — in
       2-3 sentences, describe the real pain this product solves."
User: <answer>
AI:   [Edit tool: replace Problem section]
AI:   "Great. Next section: **Target users**. Who is the primary persona?"
…
AI:   "All 6 sections filled. Promote to `status: active`? (y/n)"
User: y
AI:   [promote] [/sdlc-kit:sync]
AI:   "✓ 00-steering/product.md is active. Next: `/sdlc-kit:steer tech`."
```

**Existing draft, user wants to refine one section:**
```
User: /sdlc-kit:steer tech
AI:   [status] tech.md — draft, updated 2026-04-10.
AI:   "A draft already exists. Want to review the whole thing, refine one section, or promote as-is?"
User: just the trade-offs section
AI:   [Read 00-steering/tech.md, locate the trade-offs heading]
AI:   "Current: <content>. What changes?"
User: <answer>
AI:   [Edit] [/sdlc-kit:sync]
```

**Zero-arg overview:**
```
User: /sdlc-kit:steer
AI:   product.md — active
      tech.md — draft
      standards.md — missing
AI:   "I'd suggest starting with `standards.md` — the template ships with strong
       defaults, so it's usually quick. Shall I run `/sdlc-kit:steer standards`?"
```

---

## See also

- `scripts/steer.py` — file-op helper.
- `assets/vault-tree/00-steering/_templates/` — canonical templates (copied into each vault at init time).
- `/sdlc-kit:adr` — for recording individual technical decisions referenced by `tech.md`.
- `/sdlc-kit:sync` — always invoked after steer edits.
