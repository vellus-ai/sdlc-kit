---
name: sdlc-design-validation
description: |
  Use as Gate 3 of the frontend UX workflow — validates that UX research
  (Gate 1) and Design System initialization (Gate 2) are complete and
  consistent before a TRD is authored (Gate 4). Reads ux-criteria.md,
  user-flows.md, wireframes/, and design-system tokens/components/patterns.
  Produces a go/no-go report and a `06-design-system/design-validation.md`
  artifact with gap analysis and explicit sign-off.
  Triggers: `/sdlc-kit:design-validation`, `/sdlc-kit:design-validation run`,
  `/sdlc-kit:design-validation approve`, "validate UX design",
  "run design gate", "is the design ready for TRD?",
  "validate before TRD", "design review gate".
  pt-BR: "validar design", "rodar gate de design",
  "o design está pronto para o TRD?", "validação de design".
  Acts as a dual-persona reviewer: **Senior UX Designer** (flow completeness,
  acceptance criteria quality, accessibility gaps) + **Frontend Architect**
  (technical feasibility, design-system coverage, spec gaps that will block
  implementation). Output: `draft` validation report that the user promotes
  to `approved` (pass) or keeps as `draft` with gap tasks. Do not invoke
  before `/sdlc-kit:ux` (Gate 1) and at least one `/sdlc-kit:design-system`
  entry exist.
---

# sdlc-kit:design-validation

Gate 3 of the frontend UX workflow. Validates that UX research and Design
System foundation are complete enough to write a meaningful TRD.

---

## What this gate checks

| Category | Checks |
|---|---|
| **UX Criteria** | Personas exist; JTBD present; ≥1 AC per JTBD; accessibility baseline filled |
| **User Flows** | ≥1 flow per JTBD; happy path + ≥1 edge path; cross-flow diagram complete |
| **Wireframes** | ≥1 wireframe per flow identified in user-flows; no empty Layout Regions; accessibility notes present |
| **Design System** | ≥1 token or component exists (Gate 2 was started); no `<tbd>` values in stable entries |
| **Cross-references** | ux-criteria wikilinks from spec/prd are resolvable; wireframes link to their flow |
| **Readiness** | No open questions marked as blocking; no `<placeholder>` tokens in diagrams |

A **PASS** means: engineering can plan implementation using these artifacts. A **FAIL** means: listed gaps must be resolved before TRD authoring begins.

---

## When to invoke

- User has completed Gates 1+2 and wants to proceed to Gate 4 (`/sdlc-kit:trd`).
- User asks "is the design ready?", "can we start the TRD?", or equivalent.

**Do not invoke when:**
- `ux-criteria.md` does not exist → run `/sdlc-kit:ux` first.
- The initiative has no user-facing surface → Gate 3 is not applicable.
- cwd is not inside a vault.

---

## Flow

### Run: `/sdlc-kit:design-validation` or `/sdlc-kit:design-validation run`

1. **Announce the review mode.** "Running Gate 3 design validation as:
   **Senior UX Designer** (flow + criteria completeness, accessibility) +
   **Frontend Architect** (feasibility, spec coverage, design-system gaps)."

2. **Read the vault** (using Read tool — do not call ux.py; read files directly):
   - `06-design-system/ux-criteria.md`
   - `06-design-system/user-flows.md`
   - `06-design-system/wireframes/*.md` (all files)
   - `06-design-system/tokens/*.md`, `components/*.md`, `patterns/*.md`
     (check if any stable entry exists for Gate 2 confirmation)

3. **Run the checklist** (all items from the table above) and collect:
   - `pass` — criterion met
   - `warn` — criterion partially met (design can proceed with noted caveat)
   - `fail` — criterion not met; blocks TRD authoring

4. **Scaffold the validation report:**
   Write `06-design-system/design-validation.md` using the template below
   (no external script needed — use the Write tool directly):
   ```markdown
   ---
   type: design-validation
   title: "Design Validation — <initiative>"
   slug: "design-validation"
   status: draft
   phase: 06
   created: <today>
   updated: <today>
   generated_by: sdlc-design-validation
   owner: "<owner>"
   tags: [ux, design, validation, gate-3]
   verdict: <PASS|FAIL|PASS_WITH_WARNINGS>
   ---

   # Design Validation — <initiative>

   **Verdict: PASS / FAIL / PASS WITH WARNINGS**

   ## Checklist

   | Category | Item | Result | Notes |
   |---|---|---|---|
   | UX Criteria | Personas present | ✅ / ❌ | |
   | UX Criteria | JTBD present | ✅ / ❌ | |
   | … | … | … | … |

   ## Gaps (FAIL items)

   For each `fail`:
   - **Gap:** <description>
   - **Blocks:** <which TRD section would be incomplete>
   - **Fix:** <what needs to be done>

   ## Warnings

   For each `warn`: describe caveat and owner.

   ## Sign-off

   - [ ] Senior UX Designer sign-off
   - [ ] Frontend Architect sign-off
   - [ ] Product Owner sign-off

   ## References

   - [[ux-criteria]]
   - [[user-flows]]
   - [[_INDEX]]
   ```

5. **Report to user:**
   - PASS: "Design Gate 3 passed. Run `/sdlc-kit:design-validation approve`
     then proceed to `/sdlc-kit:trd new <title>`."
   - PASS WITH WARNINGS: "Design Gate 3 passed with warnings. Review the
     caveats in `design-validation.md` before TRD authoring."
   - FAIL: "Design Gate 3 failed. N gap(s) must be resolved. See
     `design-validation.md` for details."

6. Invoke `/sdlc-kit:sync`.

### Approve: `/sdlc-kit:design-validation approve`

1. Read `06-design-system/design-validation.md`. Check `verdict` frontmatter.
2. If `verdict: FAIL` → refuse. "Gate 3 has open failures. Resolve them first."
3. If PASS or PASS_WITH_WARNINGS → run the sign-off checklist with the user:
   - "Senior UX Designer sign-off confirmed?"
   - "Frontend Architect sign-off confirmed?"
   - "Product Owner sign-off confirmed?"
4. On explicit yes for all three: flip `status: draft` → `status: approved`
   in `design-validation.md` via Edit tool.
5. Invoke `/sdlc-kit:sync`.
6. Suggest next step: `/sdlc-kit:trd new <title>`.

---

## Guardrails

**Never:**
- Auto-approve. All three sign-offs must be confirmed by the user explicitly.
- Mark a FAIL verdict as PASS — if the UX Criteria or user flows are
  missing key content, it's a FAIL regardless of time pressure.
- Proceed to TRD without an `approved` design-validation. This gate exists
  to prevent TRD authors from writing NFRs for undefined surfaces.
- Overwrite an existing `approved` design-validation without `--force` and
  explicit user confirmation.

**Always:**
- Mirror the user's active conversation language.
- Read the actual files before validating — do not rely on frontmatter alone.
- Surface specific line-level gaps (e.g., "User Flows > Flow 01 > Error Paths:
  empty — must have ≥ 1 edge case").
- On FAIL, produce actionable fix tasks the user can pick up immediately.
- After any write, invoke `/sdlc-kit:sync`.

---

## Examples

**Running the gate:**
```
User: /sdlc-kit:design-validation
AI:   "Running Gate 3 — Senior UX Designer + Frontend Architect lenses."
AI:   [reads ux-criteria.md, user-flows.md, wireframes/login.md, wireframes/checkout.md]
AI:   "Gate 3 results:
       ✅ Personas (2 defined)
       ✅ JTBD (3 present, mapped to AC)
       ❌ User Flows — Flow 02 (Payment) has no edge paths
       ❌ Wireframe `checkout` — Layout Regions section is empty
       ⚠️  Design System — 0 stable tokens (Gate 2 not started)

       Verdict: FAIL — 2 blocking gaps.
       Report saved to design-validation.md.
       Fix flows + wireframe, then re-run."
```

**Gate passing:**
```
User: /sdlc-kit:design-validation run
AI:   [reads files] "All items pass. 1 warning: accessibility notes in
       wireframe/login have placeholders.
       Verdict: PASS WITH WARNINGS.
       Run `/sdlc-kit:design-validation approve` after the team reviews
       the warnings."
```

---

## See also

- `/sdlc-kit:ux` — Gate 1: UX research.
- `/sdlc-kit:design-system` — Gate 2: design tokens, components, patterns.
- `/sdlc-kit:trd` — Gate 4: technical NFR requirements (requires Gate 3 approved).
- `/sdlc-kit:sync` — vault reindex.
