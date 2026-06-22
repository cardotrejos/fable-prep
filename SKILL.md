---
name: fable-prep
description: >-
  Prepare and execute your hardest, highest-leverage work for your most capable model.
  ONE adaptive loop. When the frontier model (Fable 5) is UNAVAILABLE it runs PLAN-MODE —
  sweeps your repos across every domain (code, design, copy, marketing), adversarially
  verifies each finding, and emits a globally-ranked WAVE QUEUE of execution-ready packets.
  When the frontier model is LIVE it runs EXECUTE-MODE — straight-executes the queue through
  tiered gates, pausing per wave. The thesis: the frontier model one-shots what cheaper models
  grind through rounds — so you never spend its scarce, expensive time on planning; you spend
  it shipping. Triggers on 'fable prep', 'prep for fable', 'fable queue', 'fable night',
  'prep hardest tasks', 'round-collapse', 'prep for my best model', 'frontier queue'.
---

# fable-prep — stage the hardest work now, one-shot it when the chef arrives

## The one idea

Your best model is the Michelin chef you can only book for a few hours, and the booking
may turn metered (API pricing) the moment it returns. You do not make that chef peel
potatoes or read the menu. You prep every station — mise en place, tickets, timers — so
the instant it walks in, it **only cooks**.

The edge of a frontier model is **not** "only it can do this." Cheaper models are good.
The edge is **round-collapse**: it one-shots what Sonnet/Opus reach only after N rounds of
iterate → review → fix. So the unit of value is *rounds eliminated × ceiling raised*, and it
applies to **everything** — code, design/UI, sales copy, marketing planning, architecture —
not just hard engineering.

Therefore: do ALL the cheap, slow work (diagnosis, selection, sequencing, acceptance
criteria, repro, test scaffolds) NOW on cheap models. Produce execution-ready packets.
When the frontier model returns, fire this same loop in execute-mode and it **straight-executes
with zero planning tax.**

## One adaptive loop, two modes

This skill is a single loop. It detects whether the frontier model is available and branches:

```
detect frontier availability
 ├─ UNAVAILABLE → PLAN-MODE   (any model: diagnose → verify → packet → rank → write waves)
 └─ LIVE        → EXECUTE-MODE (frontier: next unblocked wave → run packets → gates → pause)
```

### Availability detection (in priority order)
1. **Sentinel file** `~/.claude/.fable-live` exists and contains `live` → LIVE. (Operator flips this
   the moment Fable returns: `echo live > ~/.claude/.fable-live`. Remove it → back to plan-mode.)
2. **Config override** `mode: "plan" | "execute"` in `config.json` forces a mode (for testing).
3. **Probe fallback**: attempt one cheap call to the configured `frontier_model`; on auth/availability
   error → PLAN-MODE. (Never assume LIVE without a positive signal — defaulting to plan is safe;
   defaulting to execute on the hardest tasks is not.)

Default when ambiguous = **PLAN-MODE**. Planning is +EV even if the frontier never returns:
the same queue runs on Opus/Sonnet, just slower.

## Generic core vs adapter (this is the public lead magnet)

The CORE is repo-agnostic — it detects what exists and works for any Claude Code user.
Per-machine specifics live in `config.json` (gitignored); ship `config.example.json`.

`config.json` keys:
- `frontier_model` (default `claude-fable-5`), `plan_model` (default `claude-opus-4-8`),
  `bulk_model` (`claude-sonnet-4-6`)
- `mission_path` — where to write the queue (default `./fable-queue/`; Sigma adapter points it at
  `~/.commandboard/missions/fable-5-prep/`)
- `sweep_surface[]` — repos to diagnose `{name, path}`. If empty, `lib/detect.sh` auto-discovers
  git repos under the cwd and common roots.
- `audit_tools[]` — diagnosis tools to fan out. If empty, `lib/detect.sh` reports which of the known
  set are installed (degrades gracefully to grep/test when none).
- `hard_constraints[]`, `quality_gates{}` — copied into every mission the loop writes.

Detect-what-exists means a stranger installs the skill, runs it on their own repo with zero
Sigma assumptions, and gets a ranked queue. The Sigma adapter is just a richer `config.json`.

---

## PLAN-MODE algorithm

Goal: turn 7 sprawling repos × every domain into a small, ruthlessly-ranked, execution-ready
queue. The leverage is **selection + execution-readiness**, NOT "find hard work" (the board
already has 1000+ todos). A 500-item dump wastes the frontier as badly as never prepping.

For each repo in `sweep_surface`, fan out diagnosis across domains. Use the richest installed
tool per lens; fall back to grep/test when absent:

| Lens | Tool (if present) | Looks for |
|---|---|---|
| Security / blast-radius | `/audit:security-audit`, `owasp-*` skills | auth, money-movement, secrets, injection |
| Tech debt / simplification | `/audit:tech-debt-audit`, `audit:simplify`, `reducing-entropy` | tangled code, dead paths, duplication |
| Performance | `/audit:performance-check`, `performance-patterns` | hot paths, N+1, cold compiles |
| Correctness gaps | `audit:holes`, `audit:gap-analysis`, `exhaustive-audit` | missing cases, stubs, TODO/NotImplemented |
| Design / UI | `audit:ui-healer`, `design-taste`, `ux-psychology-pro` | slop UI, a11y, taste ceiling |
| Copy / marketing | `copywriting`, `marketing-psychology`, `hormozi-frameworks` | weak offers, flat sales copy |
| Architecture / features | `senior-architect`, `architecture-patterns` | net-new high-leverage features |

### The packet (one task = one execution-ready unit)
Every queued item MUST be executable with zero re-planning. Schema (superset of your wave-task
format) — write into `wave-*.json`:

```json
{
  "id": "fp-<repo>-<n>",
  "title": "imperative, specific",
  "domain": "security|techdebt|perf|correctness|design|copy|marketing|architecture|feature",
  "working_directory": "/abs/path/to/repo",
  "files": ["concrete/paths/to/touch"],
  "operation": "exactly what to do — find/replace, or a precise spec a one-shot can execute",
  "reason": "why this matters (the round-collapse / value / risk justification)",
  "acceptance": "the done-state in one sentence",
  "machine_check": "a shell command whose output proves done (e.g. grep -c returns 0, test passes)",
  "expect": "expected machine_check output",
  "rounds_saved": 0,            // est. iterate→fix rounds a cheaper model would need
  "ceiling_lift": "low|med|high", // how much higher the frontier's output ceiling is here
  "score": 0.0,                 // computed — see ranking
  "blocked_by": []              // packet ids that must land first
}
```

### Adversarial verification of findings (NON-NEGOTIABLE — June-9 lesson)
~25% of raw audit-agent findings fail verification (stale paths, already-fixed, wrong). Before a
finding becomes a packet, a SECOND independent agent must confirm it against current code
(`adversarial-verify-fanout`). Default the verifier to "reject unless it can reproduce the problem
on disk right now." Phantom work in the queue burns the frontier on nothing.

### Ranking (the global order)
`score = w_qual·QUALIFY + w_val·VALUE + w_risk·RISK`
- **QUALIFY (round-collapse, the entry ticket)** = normalize(`rounds_saved`) × ceiling_lift weight.
  If QUALIFY ≈ 0 (a cheaper model one-shots it too) → **drop from the Fable queue**, route to a
  normal board card. This is the filter that makes the queue valuable.
- **VALUE** = business impact (revenue / retention / launch-blocking on a main product).
- **RISK** = blast radius (money-movement, auth, security, data, live systems).
- Weights in `config.json` (`scoring.weights`), default `{qual: 0.5, value: 0.3, risk: 0.2}`.

Sort packets desc by `score` across ALL repos → that global order becomes the waves.

### Wave assembly
- Group ranked packets into waves of coherent, independently-shippable work; respect `blocked_by`.
- Wave 1 = highest global score AND lowest cross-dependency (fastest proof when Fable lands).
- Write `mission.json` (north_star, hard_constraints, quality_gates, `waves[]` index) + one
  `wave-*.json` per wave. Re-runnable: a second plan-mode pass updates scores and re-sequences
  without duplicating already-queued packets (dedup by `id` / title+file signature).

PLAN-MODE output = a populated `fable-5-prep` mission + a one-screen `QUEUE-SUMMARY.md`
(top packets, per-repo counts, total est. rounds_saved) for the operator and the reel.

### Orchestration notes (hard-won — encode these)
- **One diagnosis agent per product**, fanned in parallel. The agent MAY use internal sub-lenses
  (security / design / copy / perf …), but it MUST merge their kept packets into its single
  `_diagnosis/<Product>.json` *before it finishes* — never leave merging to a parent. Sub-lenses
  writing the same path concurrently race and silently lose packets.
- **The agent's prose summary is NOT the artifact.** Agents reliably *report* findings and
  unreliably *write files*. Treat `_diagnosis/<Product>.json` as the source of truth; the
  orchestrator verifies each file exists + parses before assembling, and reconstructs from the
  returned summary if an agent skipped the write.
- **Assembly is deterministic, not an agent.** Run `lib/assemble.py` to score, globally rank, and
  write `wave-*.json` + `QUEUE-SUMMARY.md` + the mission `waves[]`. It's idempotent — re-run as each
  product lands; the queue refines in place. Never hand-rank.
- **Watchdog the fan-out** (liveness ≠ file mtime): poll `_diagnosis/*.json` + the agents' rest
  state; an agent at rest with no file means re-message it to write, or reconstruct from its summary.

---

## EXECUTE-MODE algorithm (frontier model live)

For each unblocked wave in order:
1. Load the wave's packets. For each packet, the **frontier model executes directly** —
   design/copy/marketing packets run ON the frontier, never re-delegated to Opus subagents
   (taste/quality is the product; see house doctrine).
2. After each packet: run `machine_check`; it must equal `expect`. Run **tier-1** gate
   (banned-marker scan + targeted tests on touched files). Commit per the operator's branch
   policy (main-only unless a repo opts into dev-flow).
3. At the **wave boundary**: run **tier-2** — the full 7-gate `sprint-pipeline` over the wave diff
   (anti_slop, ui_validation [frontend only], devils_advocate, gap_analysis to 2 clean rounds,
   qa_verification, cross_model_review, greptile_score). Never hand-type a gate result.
4. **PAUSE** with a PASS/MISS/SKIP report per packet + evidence. Wait for the operator's nod
   before the next wave. A failed wave gate → cards to `review`, not silently green.

### Hard rails (always on, both modes — copied into mission.hard_constraints)
- **NEVER touch trading**: no edits to order/execution/broker/killswitch paths; check
  `~/.donna/killswitch.json` is untouched; trading CLIs/automations are off-limits.
- **Archive, never delete**: deletion is the only operator gate — move to `_archive/`, never `rm`.
- **Branch policy = main-only** unless the repo has `.sigma/dev-flow`; never `git checkout -b`
  without the `branch-ok:` sentinel.
- **Verify, don't assert**: every "done" carries its `machine_check` output. No green-on-broken-build.
- **Watchdog**: liveness ≠ file mtime — poll deliverable files + `ps`, not the completion signal alone.

---

## Run it

- `Skill(fable-prep)` with no args → detect mode and proceed.
- "plan" / "diagnose" → force PLAN-MODE (populate/refresh the queue).
- "execute" / "fable night" → force EXECUTE-MODE (requires the sentinel or `--force-execute`).
- "status" → print `QUEUE-SUMMARY.md` + which wave is next.

First run on a fresh machine: `lib/detect.sh` writes a starter `config.json` from what it finds,
then PLAN-MODE produces the first queue. That first queue + its summary is the reel.
