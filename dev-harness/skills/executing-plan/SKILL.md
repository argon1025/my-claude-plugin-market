---
name: executing-plan
description: Use when implementing an approved plan snapshot in .harness/workspace/progress/{slug}/plan.md — typically a fresh session after planning ("계획 실행", "플랜 실행", "execute the plan").
---

Execute the approved plan exactly. The plan is the contract — deviations go back to the user.

## Pre-code gate (mandatory, in order)

1. Resolve `{branch-slug}` from the current branch. Read `.harness/workspace/progress/{slug}/plan.md` in full, plus `feedback.md` if present. No plan.md → stop and ask; never improvise a plan.
2. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wiki_index.py"` from the project root. Before writing any code, read:
   - every doc in the plan's required-reading list,
   - every doc whose `scope` matches files the plan touches — including broad-scope convention/style docs (a scope like `src/**` matches every code task): never skip them as "generic".

   Write code in the idiom these docs and the surrounding code establish.

## Execution loop

- Follow the plan's commit breakdown in order: one task → verify → one commit (norms and feedback grammar: the session-injected dev-harness guide).
- Reality contradicts the plan (API shape, missing dependency, failed assumption) → stop, report evidence, get a decision. Agreed deviation → append `## Re-plan YYYY-MM-DD` to plan.md, then continue.
- Append feedback.md entries as facts surface — at the latest before the commit that uses them.

## Done

All planned commits landed and verify green → report per-commit results. PR creation is out of scope — only on user request.
