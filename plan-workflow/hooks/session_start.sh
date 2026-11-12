#!/bin/bash
# 작업 기록 규약 요약(rules/agent-guide.md)과 현재 브랜치의 기록 위치를 세션 컨텍스트로 주입한다.
# hooks.json의 SessionStart에 matcher가 없어 startup·resume·clear·compact 모두에서 다시 돈다.
# 브랜치명에서 대문자 이슈 키(PROJ-123)만 뽑아 그 키가 들어간 폴더를 찾고, 키가 없으면 폴더를 정하지 않는다.
# 기록 본문은 주입하지 않고 파일 유무와 읽기 지시만 알린다.
# 기록 폴더 상위 경로는 config.json의 workspace.root, 안내에 쓰는 플러그인 이름은 plugin.json의 name에서 읽는다.
# git 저장소 밖에서는 조용히 끝낸다.
set -uo pipefail

PLUGIN_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_DIR="$(python3 -c '
import json, os, sys
try:
    event = json.load(sys.stdin)
except (ValueError, TypeError):
    event = {}
print((event.get("cwd") if isinstance(event, dict) else None) or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
')"
git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

PROJECT_DIR="$(git -C "$PROJECT_DIR" rev-parse --show-toplevel)"
BRANCH="$(git -C "$PROJECT_DIR" branch --show-current 2>/dev/null || true)"

python3 - "$PLUGIN_DIR" "$PROJECT_DIR" "$BRANCH" <<'PY' 2>/dev/null || exit 0
import json
import os
import re
import sys

plugin_root, project_dir, branch = sys.argv[1], sys.argv[2], sys.argv[3]

with open(os.path.join(plugin_root, "config.json"), encoding="utf-8") as handle:
    root = json.load(handle)["workspace"]["root"]
with open(os.path.join(plugin_root, ".claude-plugin", "plugin.json"), encoding="utf-8") as handle:
    name = json.load(handle)["name"]
with open(os.path.join(plugin_root, "rules", "agent-guide.md"), encoding="utf-8") as handle:
    guide = (
        handle.read().strip()
        .replace("{PLUGIN_ROOT}", plugin_root)
        .replace("{PLUGIN_NAME}", name)
        .replace("{WORKSPACE_ROOT}", root)
    )

# 소문자 토큰(utf-8, log-4 등)은 이슈 키가 아닌 경우가 많아 대문자 키만 인정한다.
found = re.search(r"(?<![A-Za-z0-9])[A-Z][A-Z0-9]+-\d+(?![A-Za-z0-9])", branch)
lines = ["", "## 현재 워크스페이스", ""]

if found:
    key = found.group(0)
    lines.append(f"- **이슈 키**: `{key}` (브랜치명에서 추출)")
    base = os.path.join(project_dir, root)
    # 이전 규칙으로 만든 폴더(브랜치명 기반, 소문자 키 포함)도 같은 키면 이어 쓴다.
    token = re.compile(rf"(?<![A-Za-z0-9]){re.escape(key)}(?![0-9])", re.IGNORECASE)
    folders = sorted(
        entry for entry in (os.listdir(base) if os.path.isdir(base) else [])
        if token.search(entry) and os.path.isdir(os.path.join(base, entry))
    )
    has_files = False
    for folder in folders:
        files = [f for f in ("plan.md", "feedback.md") if os.path.isfile(os.path.join(base, folder, f))]
        has_files = has_files or bool(files)
        state = "·".join(f"`{f}`" for f in files) + " 있음" if files else "기록 파일 없음"
        lines.append(f"- **기록 폴더**: `{root}/{folder}/` — {state}")
    if not folders:
        lines.append(f"- **기록 폴더**: `{root}/{key}/` — 아직 없으며 첫 기록 때 만듦")
    if has_files:
        lines.append("- **읽기**: 작업을 시작하기 전에 위 폴더의 기록 파일을 읽음")
else:
    lines.append("- **이슈 키**: 브랜치명에 없음 — 요청에 이슈 키가 있으면 그 키로, 없으면 작업 주제의 kebab-case 이름으로 폴더를 정함")
    lines.append(f"- **기록 폴더**: `{root}/{{폴더 이름}}/`")

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": guide + "\n" + "\n".join(lines),
    }
}, ensure_ascii=False))
PY
