---
name: sdlc-trd
description: |
  Use when the user wants to record, review, or transition a Technical
  Requirements Document (TRD) — the cross-cutting non-functional baseline
  (performance, scalability, reliability, security, privacy/LGPD,
  observability, accessibility, maintainability, portability, cost) that
  multiple features/services inherit. One file per TRD under
  `02-architecture/trd/<slug>.md`, topic-based (not numbered). English
  triggers: `/sdlc-kit:trd`, `/sdlc-kit:trd new <title>`,
  `/sdlc-kit:trd list`, `/sdlc-kit:trd approve <slug>`,
  `/sdlc-kit:trd deprecate <slug>`, "write a TRD for X",
  "define platform NFRs", "set an availability SLO for the gateway",
  "approve the security TRD", "deprecate the old caching TRD". pt-BR
  triggers: "escrever um TRD para X", "definir os NFRs da plataforma",
  "estabelecer um SLO de disponibilidade para o gateway",
  "aprovar o TRD de segurança", "deprecar o TRD antigo de caching".
  Co-authored by a triad of expert personas: a **Software Architect**
  (drives scope, platform shape, pattern choices), an **AppSec Engineer**
  (drives security baseline, supply chain, privacy/LGPD, threat-model
  gates) and an **SRE / Platform Engineer** (drives SLIs/SLOs, RPO/RTO,
  observability, capacity, cost). Every requirement produced is testable
  (named metric + target + measurement method) and inheritable (feature
  specs either "comply with [[TRD-<slug>]]" in their §7 NFR block or request
  a documented deviation via an ADR). The script only does deterministic
  file ops — listing, scaffolding from `02-architecture/_templates/trd.md.tpl`,
  and lifecycle transitions (`draft → approved → deprecated`). The LLM
  drives the content interview section-by-section via Edit/Write, mirroring
  the user's chat language. Slugs are stable references and files are never
  renamed — if a TRD should no longer apply, deprecate it and write a
  successor. After scaffold or transition, invokes `/sdlc-kit:sync` so MOCs
  and `_INDEX.md` reflect the change. Do not invoke for feature-level
  functional requirements (`/sdlc-kit:spec`), product requirements
  (`/sdlc-kit:prd`), or single architectural decisions (`/sdlc-kit:adr`).
---

# sdlc-kit:trd

Creates and matures Technical Requirements Documents under `02-architecture/trd/`.

A TRD is the **cross-cutting non-functional contract** for a platform or bounded context: performance budgets, availability SLOs, security baseline, privacy/LGPD obligations, observability floor, accessibility criteria, cost ceilings. Feature specs inherit from it and call out any justified deviation via an ADR.

---

## What a TRD is (and isn't)

| TRD is… | TRD isn't… |
|---|---|
| The cross-feature NFR baseline (p95 latency, availability, RPO/RTO, TLS, KMS, WCAG 2.1 AA, SLI/SLO with burn alerts, cost ceilings) | A feature spec — feature-level FRs/NFRs belong in `/sdlc-kit:spec` |
| Testable: every requirement names a metric, a target, and a measurement method | A wish list or policy document without thresholds |
| Inherited by feature specs — their §7 NFR block says "complies with [[TRD-<slug>]]" | A replacement for ADRs — a TRD sets the baseline; an ADR records a specific structural decision that implements or deviates from it |
| Topic-based (slug = `api-rate-limiting`, `platform-security`, `mobile-client`) and stable | Numbered or sequence-based — there's no `TRD-0001`, the topic is the reference |
| Co-authored by **Software Architect + AppSec Engineer + SRE/Platform** | A solo architect document — if one of the three lenses is missing, the TRD is incomplete |

Statuses form a lifecycle: `draft` → `approved` → `deprecated`.

- `draft` — scaffolded, under review, not yet binding.
- `approved` — decision-authority signed off. Feature specs **must** comply or raise an ADR exception.
- `deprecated` — no longer binding on new work. Kept for history; successor TRD (if any) is linked from the frontmatter.

---

## When to invoke

Invoke when:

- The user types `/sdlc-kit:trd`, `/sdlc-kit:trd new <title>`, `/sdlc-kit:trd list`, `/sdlc-kit:trd approve <slug>`, `/sdlc-kit:trd deprecate <slug>`.
- The user says "write a TRD", "define the platform NFRs", "set an availability SLO", "approve the security TRD", "deprecate the old caching TRD", or equivalent phrasing in any other language.
- Multiple features are about to repeat the same non-functional commitments (latency, availability, security, observability) — pull them into a TRD so the commitments have one source of truth.
- A compliance or regulatory driver (LGPD, GDPR, sector audits) mandates a cross-cutting baseline that has no home yet.

**Do not** invoke when:

- The requirement is feature-specific (single critical path, single endpoint) → `/sdlc-kit:spec` §7.
- The user wants product requirements → `/sdlc-kit:prd`.
- The user wants a single architectural decision (pick Postgres vs Mongo, adopt gRPC) → `/sdlc-kit:adr`.
- cwd is not inside a vault.

---

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Template exists** at `<vault>/02-architecture/_templates/trd.md.tpl`. If missing (legacy vault), suggest `/sdlc-kit:init` repair.

---

## The expert triad

Every interview is co-authored, on every TRD, from the scaffold forward. Announce the triad at the start of the interview so the user knows which lenses are active:

> "I'll author this TRD as a triad: **Software Architect** (scope + patterns), **AppSec Engineer** (security + privacy), **SRE/Platform** (SLIs/SLOs + capacity + cost). Each section gets all three lenses before we move on."

| Section | Architect lens | AppSec lens | SRE/Platform lens |
|---|---|---|---|
| §1 Scope | Which services, which domains, which features inherit | Trust boundaries, regulated data flows in scope | Blast radius, tier classification |
| §2 Motivation | Cross-cutting risk/opportunity | Compliance/regulatory driver | Operational pain (pages, incidents, toil) |
| §3 Governance | Decision authority, review cadence | Exception review path | On-call owner, audit cadence |
| §4.1 Performance | p95 budget per critical path, throughput baseline | Abuse/DoS budget separation | Dashboards, load test source |
| §4.2 Scalability | Horizontal vs vertical, bottleneck | Tenant isolation under load | Peak absorption, data-volume ceilings |
| §4.3 Reliability | Multi-AZ/region posture, failure domains | Integrity under failure (no data loss = no fraud window) | SLO target, error budget, RPO/RTO, restore drills |
| §4.4 Security | AuthN/AuthZ baseline, deny-by-default | Full STRIDE pass, supply chain (Cosign/SBOM), vuln SLAs | Alerting on auth failures, key rotation ops |
| §4.5 Privacy/LGPD | Data flow minimization | Subject rights, masking, retention, audit trail | Log redaction at collector, retention enforcement |
| §4.6 Observability | Structured logs + baggage semantics | Audit log immutability, sensitive-field redaction | SLI/SLO with burn alerts, RED+USE metrics, OTEL traces, runbooks |
| §4.7 A11Y & UX | User-facing surfaces in scope | — | Synthetic accessibility checks in CI |
| §4.8 Maintainability | Linter/type-check, docs-as-code | SAST/SCA gates, image scan | CI budgets, flake policy |
| §4.9 I18N & Portability | Locales, runtime portability | Locale-aware redaction | Container runtime, cloud constraints |
| §4.10 Cost | Unit cost per request/tenant | Cost of security posture (KMS, signing, scanning) | Idle/off-peak scale-down, budget alarms |
| §5 SLIs & SLOs (consolidated) | Critical-path selection | Security SLIs (auth failure rate, vuln aging) | SLO math, burn rate alerts, error budget policy |
| §7 Impacts on existing systems | Migration shape | Required compensating controls | Rollout + verification plan |
| §8 Compliance & exception | ADR-link contract | Exception deviation review | Audit evidence cadence |
| §9 Technical risks | Architectural risks | AppSec risks | Operational risks |

If a cell is "—" for a given lens, still mention that lens was considered and found nothing to add — that's different from "forgotten".

---

## Flow

### List: `/sdlc-kit:trd` or `/sdlc-kit:trd list`

1. Run `trd.py --action list`. Parse the JSON `trds` array.
2. Show a compact table: `slug | status | title | owner | updated`.
3. If empty, offer: "No TRDs yet. Want to author one with `/sdlc-kit:trd new <title>`?"
4. Otherwise, offer next actions: open a draft, approve a mature draft, or create a new one.

### New TRD: `/sdlc-kit:trd new <title>`

1. **Derive the slug.** Propose a slug (lowercase ASCII, hyphen-separated) from the title and confirm — the user can override with `--slug`.
2. **List first** so you can warn about a collision early.
3. **Scaffold.** Run:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-trd/scripts/trd.py" \
     --vault-root "<vault>" --action scaffold \
     --slug "<slug>" --title "<title>" [--owner "<owner>"]
   ```
   The script refuses to overwrite an existing slug unless `--force` is passed; never pass `--force` without the user's explicit instruction.
4. **Announce the triad** and walk the interview (see below).

### The interview (LLM-driven, triad, section by section)

Walk the template top-to-bottom. One focused question at a time, editing in place via the Edit tool — do not rewrite the entire file at once. For each section, apply all three lenses before moving on.

**Phase A — Scope & governance** (§1–§3)
1. **Scope.** Which services/bounded contexts are in scope? Which features inherit? What is explicitly out of scope (and where is *its* TRD)?
2. **Parent/related docs.** Link C4 (`[[context]]`, `[[container]]`), related TRDs, related ADRs.
3. **Motivation.** 2–3 paragraphs: cross-cutting risk, what happens without a shared baseline, business/regulatory/operational driver.
4. **Governance.** Owner, decision authority, review cadence, exception process, effective-from date, sunset/next-review-by date.

**Phase B — Cross-cutting NFRs** (§4, all 10 sub-sections, always)

For each of §4.1 through §4.10, the rule is **fill it or mark it explicitly N/A with a reason** — never leave a sub-section blank. Every requirement produced must be **testable**: name the metric, the target, and the measurement method (dashboard / SLI source / load-test script / audit query).

| # | Section | Minimum deliverable |
|---|---|---|
| 4.1 | Performance | p95 latency budget on critical paths, throughput baseline, end-to-end response budget |
| 4.2 | Scalability | Peak vs steady multiplier, horizontal scaling ceiling + bottleneck, data volume ceiling |
| 4.3 | Reliability | Monthly availability SLO + error budget, RTO/RPO for tier-1 data, backup/restore drill cadence, multi-AZ/region posture |
| 4.4 | Security | AuthN baseline, AuthZ baseline (deny-by-default), encryption in transit + at rest, secrets sourcing + rotation, supply chain (signed images + SBOM), vuln SLA, STRIDE gate on new exposed surfaces |
| 4.5 | Privacy/LGPD | Data minimization, subject rights SLA, masking/redaction, retention matrix, tamper-evident audit log for sensitive actions |
| 4.6 | Observability | Structured-log schema w/ `correlation_id`/`tenant_id`/`actor_id`, RED+USE metrics, OTEL spans + baggage, SLO burn-rate alerts, DLQ alerts, runbook per alert |
| 4.7 | Accessibility + UX | WCAG 2.1 Level AA baseline on every user-facing surface, RFC 7807 problem-details error model |
| 4.8 | Maintainability | Test-coverage floor on changed files, linter + type-check + SAST + SCA + image-scan gates, Conventional Commits, docs-as-code discipline |
| 4.9 | I18N + Portability | Supported locales, container/orchestrator/cloud portability boundaries |
| 4.10 | Cost | Unit-cost ceiling per request/tenant/GB, off-peak scale-down target |

Every requirement gets the `TRD-<AREA>-<NN>` id assigned in the template (e.g. `TRD-PERF-01`, `TRD-SEC-04`). Keep the prefixes — feature specs will reference them.

**Phase C — Consolidated SLIs/SLOs** (§5)
Fill the `SLI | definition | SLO target | window | error budget | burn alert` table. Always include availability, p95 latency, error rate, and queue lag (where asynchronous). Burn-rate alerts default to `2%/1h` fast, `10%/6h` slow unless the user gives a reason to differ.

**Phase D — Architecture reference, impacts, risks** (§6–§9)
5. **Architecture.** Brief platform shape with the mermaid sketch. Link C4 where it exists.
6. **Impacts on existing systems.** One row per system that must change to comply, with effort estimate and owner — otherwise the TRD is aspirational.
7. **Compliance & exception process.** Compliance evidence method per TRD-* (test / dashboard / audit query); exception = ADR linked back to this TRD, with compensating control and sunset date.
8. **Technical risks.** L/M/H probability × impact with mitigation and owner. Architect, AppSec and SRE each contribute at least one row.
9. **Open questions.** Capture anything the triad could not resolve now, with owner + by-when.

**References (§References)**
Wikilink `[[context]]`, `[[container]]`, related ADRs, related TRDs, and the global `[[_INDEX]]`.

Keep the whole interview bounded — roughly 10–14 questions; prefer N/A with a reason over long digressions. When the user has nothing for a sub-section, leave the template prose in place, mark it `N/A — <reason>`, and offer to revisit at the next review.

### Transition: `/sdlc-kit:trd {approve|deprecate} <slug>`

Map verb → target status:

| Verb | Target status | When to use |
|---|---|---|
| `approve` | `approved` | Decision authority signed off; feature specs must now comply or raise an ADR exception |
| `deprecate` | `deprecated` | No longer binding on new work (usually because a successor TRD exists or the platform shape changed) |

Run:
```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-trd/scripts/trd.py" \
  --vault-root "<vault>" --action transition \
  --slug "<slug>" --to "<draft|approved|deprecated>"
```

Idempotent: if the TRD is already at the target status, the script writes nothing.

**Before approving**, run the pre-approval checklist with the user:

- [ ] All §4 sub-sections filled or explicitly `N/A` with a reason.
- [ ] Every requirement has metric + target + measurement method.
- [ ] §5 SLI/SLO table has availability + latency + error-rate rows.
- [ ] §3 Governance has decision authority, review cadence, exception path.
- [ ] §7 Impacts lists every affected system with owner + effort estimate (or is explicitly "greenfield, no existing impact").
- [ ] §8 Compliance & exception process names the ADR-linking flow.
- [ ] Triad acknowledgement captured (Architect / AppSec / SRE each signed off on their lens).

If any box is unchecked, do **not** approve — invite the user to fill the gap or mark it N/A first.

**Before deprecating**, confirm:
- Is there a successor TRD? If yes, capture the link in §1.3 before deprecating.
- Are any feature specs currently declaring compliance with this TRD? If yes, warn the user — those specs will need to be retargeted.

### Sync

After every `scaffold` or `transition`, invoke `/sdlc-kit:sync` so `_INDEX.md` and `02-architecture/_MOC.md` reflect the change.

---

## Output contract

```json
// --action list
{
  "status": "ok",
  "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "trds": [
    {
      "slug": "platform-security",
      "path": "02-architecture/trd/platform-security.md",
      "title": "Platform Security Baseline",
      "status": "approved",
      "owner": "Milton",
      "updated": "2026-04-17"
    }
  ],
  "count": 1,
  "errors": []
}

// --action scaffold
{
  "status": "ok",
  "action": "scaffold",
  "vault_root": "/abs/path/.sdlc",
  "slug": "api-rate-limiting",
  "trd_path": "02-architecture/trd/api-rate-limiting.md",
  "was_new": true,
  "errors": []
}

// --action transition
{
  "status": "ok",
  "action": "transition",
  "vault_root": "/abs/path/.sdlc",
  "slug": "api-rate-limiting",
  "trd_path": "02-architecture/trd/api-rate-limiting.md",
  "previous_status": "draft",
  "new_status": "approved",
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error (invalid slug/status, TRD not found, collision without `--force`) · `2` fatal (permission denied, IO, missing template).

---

## Guardrails

**Never:**
- Skip the triad. Every section gets the Architect + AppSec + SRE lenses before moving on. If a lens is genuinely silent on a sub-section, say so explicitly — "AppSec: no additional constraint beyond §4.4 baseline" — rather than silently omitting it.
- Leave any §4 sub-section blank. Fill it, or mark it explicitly `N/A — <reason>`. A silent omission will let a feature spec inherit an undefined commitment.
- Produce an untestable requirement. "Fast" / "secure" / "reliable" are not requirements. If you cannot name a metric, a target and a measurement method, you have a *goal*, not a requirement — ask the user to make it measurable before writing the row.
- Write an SLO without an error budget and a burn-rate alert. An SLO without a burn policy is decoration.
- Approve a TRD with open §4 sections, open §5 SLO rows, or empty governance. The pre-approval checklist is a hard gate.
- Rename or delete an existing TRD. The slug is a stable reference — if the topic shifts, deprecate the TRD and scaffold a successor.
- Treat a TRD as a substitute for an ADR. A TRD sets the baseline ("TLS ≥ 1.2 everywhere"); an ADR records a specific structural decision ("adopt mTLS between internal services using SPIFFE").
- Duplicate cross-cutting NFRs inside a feature spec. The spec's §7 NFR block either *inherits* from the TRD ("complies with [[TRD-<slug>]]") or *calls out a justified deviation* via an ADR.

**Always:**
- Match the user's active conversation language.
- Announce the triad at the start of the interview.
- Run `--action list` before `scaffold` so you can report the collision surface.
- Mirror the template taxonomy exactly — the 10 `§4.x` buckets and their `TRD-<AREA>-<NN>` prefixes align with `04-specs/_templates/requirements.md.tpl §7`, which is how feature specs inherit.
- Invoke `/sdlc-kit:sync` after any scaffold or transition.
- Before `approve`, walk the pre-approval checklist with the user, section by section, and get an explicit "go" — `approved` means humans signed off.
- Before `deprecate`, search for feature specs currently declaring compliance and warn the user about the retarget they'll need.
- Surface the generated file path in the final report so the user can open it.

---

## Examples

> Examples below are in English. In a real session, mirror the user's active conversation language in every user-facing line.

**Authoring a new TRD:**
```
User: /sdlc-kit:trd new Platform security baseline
AI:   [list] 0 existing TRDs. Proposed slug: `platform-security-baseline`. OK, or override?
User: shorten to `platform-security`.
AI:   [scaffold --slug platform-security --title "Platform security baseline"]
AI:   created 02-architecture/trd/platform-security.md (status=draft).
AI:   "I'll author this as a triad — Software Architect + AppSec + SRE/Platform. Let's start with
       §1 Scope. Which services/domains are in scope, and which features inherit this baseline?"
User: <answer>
AI:   [Edit §1 Scope, then §2 Motivation, §3 Governance, §4.1 Performance …]
…
AI:   "All 10 §4 sub-sections filled (4.7 and 4.9 marked N/A with reason). Pre-approval checklist
       ready — want to walk it now, or leave as `draft` for tech-lead review?"
User: leave as draft; will review on Thursday.
AI:   "Got it. When ready: `/sdlc-kit:trd approve platform-security`."
```

**Listing TRDs:**
```
User: /sdlc-kit:trd list
AI:   | slug                  | status     | title                          | owner    | updated    |
      |-----------------------|------------|--------------------------------|----------|------------|
      | platform-security     | approved   | Platform Security Baseline     | Milton   | 2026-04-17 |
      | api-rate-limiting     | draft      | API Rate Limiting NFRs         | Ana      | 2026-04-16 |
      | mobile-client         | deprecated | Mobile Client NFRs             | legacy   | 2025-11-02 |
AI:   "3 TRDs. Want to walk the rate-limiting draft toward approval?"
```

**Approving after review (pre-approval checklist):**
```
User: /sdlc-kit:trd approve platform-security
AI:   [list] platform-security — draft.
AI:   "Before approving, let's walk the pre-approval checklist together."
AI:   "- §4 sub-sections: 10/10 filled or N/A? ✓
       - Every TRD-* has metric + target + measurement? ✓
       - §5 SLI/SLO table has availability + latency + error rate + queue lag? ✓
       - §3 Governance: decision authority = Platform Eng Lead, cadence = quarterly, exception = ADR? ✓
       - §7 Impacts: 3 systems listed with owner + estimate? ✓
       - §8 exception flow names ADR contract? ✓
       - Triad sign-off: Architect ✓ / AppSec ✓ / SRE ✓?"
User: all green.
AI:   [transition draft→approved] [/sdlc-kit:sync]
AI:   "✓ TRD platform-security is now approved. Feature specs must comply — or raise an ADR
       exception referencing this TRD."
```

**Idempotent transition:**
```
User: /sdlc-kit:trd approve platform-security
AI:   [list] platform-security already approved — nothing to do. Skipping sync.
```

**Deprecating with successor:**
```
User: /sdlc-kit:trd deprecate mobile-client
AI:   "Before deprecating, is there a successor TRD (e.g. a replacement mobile-experience TRD)?"
User: yes, `mobile-experience` was approved last month.
AI:   "Any feature specs currently declaring compliance with `mobile-client`? Let me check."
AI:   [grep `[[TRD-mobile-client]]` under 04-specs — 2 hits]
AI:   "2 feature specs still reference it: `04-specs/offline-sync/requirements.md` and
       `04-specs/push-notifications/requirements.md`. They'll need to be retargeted to
       `[[TRD-mobile-experience]]` before deprecation bites. Proceed anyway?"
User: yes, open tickets for the retarget.
AI:   [Edit §1.3 of mobile-client: superseded_by: mobile-experience]
AI:   [transition approved→deprecated] [/sdlc-kit:sync]
AI:   "✓ TRD mobile-client is now deprecated, linked to successor `mobile-experience`.
       Heads-up: 2 specs still reference it — retarget before their next change."
```

---

## See also

- `scripts/trd.py` — file-op helper.
- `assets/vault-tree/02-architecture/_templates/trd.md.tpl` — canonical TRD template (10 §4 sub-sections + §5 SLI/SLO table + §8 exception flow).
- `/sdlc-kit:adr` — single architectural decisions; also the exception-carrier when a feature deviates from an approved TRD.
- `/sdlc-kit:spec` — feature-level specs whose §7 NFR block inherits from one or more TRDs.
- `/sdlc-kit:c4` — context/container/component diagrams that the TRD scope references.
- `/sdlc-kit:sync` — always invoked after TRD edits.
