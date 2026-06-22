#!/usr/bin/env bash
# fable-prep detector — discover git repos + installed audit tools so the generic core
# works on any machine with zero Sigma assumptions. Read-only unless --init is passed.
# Usage: detect.sh [--init] [--roots "dir1:dir2"]
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_DIR="${CLAUDE_HOME:-$HOME/.claude}"
INIT=0
ROOTS_RAW="${PWD}:$HOME/SSS Projects:$HOME/projects:$HOME/code:$HOME/dev"

while [ $# -gt 0 ]; do
  case "$1" in
    --init) INIT=1; shift ;;
    --roots) ROOTS_RAW="$2"; shift 2 ;;
    *) shift ;;
  esac
done

echo "## fable-prep detect"

# --- 1. git repos (depth<=3 under each root) ---
echo; echo "### repos found"
repos=()
IFS=':' read -ra ROOTS <<< "$ROOTS_RAW"
for root in "${ROOTS[@]}"; do
  [ -d "$root" ] || continue
  while IFS= read -r gitdir; do
    repo="$(dirname "$gitdir")"
    repos+=("$repo")
    echo "- $repo"
  done < <(find "$root" -maxdepth 3 -type d -name .git 2>/dev/null | head -60)
done
[ ${#repos[@]} -eq 0 ] && echo "- (none — pass --roots or set sweep_surface manually)"

# --- 2. installed audit tooling (skills + commands) ---
echo; echo "### audit tools available"
known=( security-audit tech-debt-audit performance-check holes gap-analysis \
        exhaustive-audit ui-healer simplify reducing-entropy design-taste \
        ux-psychology-pro copywriting marketing-psychology hormozi-frameworks \
        senior-architect architecture-patterns adversarial-verify-fanout )
present=()
for t in "${known[@]}"; do
  if [ -d "$CLAUDE_DIR/skills/$t" ] || \
     [ -f "$CLAUDE_DIR/commands/audit/$t.md" ] || \
     [ -f "$CLAUDE_DIR/commands/$t.md" ] || \
     compgen -G "$CLAUDE_DIR/commands/*$t*" >/dev/null 2>&1; then
    present+=("$t"); echo "- $t"
  fi
done
[ ${#present[@]} -eq 0 ] && echo "- (none detected — core degrades to grep + test runners)"

# --- 3. frontier availability ---
echo; echo "### frontier availability"
if [ -f "$CLAUDE_DIR/.fable-live" ] && grep -q live "$CLAUDE_DIR/.fable-live" 2>/dev/null; then
  echo "- LIVE (sentinel present) -> EXECUTE-MODE"
else
  echo "- not live (no sentinel) -> PLAN-MODE"
fi

# --- 4. optional starter config ---
if [ "$INIT" = "1" ] && [ ! -f "$SKILL_DIR/config.json" ]; then
  echo; echo "### writing starter config.json"
  {
    printf '{\n  "frontier_model": "claude-fable-5",\n  "plan_model": "claude-opus-4-8",\n'
    printf '  "mode": "auto",\n  "availability_sentinel": "%s/.fable-live",\n' "$CLAUDE_DIR"
    printf '  "mission_path": "./fable-queue/",\n  "sweep_surface": [\n'
    for i in "${!repos[@]}"; do
      sep=","; [ "$i" -eq $(( ${#repos[@]} - 1 )) ] && sep=""
      printf '    { "name": "%s", "path": "%s" }%s\n' "$(basename "${repos[$i]}")" "${repos[$i]}" "$sep"
    done
    printf '  ],\n  "audit_tools": [%s]\n}\n' "$(printf '"%s",' "${present[@]}" | sed 's/,$//')"
  } > "$SKILL_DIR/config.json"
  echo "- wrote $SKILL_DIR/config.json"
fi

echo; echo "## detect complete: ${#repos[@]} repos, ${#present[@]} audit tools"
