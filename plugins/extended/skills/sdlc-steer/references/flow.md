# sdlc-kit:steer — full flow

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Templates exist** at `<vault>/00-steering/_templates/{product,tech,standards}.md.tpl`.

## Flow

### Zero-arg: `/sdlc-kit:steer`

1. Run `steer.py --action status`.
2. Show one-line summary per doc: `product.md — missing | tech.md — draft | standards.md — active`.
3. Suggest next action via `next_suggested`:
   - first missing → "Want to start with `/sdlc-kit:steer <name>`?"
   - else first draft → "Want to review and promote `<name>.md`?"
   - none pending → "All three steering docs are active."

### With arg: `/sdlc-kit:steer {product|tech|standards}`

1. **Status check** first — does target exist?
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-steer/scripts/steer.py" \
     --vault-root "<vault>" --action status
   ```
2. **Branch A — doc missing:** scaffold.
   ```bash
   python "...steer.py" --vault-root "<vault>" --action scaffold --doc <name>
   ```
   Then begin the interview.
3. **Branch B — doc exists (draft or active):** read the file, ask what sections to update. Offer: `[r] review and refine  [s] show diff before edits  [p] promote to active (if complete)  [x] cancel`.

### The interview (LLM-driven, section by section)

For each section:
1. Show section name and any placeholder text.
2. Ask focused question in user's chat language.
3. Edit the section in place via Edit.
4. Move to next.

Don't rewrite the whole file at once. Section-by-section.

Keep short:
- `product.md`: problem → target users → value prop → principles → north-star → non-goals (≤ 6 questions).
- `tech.md`: stack rows → principles → trade-offs → founding ADRs → quality rules (≤ 5 questions).
- `standards.md`: most ships with good defaults — only ask project-specific rows (code style, review thresholds).

### Promotion

When user says "this is good" / "ship it" / explicitly approves:
```bash
python "...steer.py" --vault-root "<vault>" --action promote --doc <name>
```

Flips `status: draft` → `status: active` and refreshes `updated:`.

### Sync

After any scaffold, edit, or promotion, invoke `/sdlc-kit:sync`.

## Output contract

```json
// --action status
{
  "status": "ok", "action": "status",
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
  "status": "ok", "action": "scaffold",
  "doc": "tech", "doc_path": "00-steering/tech.md",
  "was_new": true, "errors": []
}

// --action promote
{
  "status": "ok", "action": "promote",
  "doc": "tech", "doc_path": "00-steering/tech.md",
  "previous_status": "draft", "new_status": "active",
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error · `2` fatal.

## Guardrails

**Never:**
- Touch `CLAUDE.md` — sovereign. Suggest manual user edit.
- Overwrite without `--force` and explicit confirmation.
- Rewrite the entire doc in one Edit call.
- Auto-promote to `active`.
- Fabricate content — leave placeholders.

**Always:**
- Match the user's active conversation language.
- Run `--action status` before scaffold/promote.
- Invoke `/sdlc-kit:sync` after edits.
- Surface generated file path.

## Examples

**Fresh vault, user starts with product vision:**
```
User: /sdlc-kit:steer product
AI:   [status] product.md — missing. [scaffold]
AI:   "**Problem** — in 2-3 sentences, the real pain this product solves."
User: <answer>
AI:   [Edit: replace Problem]
AI:   "**Target users** — who's the primary persona?"
…
AI:   "All 6 sections filled. Promote to `status: active`?"
User: y
AI:   [promote][/sdlc-kit:sync]
AI:   "✓ active. Next: `/sdlc-kit:steer tech`."
```

**Existing draft, refine one section:**
```
User: /sdlc-kit:steer tech
AI:   [status] tech.md — draft, updated 2026-04-10.
AI:   "Draft exists. Review whole, refine one section, or promote as-is?"
User: just trade-offs
AI:   [Read; locate trade-offs heading]
AI:   "Current: <content>. What changes?"
User: <answer>
AI:   [Edit][/sdlc-kit:sync]
```

**Zero-arg overview:**
```
User: /sdlc-kit:steer
AI:   product.md — active
      tech.md — draft
      standards.md — missing
AI:   "I'd suggest starting with `standards.md` — defaults are strong, usually quick."
```

## See also

- `scripts/steer.py` — file-op helper.
- `assets/vault-tree/00-steering/_templates/`.
- `/sdlc-kit:adr`, `/sdlc-kit:sync`.
