---
name: init
description: Use when activating dev-harness in a project without .harness/ ("하네스 초기화", "harness init", "하네스 설정") — scaffolds .harness/docs, workspace/progress, workspace/done with .gitkeep. Idempotent.
---

Scaffold the project-side data directories that dev-harness consumes. The plugin ships rules, skills, and the wiki indexer; each project holds its own wiki (`.harness/docs/`) and branch workspace (`.harness/workspace/`).

## Steps

1. Create these directories at the project root, each with a `.gitkeep` so git tracks them while empty:
   - `.harness/docs/`
   - `.harness/workspace/progress/`
   - `.harness/workspace/done/`
2. Idempotent: never touch anything that already exists (existing docs, workspace folders, files stay as-is); create only what is missing. Report a table of `경로 / 생성 | 이미 존재`.
3. Verify: run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wiki_index.py"` from the project root once — an empty table (headers only) is the expected result for a fresh scaffold; an existing wiki prints its docs.
4. The SessionStart hook injects the operating guide from the next session onward. To apply it in this session immediately, read `${CLAUDE_PLUGIN_ROOT}/rules/agent-guide.md` now and follow it.
5. Commit only on user instruction.
