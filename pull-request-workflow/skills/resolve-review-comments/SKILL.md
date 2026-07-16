---
name: resolve-review-comments
description: Use when applying review comments on a GitHub pull request as the PR author ("리뷰 반영", "코멘트 반영", "리뷰 코멘트 처리", right after a /pull-request-workflow:review-pull-request report) — triages every unresolved comment (AI + human) into 수용/기각/이미 해결 with evidence, fixes accepted ones as commits, then after ONE batch approval pushes and replies to each thread. NOT for reviewing a PR (that is /pull-request-workflow:review-pull-request's job). Requires running inside the target repo's checkout.
argument-hint: "[pr-url]"
---

Requires GitHub CLI: `gh auth status` must succeed; not authenticated → stop.

## Guardrails

- No force-push, ever.
- Verification failure → no push; stop and report — no retry loops, no workarounds.
- Do not create new review findings — reviewing is /pull-request-workflow:review-pull-request's job. Problems noticed while fixing → report only.
- All external actions (push + replies + thread resolution) bundled behind ONE approval per round.
- No silent omissions — rejections, deferrals, skipped verification all reported.
- Same-repo only — PR's owner/repo must match the local checkout (or its `parent` when origin is a fork) → else refuse, point to its checkout.

## Steps

**1. Resolve PR + branch.** Coords: `gh repo view --json owner,name,parent` (origin a fork → PR repo = `parent`). PR: URL arg → parse owner/repo/number, must match local coords else refuse; no arg → `gh pr list --state open --json number,title,author,headRefName` table (번호|제목|작성자|소스 브랜치) → await choice. Current branch must be the PR source branch — else `gh pr checkout <n>` (handles forks, configures the push remote; working tree dirty → stop, report).

**2. Collect unresolved comments.** Inline threads via GraphQL, filter `isResolved: false` (keep BOTH thread `id` — for the resolve mutation — and comment `databaseId` — for REST replies):

```
gh api graphql -f query='query($owner:String!,$repo:String!,$pr:Int!){
  repository(owner:$owner,name:$repo){pullRequest(number:$pr){
    reviewThreads(first:100){nodes{id isResolved path line
      comments(first:50){nodes{databaseId author{login} body}}}}}}}' \
  -f owner=<owner> -f repo=<repo> -F pr=<n>
```

Plus top-level comments: `gh pr view <n> --json comments`. Exclude: resolved threads, threads already closed by a reply, and the anchorless `[AI 코드리뷰]` summary comment.

**3. Triage (ownership).** Examine each comment critically against current HEAD → 수용/기각/이미 해결, evidence mandatory. Rejecting without confirming the code path/behavior is forbidden. Report (한국어) as a table: 코멘트|판정|근거|수정 방향. Then continue to fixes.

**4. Fix accepted items.** One logical unit = one commit (Conventional Commits). Run the project's verification — lint·typecheck·test, whichever exist — and require green. Failure → stop and report.

**5. One batch approval → push + replies.** Ask once: "푸시 + 답글 게시 진행?". On approval: `git push` (gh pr checkout already set the upstream), then per thread reply via `gh api repos/<owner>/<repo>/pulls/<n>/comments/<databaseId>/replies -f body='...'` — 수용 "반영했어요 — <commit sha>" / 기각 근거 1~2줄 / 이미 해결 확인 1줄. After replying to 수용/이미 해결 threads, resolve them so the state is machine-readable for the next review run:

```
gh api graphql -f query='mutation($tid:ID!){
  resolveReviewThread(input:{threadId:$tid}){thread{isResolved}}}' -f tid=<thread-id>
```

Declined → nothing leaves the machine; report local commit state.

**6. Loop handoff.** End with one line: "재검증: `/pull-request-workflow:review-pull-request` 재실행". Loop exits when re-review reports zero Blocker·Bug.
