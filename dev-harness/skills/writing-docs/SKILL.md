---
name: writing-docs
description: Use when a merged feature branch's workspace artifacts (feedback.md, plan.md, commits) must be harvested into the .harness/docs/ LLM wiki ("문서 수확", "위키 반영", "피드백 정리").
---

Extract non-code facts from a finished branch's workspace artifacts and reflect them in `.harness/docs/` via create, merge, cascade.

Read `${CLAUDE_PLUGIN_ROOT}/references/wiki-rules.md` first — the contract for record/exclude criteria, folder decision, frontmatter, skeletons, and style. It is not auto-loaded.

## Contract

- Run on the integration branch (develop/main/master) after the feature branch is merged and pulled — the wiki SSOT lives there. No base-branch refusal.
- Inputs: `.harness/workspace/progress/{slug}/feedback.md` (primary) + `plan.md` when present + the merged branch's git log. A missing `plan.md` is normal — proceed. Read any other `.md` in the folder too (older archives may hold `brainstorm.md`).
- `.harness/docs/` is a permanent shared asset. No writes before user approval.
- Never record facts absent from the inputs or the diff.

## Steps

1. Resolve the target slug: use the argument if given. Else list `.harness/workspace/progress/*` folders — exactly one → use it; several → ask the user to pick; none → report "no pending workspace", exit.
2. Verify the folder actually merged: `git log --oneline -- .harness/workspace/progress/{slug}/` must be non-empty on the current branch (covers squash merges too). Empty → the workspace never merged (abandoned branch or uncommitted work) — do not harvest; facts about unmerged code must not enter the wiki. Confirm with the user: abandoned → move the folder to `done/{slug}` without harvesting; otherwise stop.
3. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wiki_index.py"` once; cache. Summarize the branch's commits.
4. Extract candidates per the wiki-rules record/exclude lists. For each: decide the folder (shape table), resolve the target file via the cached index (same domain → merge, else new), and mark cascade targets where a new fact changes an existing doc's meaning.
5. Present the candidate table `(fact, folder, path, merge|new, cascade targets)` for approval. Reflect edit/exclude requests, re-confirm; only approved rows proceed. Zero candidates → skip to step 7.
6. Apply per wiki-rules: frontmatter (never write `harvested`), folder skeletons, style. Merge keeps the existing body and adds facts; conflicts → cite source, state both. Cascade = surgical edits on affected sections; meaning changed → refresh `description`, bump `updated`.
7. Move `.harness/workspace/progress/{slug}` → `.harness/workspace/done/{slug}` (whole folder, never delete) — always, including the zero-candidate path. Report the changed-file list. Commit only on user instruction.
