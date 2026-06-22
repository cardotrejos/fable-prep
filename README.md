# fable-prep

**Stage your hardest work now. One-shot it the moment your best model arrives.**

Your most capable model is the chef you can only book for a few hours — and the booking may
turn metered the instant it's back. You don't make that chef read the menu. You prep every
station so it *only cooks*.

The edge of a frontier model isn't "only it can do this." Cheaper models are good. The edge is
**round-collapse**: it one-shots what they reach only after rounds of iterate → review → fix.
So you do the slow, cheap work — diagnosis, selection, sequencing, acceptance criteria, test
scaffolds — *now*, on a cheaper model. You produce execution-ready packets. When the frontier
model returns, you fire one loop and it **straight-executes with zero planning tax.**

## One loop, two modes

```
detect frontier availability
 ├─ UNAVAILABLE → PLAN-MODE    diagnose repos → adversarially verify → rank → write a wave queue
 └─ LIVE        → EXECUTE-MODE  next wave → run packets → tiered gates → pause for your nod
```

It flips automatically on a sentinel file. No frontier access yet? It plans. Frontier live?
It ships. Same command either way.

## What makes the queue worth more than a TODO list

- **Ruthless selection, not a dump.** A 500-item pile wastes a scarce model as badly as no prep.
  Each task is scored by *rounds saved × ceiling lift*; anything a cheaper model one-shots too is
  dropped from the queue.
- **Cross-domain.** Code, design/UI, sales copy, marketing — anywhere a frontier model collapses
  rounds, not just hard engineering.
- **Execution-ready packets.** Concrete files, exact operation, an acceptance criterion, and a
  `machine_check` shell oracle that *proves* done. No re-planning on expensive time.
- **Findings are adversarially verified** before they enter the queue — no phantom work.
- **Safety rails built in.** Never touches money/trading paths, archives instead of deleting,
  respects your branch policy, gates every commit, pauses at each wave boundary.

## Install

```bash
git clone https://github.com/Dallionking/fable-prep ~/.claude/skills/fable-prep
cp ~/.claude/skills/fable-prep/config.example.json ~/.claude/skills/fable-prep/config.json
bash ~/.claude/skills/fable-prep/lib/detect.sh --init   # auto-discovers your repos + audit tools
```

## Use

```
/fable-prep            # detect mode and go
/fable-prep plan       # force diagnosis → refresh the queue
/fable-prep execute    # force execution (needs the live sentinel)
/fable-prep status     # show the queue summary + next wave
```

Configure your models, repos, and rails in `config.json`. The core is repo-agnostic and
detects what exists — bring your own stack.

---

*Built the way the June 2026 harness-optimization was: one frontier pass, a real before/after
report, and a skill anyone can install.*
