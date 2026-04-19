# sdlc-kit:trd — full flow

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Template exists** at `<vault>/02-architecture/_templates/trd.md.tpl`.

## The expert triad

Announce at the start:
> "I'll author this TRD as a triad: **Software Architect** (scope + patterns), **AppSec Engineer** (security + privacy), **SRE/Platform** (SLIs/SLOs + capacity + cost). Each section gets all three lenses before we move on."

| Section | Architect | AppSec | SRE/Platform |
|---|---|---|---|
| §1 Scope | Which services, domains, features inherit | Trust boundaries, regulated data flows | Blast radius, tier classification |
| §2 Motivation | Cross-cutting risk/opportunity | Compliance/regulatory driver | Operational pain (pages, incidents, toil) |
| §3 Governance | Decision authority, review cadence | Exception review path | On-call owner, audit cadence |
| §4.1 Performance | p95 budget per critical path, throughput | Abuse/DoS budget separation | Dashboards, load test source |
| §4.2 Scalability | Horizontal vs vertical, bottleneck | Tenant isolation under load | Peak absorption, data-volume ceilings |
| §4.3 Reliability | Multi-AZ/region posture, failure domains | Integrity under failure | SLO target, error budget, RPO/RTO, restore drills |
| §4.4 Security | AuthN/AuthZ baseline, deny-by-default | Full STRIDE pass, supply chain (Cosign/SBOM), vuln SLAs | Alerting on auth failures, key rotation |
| §4.5 Privacy/LGPD | Data flow minimization | Subject rights, masking, retention, audit trail | Log redaction at collector, retention enforcement |
| §4.6 Observability | Structured logs + baggage | Audit log immutability, sensitive-field redaction | SLI/SLO with burn alerts, RED+USE metrics, OTEL traces, runbooks |
| §4.7 A11Y & UX | User-facing surfaces in scope | — | Synthetic accessibility checks in CI |
| §4.8 Maintainability | Linter/type-check, docs-as-code | SAST/SCA gates, image scan | CI budgets, flake policy |
| §4.9 I18N & Portability | Locales, runtime portability | Locale-aware redaction | Container runtime, cloud constraints |
| §4.10 Cost | Unit cost per request/tenant | Cost of security posture (KMS, signing, scanning) | Idle/off-peak scale-down, budget alarms |
| §5 SLIs & SLOs | Critical-path selection | Security SLIs (auth failure rate, vuln aging) | SLO math, burn rate alerts, error budget policy |
| §7 Impacts | Migration shape | Required compensating controls | Rollout + verification plan |
| §8 Compliance & exception | ADR-link contract | Exception deviation review | Audit evidence cadence |
| §9 Technical risks | Architectural risks | AppSec risks | Operational risks |

If a cell is "—", still mention the lens was considered and found nothing — different from "forgotten".

## Flow

### List: `/sdlc-kit:trd` or `/sdlc-kit:trd list`

1. Run `trd.py --action list`.
2. Show: `slug | status | title | owner | updated`.
3. Offer next.

### New: `/sdlc-kit:trd new <title>`

1. **Derive slug.** Propose from title; allow override.
2. **List first** to warn collisions.
3. **Scaffold:**
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-trd/scripts/trd.py" \
     --vault-root "<vault>" --action scaffold \
     --slug "<slug>" --title "<title>" [--owner "<owner>"]
   ```
4. **Announce the triad** and walk the interview.

### The interview (LLM-driven, triad, section by section)

**Phase A — Scope & governance** (§1–§3)
1. **Scope.** Which services/contexts in scope? Which features inherit? What's out of scope (and where is *its* TRD)?
2. **Parent/related docs.** Link C4 (`[[context]]`, `[[container]]`), related TRDs, related ADRs.
3. **Motivation.** 2–3 paragraphs: cross-cutting risk; what happens without a baseline; business/regulatory/operational driver.
4. **Governance.** Owner, decision authority, review cadence, exception process, effective-from, sunset/next-review-by.

**Phase B — Cross-cutting NFRs** (§4, all 10, always)

For each §4.1–§4.10: **fill it or mark explicitly N/A with reason** — never blank.
Every requirement must be **testable**: name metric, target, measurement method.

| # | Section | Minimum deliverable |
|---|---|---|
| 4.1 | Performance | p95 latency budget on critical paths, throughput baseline, end-to-end response budget |
| 4.2 | Scalability | Peak vs steady multiplier, horizontal scaling ceiling + bottleneck, data volume ceiling |
| 4.3 | Reliability | Monthly availability SLO + error budget, RTO/RPO for tier-1, backup/restore drill cadence, multi-AZ/region |
| 4.4 | Security | AuthN baseline, AuthZ baseline (deny-by-default), encryption in transit + at rest, secrets sourcing + rotation, supply chain (signed images + SBOM), vuln SLA, STRIDE gate on new exposed surfaces |
| 4.5 | Privacy/LGPD | Data minimization, subject rights SLA, masking/redaction, retention matrix, tamper-evident audit log |
| 4.6 | Observability | Structured-log schema w/ `correlation_id`/`tenant_id`/`actor_id`, RED+USE metrics, OTEL spans + baggage, SLO burn-rate alerts, DLQ alerts, runbook per alert |
| 4.7 | A11Y + UX | WCAG 2.1 AA on user-facing surfaces, RFC 7807 problem-details error model |
| 4.8 | Maintainability | Test-coverage floor on changed files, linter + type-check + SAST + SCA + image-scan gates, Conventional Commits, docs-as-code |
| 4.9 | I18N + Portability | Supported locales, container/orchestrator/cloud portability boundaries |
| 4.10 | Cost | Unit-cost ceiling per request/tenant/GB, off-peak scale-down target |

Every requirement gets the `TRD-<AREA>-<NN>` id (e.g. `TRD-PERF-01`, `TRD-SEC-04`).
Keep the prefixes — feature specs reference them.

**Phase C — Consolidated SLIs/SLOs** (§5)
Fill `SLI | definition | SLO target | window | error budget | burn alert`. Always
include availability, p95 latency, error rate, queue lag (where async). Burn-rate
defaults `2%/1h` fast, `10%/6h` slow unless reason to differ.

**Phase D — Architecture, impacts, risks** (§6–§9)
5. **Architecture.** Brief platform shape with mermaid sketch. Link C4 where it exists.
6. **Impacts on existing systems.** One row per system that must change to comply, with effort estimate + owner — otherwise the TRD is aspirational.
7. **Compliance & exception process.** Compliance evidence per TRD-* (test/dashboard/audit query); exception = ADR linked back, with compensating control + sunset date.
8. **Technical risks.** L/M/H probability × impact with mitigation + owner. Architect, AppSec, SRE each contribute ≥ 1 row.
9. **Open questions.** With owner + by-when.

**References (§References)** — `[[context]]`, `[[container]]`, related ADRs/TRDs, `[[_INDEX]]`.

Bound to ~10–14 questions; prefer N/A with reason over digressions.

### Transition: `/sdlc-kit:trd {approve|deprecate} <slug>`

| Verb | Target | When |
|---|---|---|
| `approve` | `approved` | Decision authority signed off |
| `deprecate` | `deprecated` | No longer binding (usually because successor exists or platform changed) |

```bash
python "...trd.py" --vault-root "<vault>" --action transition \
  --slug "<slug>" --to "<draft|approved|deprecated>"
```

Idempotent.

**Pre-approval checklist** (hard gate):

- [ ] All §4 sub-sections filled or explicitly `N/A` with reason.
- [ ] Every requirement has metric + target + measurement method.
- [ ] §5 SLI/SLO has availability + latency + error-rate rows.
- [ ] §3 Governance has decision authority, review cadence, exception path.
- [ ] §7 Impacts lists every affected system with owner + effort estimate (or "greenfield").
- [ ] §8 Compliance & exception process names the ADR-linking flow.
- [ ] Triad acknowledgement captured (Architect / AppSec / SRE each signed off).

If any unchecked, do **not** approve.

**Before deprecating**:
- Successor TRD? If yes, capture link in §1.3 first.
- Feature specs declaring compliance? Warn — they'll need retargeting.

### Sync

After every `scaffold` or `transition`, invoke `/sdlc-kit:sync`.

## Output contract

```json
// --action list
{
  "status": "ok", "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "trds": [
    {"slug": "platform-security", "path": "02-architecture/trd/platform-security.md",
     "title": "Platform Security Baseline", "status": "approved",
     "owner": "Milton", "updated": "2026-04-17"}
  ],
  "count": 1, "errors": []
}

// --action scaffold
{
  "status": "ok", "action": "scaffold",
  "slug": "api-rate-limiting",
  "trd_path": "02-architecture/trd/api-rate-limiting.md",
  "was_new": true, "errors": []
}

// --action transition
{
  "status": "ok", "action": "transition",
  "slug": "api-rate-limiting",
  "trd_path": "02-architecture/trd/api-rate-limiting.md",
  "previous_status": "draft", "new_status": "approved",
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error · `2` fatal.

## Guardrails

**Never:**
- Skip the triad. If a lens is silent on a sub-section, say so explicitly.
- Leave any §4 sub-section blank. Fill or `N/A — <reason>`.
- Produce an untestable requirement. "Fast" / "secure" / "reliable" are goals, not requirements. Need metric + target + measurement.
- Write an SLO without an error budget and burn-rate alert. SLO without burn = decoration.
- Approve with open §4 sections, open §5 SLOs, or empty governance. Hard gate.
- Rename or delete a TRD. Slug is stable. Deprecate + write successor.
- Treat a TRD as substitute for ADR. TRD = baseline ("TLS ≥ 1.2 everywhere"); ADR = specific structural decision ("adopt mTLS using SPIFFE").
- Duplicate cross-cutting NFRs inside a feature spec. Spec §7 inherits from TRD or calls out a justified deviation via ADR.

**Always:**
- Match the user's active conversation language.
- Announce the triad at the start.
- Run `--action list` before `scaffold`.
- Mirror template taxonomy — 10 §4.x buckets and `TRD-<AREA>-<NN>` prefixes align with `04-specs/_templates/requirements.md.tpl §7`.
- Invoke `/sdlc-kit:sync` after any scaffold or transition.
- Before `approve`, walk pre-approval checklist with user; explicit "go".
- Before `deprecate`, search feature specs for compliance refs and warn.
- Surface generated file path.

## Examples

**Authoring a new TRD:**
```
User: /sdlc-kit:trd new Platform security baseline
AI:   [list] 0 existing. Proposed slug: `platform-security-baseline`. OK?
User: shorten to `platform-security`.
AI:   [scaffold --slug platform-security]
AI:   "Authoring as triad — Architect + AppSec + SRE. §1 Scope: which services/domains in scope? Which features inherit?"
User: <answer>
AI:   [Edit §1, then §2, §3, §4.1 …]
…
AI:   "All 10 §4 filled (4.7 and 4.9 N/A with reason). Pre-approval checklist ready — walk now or leave as `draft`?"
User: leave as draft.
AI:   "When ready: `/sdlc-kit:trd approve platform-security`."
```

**Approving (pre-approval checklist):**
```
User: /sdlc-kit:trd approve platform-security
AI:   [list] platform-security — draft.
AI:   "Walking pre-approval:
       - §4 sub-sections 10/10 filled or N/A ✓
       - Every TRD-* has metric + target + measurement ✓
       - §5 has availability + latency + error rate + queue lag ✓
       - §3 Governance: authority, cadence, exception ✓
       - §7 Impacts: 3 systems with owner + estimate ✓
       - §8 names ADR contract ✓
       - Triad: Architect ✓ / AppSec ✓ / SRE ✓?"
User: all green.
AI:   [transition draft→approved][/sdlc-kit:sync]
AI:   "✓ approved. Feature specs must comply or raise an ADR exception."
```

**Deprecating with successor:**
```
User: /sdlc-kit:trd deprecate mobile-client
AI:   "Successor TRD?"
User: yes, `mobile-experience` was approved last month.
AI:   "Specs declaring compliance with `mobile-client`? Let me check."
AI:   [grep `[[TRD-mobile-client]]` under 04-specs — 2 hits]
AI:   "2 specs reference it: `offline-sync/requirements.md` and `push-notifications/requirements.md`. They'll need retargeting. Proceed?"
User: yes, open tickets.
AI:   [Edit §1.3 of mobile-client: superseded_by: mobile-experience]
AI:   [transition approved→deprecated][/sdlc-kit:sync]
```

## See also

- `scripts/trd.py` — file-op helper.
- `assets/vault-tree/02-architecture/_templates/trd.md.tpl`.
- `/sdlc-kit:adr` — single decisions; also exception-carrier when feature deviates from approved TRD.
- `/sdlc-kit:spec` — feature specs whose §7 NFR block inherits from one or more TRDs.
- `/sdlc-kit:c4`, `/sdlc-kit:sync`.
