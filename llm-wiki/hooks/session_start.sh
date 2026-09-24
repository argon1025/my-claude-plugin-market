#!/bin/bash
# 위키 규약(rules/agent-guide.md), 상태 헤더, 그래프 파생 블록(레포 지도 → 현재 레포 기준
# 의존 3묶음), 목록(도메인 루트 + 현재 레포)을 세션 컨텍스트로 주입한다.
# 파생은 scripts/graph.py가 registry.json·deps.json에서 만든다.
#
# hooks.json의 SessionStart에 matcher가 없어 startup·resume·clear·compact·fork 모두에서 다시 돈다.
# 주입은 전 이벤트에서 하고, 원격 pull은 stdin의 source가 startup·resume일 때만 한다 —
# clear·compact는 같은 세션의 재주입이고 fork는 부모가 이미 당겼다.
# 어떤 실패에서도 종료 코드 0으로 끝난다 — 0이 아닌 값을 내면 주입이 조용히 사라진다.
# set -e를 걸지 않는다 — 실패 명령 하나로 주입 전체가 사라진다.
set -uo pipefail

WIKI="${LLM_WIKI_ROOT:-$HOME/.ai-docs/wiki}"
PLUGIN="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"

ALERT='첫 응답에서 사용자에게 알릴 것'

command -v python3 >/dev/null 2>&1 || exit 0

INPUT=""
[ -t 0 ] || INPUT="$(cat 2>/dev/null || true)"
SOURCE="$(printf '%s' "$INPUT" | python3 -B -c 'import json,sys;print(json.load(sys.stdin).get("source") or "startup")' 2>/dev/null || echo startup)"
[ -n "$SOURCE" ] || SOURCE=startup

# pull 주기. LLM_WIKI_SYNC_MINUTES(분)로 덮어쓰고, 정수가 아니면 기본 10분.
SYNC_MINUTES="${LLM_WIKI_SYNC_MINUTES:-10}"
case "$SYNC_MINUTES" in ''|*[!0-9]*) SYNC_MINUTES=10 ;; esac
SYNC_SECONDS=$(( SYNC_MINUTES * 60 ))

emit() {
  python3 -B -c 'import json,sys;print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":sys.argv[1]}},ensure_ascii=False))' "$1" 2>/dev/null
  exit 0
}

if [ ! -f "$WIKI/registry.json" ]; then
  emit "LLM-WIKI: 위키가 $WIKI 에 없음 — /llm-wiki:init 으로 clone 하거나 새로 만들 것"
fi

# 원격 동기화. startup·resume에서 FETCH_HEAD가 주기보다 오래됐을 때만 당기고, 3초 안에 안 끝나면
# 이전 사본으로 간다. 세션 시작을 붙잡지 않는 것이 최신 목록보다 중요하다.
SYNC_NOTE=""
GIT_DIR="$(git -C "$WIKI" rev-parse --absolute-git-dir 2>/dev/null || true)"
if { [ "$SOURCE" = startup ] || [ "$SOURCE" = resume ]; } && [ -n "$GIT_DIR" ] && git -C "$WIKI" remote get-url origin >/dev/null 2>&1; then
  FRESH=0
  if [ -f "$GIT_DIR/FETCH_HEAD" ]; then
    MTIME="$(stat -f %m "$GIT_DIR/FETCH_HEAD" 2>/dev/null || stat -c %Y "$GIT_DIR/FETCH_HEAD" 2>/dev/null || echo 0)"
    [ "$(( $(date +%s) - MTIME ))" -lt "$SYNC_SECONDS" ] && FRESH=1
  fi
  if [ "$FRESH" -eq 0 ]; then
    GIT_TERMINAL_PROMPT=0 git -C "$WIKI" pull --ff-only --quiet >/dev/null 2>&1 &
    PULL_PID=$!
    for _ in 1 2 3 4 5 6; do
      kill -0 "$PULL_PID" 2>/dev/null || break
      sleep 0.5
    done
    if kill -0 "$PULL_PID" 2>/dev/null; then
      SYNC_NOTE="# 위키 동기화 지연 — 아래 목록은 이전 사본. $ALERT"
    elif ! wait "$PULL_PID"; then
      SYNC_NOTE="# 위키 동기화 실패 — 아래 목록은 이전 사본. $ALERT"
    fi
  fi
fi

# fork 워크플로에서 origin은 개인 포크이고 upstream이 정본이다. 노드에는 정본만 적으므로
# upstream을 먼저 본다 — 둘 다 없거나 어긋나도 resolve_repo의 slug 폴백이 받는다.
REMOTE="$(git -C "$PROJECT_DIR" remote get-url upstream 2>/dev/null || git -C "$PROJECT_DIR" remote get-url origin 2>/dev/null || true)"
COMMON_DIR="$(git -C "$PROJECT_DIR" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
TOPLEVEL="$(git -C "$PROJECT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"

python3 -B - "$PLUGIN" "$WIKI" "$REMOTE" "$COMMON_DIR" "$TOPLEVEL" "$SYNC_NOTE" <<'PY' 2>/dev/null || exit 0
import json
import os
import subprocess
import sys
from pathlib import Path

plugin, wiki, remote, common_dir, toplevel, sync_note = sys.argv[1:7]
sys.path.insert(0, os.path.join(plugin, "scripts"))
import catalog
import graph

SOFT_BUDGET = 8000

wiki_root = Path(wiki)
knowledge = wiki_root / "knowledge"
graph_py = os.path.join(plugin, "scripts", "graph.py")

guide = (Path(plugin) / "rules" / "agent-guide.md").read_text(encoding="utf-8").strip()
guide = guide.replace("{WIKI_ROOT}", wiki).replace("{GRAPH_PY}", graph_py)

registry = graph.load_registry(wiki_root)
edges = graph.load_edges(wiki_root)
slug, domain = graph.resolve_repo(registry, remote, common_dir)

# 무인 갱신은 이 파일에 경로가 있는 레포만 처리한다 — 그 레포에서 세션을 한 번 여는 것이 등록이다.
# .local/은 .gitignore 대상이라 clean-tree 판정에 걸리지 않는다.
paths = catalog.load_json(wiki_root / ".local" / "paths.json", {})
if not isinstance(paths, dict):
    paths = {}
if domain and toplevel and paths.get(slug) != toplevel:
    paths[slug] = toplevel
    local = wiki_root / ".local" / "paths.json"
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_text(json.dumps(paths, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

header = []
if sync_note:
    header.append(sync_note)

# 등록 레포의 도메인·slug는 레포 지도 머리글이 말하므로 여기서는 미등록만 알린다.
if slug and not domain:
    header.append(f"# 미등록 레포 {slug} — /llm-wiki:register 로 등록하면 레포 지도·의존이 주입됨")

# 위키가 이 레포를 얼마나 따라왔는지는 커서와 HEAD의 거리로 보인다.
if domain:
    state = catalog.load_json(wiki_root / "state" / f"{slug}.json", {})
    cursor = state.get("cursor") if isinstance(state, dict) else None
    if not cursor:
        header.append("# 커서 없음 — 첫 update가 등록")
    elif toplevel:
        try:
            result = subprocess.run(
                ["git", "-C", toplevel, "rev-list", "--count", f"{cursor}..HEAD"],
                capture_output=True, text=True, timeout=5,
            )
            behind = int(result.stdout.strip()) if result.returncode == 0 else None
        except (OSError, ValueError, subprocess.SubprocessError):
            behind = None
        if behind:
            header.append(f"# 커서 {cursor[:7]} · HEAD보다 {behind}커밋 뒤 — /llm-wiki:update 권장")
        elif behind == 0:
            header.append(f"# 커서 {cursor[:7]} · HEAD와 같음")

# 그래프 블록은 저장된 문서가 아니라 registry.json 노드와 deps.json 간선에서 파생한다.
graph_block = graph.render_session(registry, edges, domain or "", slug, paths)

# 도메인 루트는 레포 폴더를 뺀 평면(shallow), 레포 폴더는 전수. 어떤 예산에서도 줄이지 않는다 —
# 에이전트는 description만으로 문서를 열지 말지 정하므로 목록에서 빠진 문서는 없는 문서가 된다.
spaces = []
if domain and (knowledge / domain).is_dir():
    root = knowledge / domain
    spaces.append(catalog.build(root, f"도메인 {domain}", shallow=True))
    if (root / slug).is_dir():
        spaces.append(catalog.build(root / slug, f"레포 {slug}"))

blocks = [guide]
if header:
    blocks.append("\n".join(header))
if graph_block:
    blocks.append(graph_block)
blocks.extend(spaces)
context = "\n\n".join(blocks)

# 주입 크기의 유일한 제어 수단은 이 권고 한 줄과 사용자의 문서 정리다.
if catalog.estimate_tokens(context) > SOFT_BUDGET:
    context = f"# 위키 목록이 약 {catalog.estimate_tokens(context):,}토큰 — /llm-wiki:audit 로 정리 권장\n\n" + context

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context,
    }
}, ensure_ascii=False))
PY
