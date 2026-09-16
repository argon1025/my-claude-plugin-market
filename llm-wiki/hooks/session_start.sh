#!/bin/bash
# 위키 규약(rules/agent-guide.md)과 3층(도메인 목록·의존 간선 → 도메인 index.md 본문 →
# 목록(도메인 루트 + 현재 레포))을 세션 컨텍스트로 주입한다.
# hooks.json의 SessionStart에 matcher가 없어 startup·resume·clear·compact·fork 모두에서 다시 돈다.
# 주입은 전 이벤트에서 하고, 원격 pull은 stdin의 source가 startup·resume일 때만 한다 —
# clear·compact는 같은 세션의 재주입이고 fork는 부모가 이미 당겼다.
# 어떤 실패에서도 종료 코드 0으로 끝난다 — 0이 아닌 값을 내면 주입이 조용히 사라진다.
set -uo pipefail

WIKI="${LLM_WIKI_ROOT:-$HOME/.ai-docs/wiki}"
PLUGIN="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"

command -v python3 >/dev/null 2>&1 || exit 0

INPUT=""
[ -t 0 ] || INPUT="$(cat 2>/dev/null || true)"
SOURCE="$(printf '%s' "$INPUT" | python3 -B -c 'import json,sys;print(json.load(sys.stdin).get("source") or "startup")' 2>/dev/null || echo startup)"
[ -n "$SOURCE" ] || SOURCE=startup

# pull 주기. LLM_WIKI_SYNC_MINUTES(분)로 덮어쓰고, 정수가 아니면 기본 10분.
SYNC_MINUTES="${LLM_WIKI_SYNC_MINUTES:-10}"
case "$SYNC_MINUTES" in ''|*[!0-9]*) SYNC_MINUTES=10 ;; esac
SYNC_SECONDS=$(( SYNC_MINUTES * 60 ))

if [ ! -f "$WIKI/registry.json" ]; then
  python3 -B -c 'import json,sys;print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":sys.argv[1]}},ensure_ascii=False))' \
    "LLM-WIKI: 위키가 $WIKI 에 없음 — /llm-wiki:init 으로 clone 하거나 새로 만들 것" 2>/dev/null
  exit 0
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

wiki_root = Path(wiki)
knowledge = wiki_root / "knowledge"
catalog_py = os.path.join(plugin, "scripts", "catalog.py")
today = date.today()

guide = (Path(plugin) / "rules" / "agent-guide.md").read_text(encoding="utf-8").strip()
guide = guide.replace("{WIKI_ROOT}", wiki).replace("{CATALOG_PY}", catalog_py)

registry = catalog.load_json(wiki_root / "registry.json", {})
if not isinstance(registry, dict):
    registry = {}
slug, domain = catalog.resolve_repo(registry, remote, common_dir)
repos = registry.get("repos", {}) or {}

# 무인 갱신은 이 파일에 경로가 있는 레포만 처리한다 — 그 레포에서 세션을 한 번 여는 것이 등록이다.
if domain and toplevel:
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

if domain:
    # 형제 레포는 이름과 문서 건수만 — 목록은 주입하지 않으므로 건수가 "볼 게 있는가"의 유일한 신호다.
    siblings = [
        f"{name} {len(catalog.docs(knowledge / domain / name)) if (knowledge / domain / name).is_dir() else 0}건"
        for name, info in sorted(repos.items())
        if info.get("domain") == domain and name != slug
    ]
    line = f"# 위키 — 도메인 {domain} · 레포 {slug}"
    if siblings:
        line += " · 형제: " + " · ".join(siblings)
    header.append(line)
elif slug:
    header.append(f"# 미등록 레포 {slug} — /llm-wiki:register 로 등록하면 도메인 목록이 함께 주입됨")

# 인박스는 도메인마다 파일 하나다 — 담당자가 다른 두 도메인이 한 파일 끝에 append하면
# 매일 pull --rebase가 충돌한다. 다른 도메인의 건수는 그 도메인 목록처럼 주입하지 않는다.
inbox = wiki_root / "inbox" / f"{domain}.md" if domain else None
if inbox is not None and inbox.is_file():
    try:
        rows = sum(1 for line in inbox.read_text(encoding="utf-8").splitlines() if line.startswith("- ["))
    except OSError:
        rows = 0
    if rows:
        header.append(f"# 확인 필요 {rows}건 — inbox/{domain}.md, /llm-wiki:add 로 처리")

# 낡음 신호의 절반은 문서 날짜가 아니라 커서와 HEAD의 거리다. 커서가 뒤처져 있으면
# 목록이 최신으로 보여도 반영되지 않은 머지가 있다는 뜻이다.
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

# 1층: 도메인 목록과 현재 도메인에 닿는 간선. 전역 index 문서를 저작하지 않고 registry.json과
# 각 도메인 index.md 첫 줄·deps.json에서 파생한다 — 도메인 간 의존은 레포 간 의존의 요약이라
# 세 번째 문서를 두면 같은 사실을 복제하고 갱신 규칙이 하나 더 는다.
domains = sorted(registry.get("domains", {}) or {})
domain_block = ""
if domains:
    head = f"# 도메인 {len(domains)}개"
    if domain:
        head += f" · 현재 {domain}"
    rows = []
    for name in domains:
        index_file = knowledge / name / catalog.INDEX_NAME
        lead = catalog.lead_line(index_file) if index_file.is_file() else "(index.md 없음 — /llm-wiki:register)"
        rows.append(f"- {name} — {lead}" if lead else f"- {name}")
    domain_block = "\n".join([head, *rows])

# 간선은 양방향으로 준다 — 현재 레포를 to로 가진 from이 이번 변경의 파급 대상이고,
# 그 from이 다른 도메인이면 목록이 주입되지 않으므로 여기가 유일한 신호다.
touching: list[tuple[str, str, str]] = []
if domain:
    for edge in catalog.load_edges(wiki_root):
        origin, target = edge.get("from"), edge.get("to")
        if not isinstance(origin, str) or not isinstance(target, str):
            continue
        if not catalog.EDGE_RE.match(origin) or not catalog.EDGE_RE.match(target):
            continue
        if domain not in (origin.split("/", 1)[0], target.split("/", 1)[0]):
            continue
        note = edge.get("note")
        suffix = f" — {note.strip()}" if isinstance(note, str) and note.strip() else ""
        touching.append((origin, target, f"- {origin} → {target}{suffix}"))
    touching.sort(key=lambda item: item[:2])

edge_block = ""
if touching:
    edge_block = "\n".join([
        f"# 의존 간선 {len(touching)}건 · {domain}에 닿는 것 (from → to = from이 to를 호출·참조)",
        *(row for _, _, row in touching),
    ])

# 도메인 지도(index.md)는 목록이 아니라 본문 전체를 주입한다 — 레포 구성·역인덱스가
# 있어야 코드 변경의 파급 레포를 답할 수 있다. 없으면 헤더에 register 안내만 남긴다.
index_block = ""
index_path = knowledge / domain / catalog.INDEX_NAME if domain else None
if domain:
    if index_path.is_file():
        index_body = "\n".join(catalog.body_lines(index_path)).strip()
        index_block = f"# 도메인 {domain} index.md · 약 {catalog.estimate_tokens(index_body):,}토큰\n\n{index_body}"
    else:
        header.append(f"# {domain}/index.md 없음 — /llm-wiki:register")

# 도메인 루트는 레포 폴더를 뺀 평면(shallow), 레포 폴더는 전수. 어떤 예산에서도 줄이지 않는다 —
# 에이전트는 description만으로 문서를 열지 말지 정하므로 목록에서 빠진 문서는 없는 문서가 된다.
spaces = []
if domain and (knowledge / domain).is_dir():
    root = knowledge / domain
    spaces.append(catalog.build(root, today, f"도메인 {domain}", shallow=True))
    if (root / slug).is_dir():
        spaces.append(catalog.build(root / slug, today, f"레포 {slug}"))

def assemble():
    blocks = [guide]
    if header:
        blocks.append("\n".join(header))
    if domain_block:
        blocks.append(domain_block)
    if edge_block:
        blocks.append(edge_block)
    if index_block:
        blocks.append(index_block)
    blocks.extend(spaces)
    return "\n\n".join(blocks)


context = assemble()

# 주입 크기의 유일한 제어 수단은 이 권고 한 줄과 사용자의 문서 정리다. 상한을 넘겼다고
# 목록을 줄이면 누락이 조용히 생기고, 접힘을 푸는 명령을 건너뛰어도 아무 신호가 없다.
if catalog.estimate_tokens(context) > SOFT_BUDGET:
    context = f"# 위키 목록이 약 {catalog.estimate_tokens(context):,}토큰 — /llm-wiki:audit 로 정리 권장\n\n" + context

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context,
    }
}, ensure_ascii=False))
PY
