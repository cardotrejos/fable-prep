#!/usr/bin/env python3
"""fable-prep assembly — read per-product diagnosis packets, score, globally rank,
and emit the wave queue + QUEUE-SUMMARY.md. Idempotent: re-run as more products land.

Usage: assemble.py [--mission-dir DIR]
Reads DIR/_diagnosis/*.json (each a list of packets), writes DIR/wave-*.json,
DIR/QUEUE-SUMMARY.md, and updates DIR/mission.json waves[].
"""
import json, sys, glob, os
from pathlib import Path

LEVEL = {"low": 0.34, "med": 0.67, "high": 1.0}
WEIGHTS = {"qual": 0.5, "value": 0.3, "risk": 0.2}

def lvl(x): return LEVEL.get(str(x).lower(), 0.5)

def score(p):
    rounds_norm = min(float(p.get("rounds_saved", 0)) / 5.0, 1.0)
    qualify = 0.5 * rounds_norm + 0.5 * lvl(p.get("ceiling_lift"))
    s = WEIGHTS["qual"] * qualify + WEIGHTS["value"] * lvl(p.get("value")) + WEIGHTS["risk"] * lvl(p.get("risk"))
    return round(s, 3), round(qualify, 3)

def wave_of(s):
    if s >= 0.80: return 1
    if s >= 0.70: return 2
    return 3

WAVE_TITLE = {
    1: "Critical security, money & revenue integrity",
    2: "High-leverage correctness, design & copy",
    3: "Hardening, resilience & tech-debt",
}

def product_of(packet_id):
    # fp-<product>-... -> product token
    parts = packet_id.split("-")
    return parts[1] if len(parts) > 2 else "unknown"

def main():
    mdir = Path(sys.argv[sys.argv.index("--mission-dir") + 1]) if "--mission-dir" in sys.argv \
        else Path(__file__).resolve().parents[0]
    if not (mdir / "_diagnosis").exists():
        # fall back to a fable-queue/ directory next to the skill
        mdir = Path.home() / "fable-queue"
    ddir = mdir / "_diagnosis"

    packets = []
    files = sorted(glob.glob(str(ddir / "*.json")))
    for f in files:
        if "copy" in os.path.basename(f).lower():
            continue
        try:
            data = json.load(open(f))
        except Exception as e:
            print(f"WARN: skip {f}: {e}", file=sys.stderr); continue
        for p in data:
            s, q = score(p)
            p["_score"], p["_qualify"], p["_product"] = s, q, product_of(p.get("id", "fp-unknown-0"))
            if q < 0.15:  # round-collapse floor — drop to a normal board card
                print(f"DROP (qualify<0.15): {p.get('id')}", file=sys.stderr); continue
            packets.append(p)

    packets.sort(key=lambda p: p["_score"], reverse=True)
    for p in packets:
        p["_wave"] = wave_of(p["_score"])

    # write wave files
    waves_index = []
    for w in (1, 2, 3):
        tasks = [p for p in packets if p["_wave"] == w]
        if not tasks:
            continue
        wf = mdir / f"wave-{w}.json"
        json.dump({
            "wave": w,
            "title": WAVE_TITLE[w],
            "task_count": len(tasks),
            "tasks": tasks,
        }, open(wf, "w"), indent=2)
        waves_index.append({"id": w, "title": WAVE_TITLE[w], "wave_file": f"wave-{w}.json",
                            "task_count": len(tasks),
                            "products": sorted({p["_product"] for p in tasks})})

    # update mission.json waves[]
    mj = mdir / "mission.json"
    if mj.exists():
        m = json.load(open(mj))
        m["waves"] = waves_index
        m["status"] = f"queue assembled: {len(packets)} packets across {len(set(p['_product'] for p in packets))} products diagnosed"
        json.dump(m, open(mj, "w"), indent=2)

    # QUEUE-SUMMARY.md
    by_prod = {}
    total_rounds = 0
    for p in packets:
        by_prod[p["_product"]] = by_prod.get(p["_product"], 0) + 1
        total_rounds += int(p.get("rounds_saved", 0))
    lines = []
    lines.append("# Fable-5 Prep — Queue Summary\n")
    lines.append(f"**{len(packets)} execution-ready packets** · est. **{total_rounds} iterate→fix rounds collapsed** · "
                 f"products: {', '.join(f'{k} ({v})' for k,v in sorted(by_prod.items()))}\n")
    lines.append("Score = 0.5·round-collapse + 0.3·value + 0.2·risk. Fire `/fable-prep execute` when Fable is live.\n")
    for w in (1, 2, 3):
        tasks = [p for p in packets if p.get("_wave") == w]
        if not tasks:
            continue
        lines.append(f"\n## Wave {w} — {WAVE_TITLE[w]}  ({len(tasks)})\n")
        lines.append("| # | score | product | domain | rounds | title |")
        lines.append("|---|---|---|---|---|---|")
        for i, p in enumerate(tasks, 1):
            lines.append(f"| {i} | {p['_score']} | {p['_product']} | {p.get('domain','')} | "
                         f"{p.get('rounds_saved','')} | {p.get('title','')[:78]} |")
    (mdir / "QUEUE-SUMMARY.md").write_text("\n".join(lines) + "\n")

    print(f"OK: {len(packets)} packets, {len(waves_index)} waves, {total_rounds} rounds collapsed")
    print(f"  -> {mdir/'QUEUE-SUMMARY.md'}")

if __name__ == "__main__":
    main()
