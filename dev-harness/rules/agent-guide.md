# dev-harness 운영 규약 (이 프로젝트에 `.harness/`가 있어 활성화됨 — 세션 전체 적용)

`.harness/docs/` = permanent wiki. `.harness/workspace/` = per-branch scratch. Consume both every turn. These rules apply with or without skills — direct work without a plan still accumulates `feedback.md`, and writing-docs harvests feedback-only folders.

Skills: `/dev-harness:init` (scaffold) · `/dev-harness:planning` · `/dev-harness:executing-plan` · `/dev-harness:walkthrough` (interactive branch review) · `/dev-harness:writing-docs` · `/dev-harness:harvest-docs`.

## Wiki lookup (mandatory before code work)

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wiki_index.py"` from the project root. Output lists each doc with its path, `description`, and `scope`. Read every doc whose `description`/`scope` matches the task. Trust wiki over your priors. Query once per session; cache. Never write or edit code before this lookup has run in the session.

## Planning

- Unclear requirements or a non-trivial feature → use plan mode.
- In plan mode — regardless of how it was entered — load the `/dev-harness:planning` skill first, always.
- Never approve a plan for or execute feature work on `develop`/`main`/`master` — create the feature branch first.
- On plan approval: copy the approved plan verbatim to `.harness/workspace/progress/{branch-slug}/plan.md` and commit it immediately (with `feedback.md` if any) as the branch's first commit — the snapshot must be reachable from other worktrees/sessions.
- The planning session ends at that commit. Implementation runs in a fresh session via the `/dev-harness:executing-plan` skill — never implement in the planning session.
- Re-planning: never delete the snapshot — append a `## Re-plan YYYY-MM-DD` section.

## Execution norms

- 1 Task = 1 commit. Conventional Commits.
- `--no-verify` and skipping tests: forbidden.
- Verification fails → stop and report. No retry loops, no workarounds.
- Ambiguity, missing dependency, or a decision outside the agreed plan → stop and ask. Never guess.

## Workspace lifecycle

`branch-slug` = `git branch --show-current` with `/` replaced by `-`. `.harness/workspace/progress/{branch-slug}/` holds `feedback.md` + `plan.md` (+ any skill artifacts). Folder name is the only metadata — files carry no frontmatter, no timestamps.

- After the branch is merged, `/dev-harness:writing-docs` harvests feedback into the wiki and moves the whole folder to `done/` — that move is writing-docs' job only.
- `done/` is never deleted (audit + relearning archive).

## Feedback append (feature branches only)

Skip when current branch is `develop`/`main`/`master`. No branch name (detached HEAD) → create or return to the feature branch before appending.

Path: `.harness/workspace/progress/{branch-slug}/feedback.md`. Create folder/file if absent. Append-only — never modify or delete prior entries.

Record only entries that pass the surprise test: an agent who has already read the relevant code would still act wrongly — or burn a debugging round — without this sentence. Every entry must fit one of these types (fits none → do not record):

- why — rationale/trade-off behind a choice (the choice is visible in code; the reason is not)
- correction — a prior belief, doc, or assumption that turned out wrong, and the corrected fact
- constraint — business/domain/infra rule the code cannot reveal, including external-library traps
- context — scope boundaries and follow-ups agreed with the user

Do not record: restatements of what a single file plainly shows, this-task-only instructions, self-improvement notes, facts already in the wiki.

Timing: append as soon as such a fact surfaces — at the latest before the commit that uses it, and include the append in that commit. An uncommitted append is invisible to other machines/worktrees and silently dropped at harvest. Before creating a PR (or declaring the branch merge-ready), review the branch once, append anything missed, and commit those appends too.

Entry format (strict — parsed by `/dev-harness:writing-docs`):

```
- {Self-contained declarative fact. Scope explicit. Not conversational.}
  - evidence: {code path}     # optional
  - url: {external url}       # optional
- {next fact}
```

Top-level `- ` bullet = entry boundary. Sub-bullets allowed only as `evidence:` or `url:`. File order = time order, oldest first. State the applied scope (product, environment, code path) in the fact itself — an unscoped fact reads as global.

## Do not

- Do not edit `.harness/docs/` directly. Wiki updates happen only via `/dev-harness:writing-docs` (per-branch) or `/dev-harness:harvest-docs` (periodic audit).
- Do not modify or delete prior `feedback.md` entries.
