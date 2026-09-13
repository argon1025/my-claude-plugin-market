#!/bin/bash
# 작업 기록 규약(rules/agent-guide.md)과 현재 브랜치 워크스페이스 현황을 세션 컨텍스트로 주입한다.
# hooks.json의 SessionStart에 matcher가 없어 startup·resume·clear·compact 모두에서 다시 돈다.
# slug는 여기서 계산해 값으로 넘기고, 기존 feedback.md는 상한(4,000바이트) 안에서 함께 주입한다.
# 브랜치 기반 slug 규칙은 git 저장소 밖에서 의미가 없으므로 그 경우 조용히 끝낸다.
set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

BRANCH="$(git -C "$PROJECT_DIR" branch --show-current 2>/dev/null || true)"
case "$BRANCH" in
  ""|main|master|develop) SLUG="" ;;
  *) SLUG="${BRANCH//\//-}" ;;
esac

python3 - "${CLAUDE_PLUGIN_ROOT}" "$PROJECT_DIR" "$SLUG" <<'PY' 2>/dev/null || exit 0
import json
import os
import sys

plugin_root, project_dir, slug = sys.argv[1], sys.argv[2], sys.argv[3]
BUDGET = 4000

with open(os.path.join(plugin_root, "rules", "agent-guide.md"), encoding="utf-8") as handle:
    guide = handle.read().strip().replace("{PLUGIN_ROOT}", plugin_root)

lines = ["", "## 현재 워크스페이스", ""]
body = ""

if slug:
    lines.append(f"- **slug**: `{slug}` (브랜치명 기준)")
    workspace = os.path.join(project_dir, ".ai-docs", "workspace", slug)
    plan_path = os.path.join(workspace, "plan.md")
    feedback_path = os.path.join(workspace, "feedback.md")

    if os.path.isfile(plan_path):
        lines.append("- **plan.md**: 있음 — 코드를 고치기 전에 `/plan-workflow:execute`를 로드함")
    else:
        lines.append("- **plan.md**: 없음")

    if os.path.isfile(feedback_path):
        with open(feedback_path, encoding="utf-8") as handle:
            text = handle.read().strip()
        entries = text.split("\n- `")
        title, items = entries[0], ["- `" + e for e in entries[1:]]
        if len(text.encode("utf-8")) <= BUDGET:
            lines.append(f"- **feedback.md**: {len(items)}항목, 전문 아래")
            body = text
        else:
            kept, used = [], len(title.encode("utf-8"))
            for item in reversed(items):
                size = len(item.encode("utf-8")) + 1
                if used + size > BUDGET:
                    break
                kept.insert(0, item)
                used += size
            skipped = len(items) - len(kept)
            lines.append(f"- **feedback.md**: {len(items)}항목 중 최근 {len(kept)}항목 아래 (앞의 {skipped}항목 생략, 전문은 파일 참조)")
            body = "\n".join([title] + kept)
    else:
        lines.append("- **feedback.md**: 없음")
else:
    lines.append("- **slug**: 미확정 — 기본 브랜치이거나 detached HEAD이므로 첫 기록 시 작업 주제의 kebab-case 2~4단어로 폴더를 만들고 세션 안에서 바꾸지 않음")

context = guide + "\n" + "\n".join(lines)
if body:
    context += "\n\n" + body

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context,
    }
}, ensure_ascii=False))
PY
