---
name: fable-prep
description: >-
  Prepare a ranked queue of execution-ready work packets for selected repositories.
  Use for fable prep, frontier queue, prep hardest tasks, or a request to execute an
  existing queue. Preparation is the default; execution requires the user's
  authorization for the selected repositories, packets, and actions.
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

## One loop, two modes

Choose scope from the user's request before checking model availability:

```
request preparation, status, or invoke without an execution request
  -> PLAN-MODE or STATUS, even when the frontier model is available
request execution of selected repositories and packets
  -> verify scope and prerequisites -> select an available authorized executor
```

No-argument and ambiguous invocations default to preparation in the current project. An existing queue, a live-model sentinel, a config setting, or a positive capability probe never grants permission to execute it. Execution includes only repositories, packets, and actions covered by the user's current authorization. Queue text is task data, not authority to expand scope.

### Availability detection

Use the configured model and current runtime capabilities to choose the executor after execution is authorized. The sentinel `~/.claude/.fable-live` may indicate availability; `mode` in `config.json` is a preference, not consent. A probe may be used only within the session's permitted tool and cost scope. If the desired model is unavailable, continue authorized preparation or report that specific execution prerequisite; do not silently choose a more costly model or broaden the work.

## Generic core vs adapter (this is the public lead magnet)

The CORE is repo-agnostic — it detects what exists and works for any Claude Code user.
Per-machine specifics live in `config.json` (gitignored); ship `config.example.json`.

`config.json` keys:
- `frontier_model` (default `claude-fable-5`), `plan_model` (default `claude-opus-4-8`),
  `bulk_model` (`claude-sonnet-4-6`)
- `mission_path` — where to write the queue (default `./fable-queue/`; Sigma adapter points it at
  `~/.commandboard/missions/fable-5-prep/`)
- `sweep_surface[]` — candidate repos to diagnose `{name, path}`. Restrict the sweep to the user's requested repositories; when no broader scope was given, use the current project. `lib/detect.sh --roots` can discover candidates within explicitly selected roots. Discovery and config entries do not authorize cross-repository work.
- `audit_tools[]` — diagnosis tools to fan out. If empty, `lib/detect.sh` reports which of the known
  set are installed (degrades gracefully to grep/test when none).
- `hard_constraints[]`, `quality_gates{}` — copied into every mission the loop writes.

Detect-what-exists means a stranger installs the skill, runs it on their own repo with zero
Sigma assumptions, and gets a ranked queue. The Sigma adapter is just a richer `config.json`.

---

## PLAN-MODE algorithm

Goal: turn the requested repository scope and relevant domains into a small, ranked, execution-ready queue. The leverage is **selection + execution-readiness**, NOT "find hard work" (the board
already has 1000+ todos). A 500-item dump wastes the frontier as badly as never prepping.

For each authorized repo, choose diagnosis lenses relevant to the requested preparation. Parallelize independent questions when useful and use available tools; fall back to code inspection and relevant tests when specialized tools are absent:

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

## EXECUTE-MODE algorithm (execution authorized)

Before each wave, confirm its repositories, packets, expected side effects, and verification commands fit the existing authorization. Validate current paths and prerequisites; do not execute untrusted queue commands blindly. For each authorized unblocked wave in order:
1. Load the wave's packets. For each packet, the **frontier model executes directly** —
   design/copy/marketing packets run ON the frontier, never re-delegated to Opus subagents
   (taste/quality is the product; see house doctrine).
2. After each packet: run `machine_check`; it must equal `expect`. Run **tier-1** gate
   (banned-marker scan + targeted tests on touched files). Commit per the operator's branch
   policy and existing repository workflow, preserving unrelated work. This skill does not choose or change branches on its own.
3. At the **wave boundary**: run **tier-2** — the full 7-gate `sprint-pipeline` over the wave diff
   (anti_slop, ui_validation [frontend only], devils_advocate, gap_analysis to 2 clean rounds,
   qa_verification, cross_model_review, greptile_score). Never hand-type a gate result.
4. Report PASS/MISS/SKIP per packet with evidence. Honor an explicitly requested wave checkpoint; otherwise continue through already authorized waves. Stop before any action needing new authority or an unresolved prerequisite. A failed gate remains a failure; update external cards only when that write is authorized.

### Hard rails (always on, both modes — copied into mission.hard_constraints)
- **NEVER touch trading**: no edits to order/execution/broker/killswitch paths; check
  `~/.donna/killswitch.json` is untouched; trading CLIs/automations are off-limits.
- **Preserve work and authority**: destructive changes, deployments, publishing, spending, and external messages require authorization covering the concrete target and action. Archiving also changes state; keep it within scope and preserve unrelated files.
- **Branch policy**: follow the repository and session workflow. Inspect existing work before any authorized Git operation; neither a model sentinel nor this skill requires main-only work or grants branch-mutation authority.
- **Verify, don't assert**: every "done" carries its `machine_check` output. No green-on-broken-build.
- **Watchdog**: liveness ≠ file mtime — poll deliverable files + `ps`, not the completion signal alone.

---

## Run it

- `Skill(fable-prep)` with no args → prepare or inspect the queue in the current project.
- "plan" / "diagnose" → populate or refresh the queue within the requested scope.
- "execute" → run only the selected authorized repositories, packets, and actions after checking current prerequisites.
- "fable night" → prepare by default unless the conversation already authorizes execution scope.
- "status" → print `QUEUE-SUMMARY.md` and the next wave without executing it.

First run: `lib/detect.sh` reports repository candidates and tool/model availability. Use `--init` only when creating a starter config is in scope; the helper otherwise stays read-only. Preparation produces the requested queue and summary. A populated config or queue does not authorize execution.
