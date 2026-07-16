---
name: create-pull-request
description: Use when a finished feature branch needs a GitHub pull request into the repo's base branch ("PR 생성", "PR 올려줘") — handles push, base-branch resolution, reviewers, PR body.
---

Requires GitHub CLI: `gh auth status` must succeed; not authenticated → stop.

Open a PR for the current feature branch. Local `origin` may be a personal fork; `gh` detects the fork's upstream (`parent`) and targets it automatically.

## Guardrails

- Base branch policy: `develop` if the target repo has one, else the repo's default branch. Never silently retarget once a base is chosen — different base → confirm with the user first.
- Never invent PR context absent from the git history or the diff. If the 배경 cannot be derived from them, ask the user.
- Reviewers not derivable from recent PRs → ask the user. Never guess.

## Steps

**1. Gather branch context.** `git branch --show-current`, `git remote -v`, `git log --oneline <base>..HEAD`, `git diff --stat <base>...HEAD` (+ full diff on code paths). Commit messages hold the "why" the diff can't give; still insufficient → ask the user.

**2. Identify the target repo and base.** `gh repo view --json owner,name,parent,defaultBranchRef` — `parent` non-null = origin is a fork, PR targets the parent repo. Base: `gh api repos/<owner>/<repo>/branches/develop` succeeds → `develop`; 404 → `defaultBranchRef`. Ambiguous (e.g. both `develop` and a release-branch flow) → confirm with the user.

**3. Derive reviewers.** `gh pr list --state merged --limit 10 --json number,title,author`, then `gh pr view <n> --json reviews,reviewRequests,body,title` on one or two feature PRs → reviewer **logins** (e.g. `octocat`). `--reviewer` takes logins, not display names. Note the repo's PR conventions (title prefix, language) and match them.

**4. Push the branch.** `git push -u origin <branch>`. Cross-fork PRs are native on GitHub — no push to the parent repo needed. Push rejected → report the raw error, stop.

**5. Create the PR.** Write the body to a scratch file, then `gh pr create --base <base> --title "..." --body-file <scratch> --reviewer <login>[,<login>] [--draft]` (`--draft` only when asked). Fork case: `gh` infers `--head <fork-owner>:<branch>` from the checkout.

Title: `[<TICKET>] <short factual summary>` (ticket = branch name if it is a ticket ID; no ticket → follow the repo's observed title convention).

Body (Korean if the repo's PRs are Korean):

```markdown
## 변경 요약
- <what changed>

## 배경
- <the problem this solves — from commit history; if underivable, ask>

## 변경 내용
- <file/area + what changed and why, one line each>

## 호환성
<backward-compat / impact, if relevant>

## 검증
- <build, type-check, manual steps>

## 주요 변경 파일
- <key paths — drop if 변경 내용 already named every file>
```

Tables are fine for listing facts; keep the sentence above a table to one line.

**6. Verify.** `gh pr view --json url,baseRefName,headRefName,reviewRequests` → confirm base branch, reviewers attached, source branch correct. Report the `url` value directly.
