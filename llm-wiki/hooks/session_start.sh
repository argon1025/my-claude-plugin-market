#!/bin/bash
# 위키 규약(rules/agent-guide.md)과 문서 목록(공통 + 현재 프로젝트)을 세션 컨텍스트로 주입한다.
# hooks.json의 SessionStart에 matcher가 없어 startup·resume·clear·compact 모두에서 다시 돈다.
# 어떤 실패에서도 종료 코드 0으로 끝난다 — 0이 아닌 값을 내면 주입이 조용히 사라진다.
set -uo pipefail

WIKI="${LLM_WIKI_ROOT:-$HOME/.ai-docs/wiki}"
PLUGIN="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"

command -v python3 >/dev/null 2>&1 || exit 0

if [ ! -d "$WIKI/knowledge" ]; then
  python3 -B -c 'import json,sys;print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":sys.argv[1]}},ensure_ascii=False))' \
    "LLM-WIKI: 위키가 $WIKI 에 없음 — /llm-wiki:init 으로 clone 하거나 새로 만들 것" 2>/dev/null
  exit 0
fi

# 원격 동기화. FETCH_HEAD가 60분 넘게 오래됐을 때만 당기고, 3초 안에 안 끝나면 이전 사본으로 간다.
# 세션 시작을 붙잡지 않는 것이 최신 목록보다 중요하다.
SYNC_NOTE=""
GIT_DIR="$(git -C "$WIKI" rev-parse --absolute-git-dir 2>/dev/null || true)"
if [ -n "$GIT_DIR" ] && git -C "$WIKI" remote get-url origin >/dev/null 2>&1; then
  FRESH=0
  if [ -f "$GIT_DIR/FETCH_HEAD" ]; then
    MTIME="$(stat -f %m "$GIT_DIR/FETCH_HEAD" 2>/dev/null || stat -c %Y "$GIT_DIR/FETCH_HEAD" 2>/dev/null || echo 0)"
    [ "$(( $(date +%s) - MTIME ))" -lt 3600 ] && FRESH=1
  fi
  if [ "$FRESH" -eq 0 ]; then
    GIT_TERMINAL_PROMPT=0 git -C "$WIKI" pull --ff-only --quiet >/dev/null 2>&1 &
    PULL_PID=$!
    for _ in 1 2 3 4 5 6; do
      kill -0 "$PULL_PID" 2>/dev/null || break
      sleep 0.5
    done
    if kill -0 "$PULL_PID" 2>/dev/null; then
      SYNC_NOTE="# 위키 동기화 지연 — 아래 목록은 이전 사본. 첫 응답에서 사용자에게 알릴 것"
    elif ! wait "$PULL_PID"; then
      SYNC_NOTE="# 위키 동기화 실패 — 아래 목록은 이전 사본. 첫 응답에서 사용자에게 알릴 것"
    fi
  fi
fi

REMOTE="$(git -C "$PROJECT_DIR" remote get-url origin 2>/dev/null || git -C "$PROJECT_DIR" remote get-url upstream 2>/dev/null || true)"
COMMON_DIR="$(git -C "$PROJECT_DIR" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
TOPLEVEL="$(git -C "$PROJECT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"

python3 -B - "$PLUGIN" "$WIKI" "$REMOTE" "$COMMON_DIR" "$TOPLEVEL" "$SYNC_NOTE" <<'PY' 2>/dev/null || exit 0
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

plugin, wiki, remote, common_dir, toplevel, sync_note = sys.argv[1:7]
sys.path.insert(0, os.path.join(plugin, "scripts"))
import catalog

SOFT_BUDGET = 8000
HARD_BUDGET = 12000

wiki_root = Path(wiki)
knowledge = wiki_root / "knowledge"
catalog_py = os.path.join(plugin, "scripts", "catalog.py")
today = date.today()

guide = (Path(plugin) / "rules" / "agent-guide.md").read_text(encoding="utf-8").strip()
guide = guide.replace("{WIKI_ROOT}", wiki)

registry = catalog.load_json(wiki_root / "registry.json", {})
if not isinstance(registry, dict):
    registry = {}
slug, project = catalog.resolve_repo(registry, remote, common_dir)
repos = registry.get("repos", {}) or {}

# 무인 갱신은 이 파일에 경로가 있는 레포만 처리한다 — 그 레포에서 세션을 한 번 여는 것이 등록이다.
if project and toplevel:
    local = wiki_root / ".local" / "paths.json"
    paths = catalog.load_json(local, {})
    if not isinstance(paths, dict):
        paths = {}
    if paths.get(slug) != toplevel:
        paths[slug] = toplevel
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text(json.dumps(paths, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

header = []
if sync_note:
    header.append(sync_note)

if project:
    siblings = [
        f"{name}: {info.get('summary', '')}".strip().rstrip(":")
        for name, info in sorted(repos.items())
        if info.get("project") == project and name != slug
    ]
    line = f"# 위키 — 프로젝트 {project} · 레포 {slug}"
    if siblings:
        line += " · 형제: " + " · ".join(siblings)
    header.append(line)
elif slug:
    header.append(f"# 미등록 레포 {slug} — /llm-wiki:init 으로 등록하면 프로젝트 목록이 함께 주입됨")

review = wiki_root / "review.md"
if review.is_file():
    try:
        rows = sum(1 for line in review.read_text(encoding="utf-8").splitlines() if line.startswith("- ["))
    except OSError:
        rows = 0
    if rows:
        header.append(f"# 확인 필요 {rows}건 — review.md, /llm-wiki:add 로 처리")

# 낡음 신호의 절반은 문서 날짜가 아니라 커서와 HEAD의 거리다. 커서가 뒤처져 있으면
# 목록이 최신으로 보여도 반영되지 않은 머지가 있다는 뜻이다.
if project:
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

# (라벨, 루트, 본문). 예산을 넘으면 이 목록에서 가장 큰 것부터 한 줄로 접는다.
spaces = []
if (knowledge / "common").is_dir():
    spaces.append(("공통", knowledge / "common", catalog.build(knowledge / "common", today, "공통")))
if project and (knowledge / "projects" / project).is_dir():
    root = knowledge / "projects" / project
    spaces.append((f"프로젝트 {project}", root, catalog.build(root, today, f"프로젝트 {project}")))

others = sorted(name for name in (registry.get("projects", {}) or {}) if name != project)
tail = []
if others:
    tail.append(f"# 다른 프로젝트 {len(others)}개: " + " · ".join(others) + " — 목록은 주입하지 않음")


def assemble():
    blocks = [guide]
    if header:
        blocks.append("\n".join(header))
    blocks.extend(text for _, _, text in spaces)
    blocks.extend(tail)
    return "\n\n".join(blocks)


context = assemble()
folded: set[int] = set()
while catalog.estimate_tokens(context) > HARD_BUDGET:
    candidates = [index for index in range(len(spaces)) if index not in folded]
    if not candidates:
        break
    index = max(candidates, key=lambda i: len(spaces[i][2]))
    folded.add(index)
    label, root, _ = spaces[index]
    count = len(catalog.docs(root))
    spaces[index] = (label, root, f'# {label} {count}건 — python3 "{catalog_py}" --root "{root}" 로 전체 보기')
    context = assemble()

if catalog.estimate_tokens(context) > SOFT_BUDGET:
    context = f"# 위키 목록이 약 {catalog.estimate_tokens(context):,}토큰 — /llm-wiki:audit 로 정리 권장\n\n" + context

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context,
    }
}, ensure_ascii=False))
PY
