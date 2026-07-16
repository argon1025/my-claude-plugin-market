---
name: review-pull-request
description: Use when reviewing a GitHub pull request ("PR 리뷰", "PR 리뷰해줘", PR URL 제시) — PR from open list or pasted URL, per-file review (버그·사이드이펙트 중심; multi-stack TS/React·NestJS·Java/Spring) + falsify pass, Korean findings graded Blocker/Bug/개선, comments posted only after approval; re-run resolves prior AI comments via replies. Reviewer only — applying comments is /pull-request-workflow:resolve-review-comments's job. NOT for the local working diff (/code-review's job). Run inside the target repo's checkout.
argument-hint: "[pr-url]"
---

Requires GitHub CLI: `gh auth status` must succeed; not authenticated → stop.

References (not auto-loaded): `references/checklists/*.md` (Layer 1, subagent-only), `references/subagent-prompts.md` (①review ②falsify ③re-anchor).

## Guardrails

- Post ONLY after explicit approval; never modify code — review only.
- Target = PR snapshot ($REVIEW_SHA); working diff → /code-review. Git side effects: `git fetch` only.
- Strict Focus is a pipeline invariant — never resurrect other-file findings.
- Same-repo only — PR's owner/repo must match the local checkout (or its `parent` when origin is a fork) → else refuse, point to its checkout.
- PR/auth/API errors → report raw error, stop — no guess-retries.
- No silent omissions — report all skips, truncation, anchor downgrades, falsify drops.

## Steps

**1. Resolve repo + PR.** `gh repo view --json owner,name,parent` → coords (origin a fork → PR repo = `parent`). No arg → `gh pr list --state open --json number,title,author,headRefName` table (번호|제목|작성자|소스 브랜치) → await choice. URL → parse owner/repo/number; must match local coords else refuse. Bare number → confirm via list. Never guess.

**2. PR meta.** `gh pr view <n> --json state,baseRefName,headRefName,headRefOid,title,body` + existing threads via GraphQL (dedup·known-issue keys; keep BOTH thread `id` — GraphQL node id — and comment `databaseId` — REST id):

```
gh api graphql -f query='query($owner:String!,$repo:String!,$pr:Int!){
  repository(owner:$owner,name:$repo){pullRequest(number:$pr){
    reviewThreads(first:100){nodes{id isResolved path line
      comments(first:50){nodes{databaseId author{login} body}}}}}}}' \
  -f owner=<owner> -f repo=<repo> -F pr=<n>
```

Plus top-level comments: `gh pr view <n> --json comments`. Any `[AI 리뷰` comment → also step 10.

**3. Diff (local first).** `git fetch origin pull/<n>/head` → REVIEW_SHA=FETCH_HEAD (works for OPEN and MERGED/CLOSED alike — GitHub keeps `refs/pull/<n>/head`); BASE=`git merge-base FETCH_HEAD origin/<baseRefName>` (fetch the base ref first if absent).
- Fetch fail → fallback `gh pr diff <n>`; gate first with `gh pr diff <n> --name-only` + per-file sizes — no server-side truncation, so oversized PRs → uncovered files = 미리뷰, report.
- Files: `git diff --find-renames --name-status $BASE $REVIEW_SHA`; per-file hunks with `-- <path>`; snapshots `git show $REVIEW_SHA:<path>`.

**4. Gate files** (exclusions → 스킵 table + reason): binary/image/font; lockfiles; pure delete/rename; `*.md` (on request); >1,500 changed lines/file (skip+warn); >30 files → ask scope first. Test files ARE reviewed.

**5. Rule discovery** (report header "적용 룰 소스" always, with detected stack):
- Layer 1 (stack detect, once per repo): all files → `checklists/common.md`; `.ts/.tsx/.js/.jsx` + react/next in nearest `package.json` deps → + `typescript-react.md`, `@nestjs/core` → + `nestjs.md`; `.java/.kt` → + `java-spring.md`. Paths relative to this skill's dir → `{CHECKLIST_PATHS}`.
- Layer 2: ① `.claude/pr-review-rules.md` if present → consume whole. ② else probe CLAUDE.md/AGENTS.md/docs/ for review-relevant rules. ③ else Layer 1 + tell user once. Layer 2 beats Layer 1 on conflict.

**6. Review.** ≤150 changed lines AND ≤3 files → direct single pass (same schema+falsify); else fan-out: 1 file = 1 general-purpose subagent, ≤5 per batch, prompt = template ①.

**7. Falsify pass** (if findings): ≤10 → one subagent, template ②; else split per file. Input = findings + relevant hunks; no tools. Count drops.

**8. Anchor.** ① `grep -nF` existing_code line 1 in `git show $REVIEW_SHA:<path>`; must land in an added-line range (multi-match → nearest line_hint). ② fail → one re-anchor call (template ③). ③ still → file-level comment, `anchor 미확정`. Never anchor outside the diff.

**9. Dedup → report → approval → post.**
- Dedup: same file+line±2+topic vs any existing comment (AI/human) → skip post, mark "기존 코멘트와 중복".
- Report (한국어): 적용 룰 소스 / Blocker·Bug·개선 섹션 — 건별 `` <등급 이모지> **<title>** — `파일:라인` [구분/등급] 규칙·출처 `` + 제안 1줄 + 상세 근거 / 요약표(파일|건수|구분|최고 등급)·스킵 표·반증 N건·중복 N건·재리뷰 판정 / `권장:` 머지 가부 1줄 / 발견 잔존 시 "다음 단계: `/pull-request-workflow:resolve-review-comments`로 반영" 1줄.
- Ask once: "게시 범위 — 전체 / Blocker·Bug만 / 안 함". Before posting, re-check `headRefOid` — changed (new push mid-review) → warn, re-anchor against the new head or stop. Inline: `gh api repos/<owner>/<repo>/pulls/<n>/comments -f body='...' -f commit_id=$REVIEW_SHA -f path='<path>' -F line=<line> -f side=RIGHT` (line = new-file line number from the anchor pipeline). One top-level `[AI 코드리뷰]` summary: `gh pr comment <n> --body-file <scratch>`. Anchor API error (422) → retry once as top-level comment with `파일:라인` in the body, report.
- Comment template (등급 이모지: 🚨 Blocker / 🐛 Bug / 💡 개선 — 양식 고정 요소라 문체 가이드의 이모지 금지 규칙보다 우선). No suggestion_code:

  ```
  <등급 이모지> **[AI 리뷰 · <구분>/<등급>]**

  **<title — 결론 1문장>**
  <fix — 행동 지시 1문장>

  > <impact — 영향·근거 1–2줄>
  ```

**10. Re-review** (`[AI 리뷰` comments exist): re-check each at REVIEW_SHA → 해결/미해결/판정불가. Pushback threads → re-examine (subagent if needed) → uphold with evidence or retract. On approval, thread replies via `gh api repos/<owner>/<repo>/pulls/<n>/comments/<databaseId>/replies -f body='...'`: 해결 "해결 확인했어요" / 미해결 remaining reason 1줄 / 철회 corrective (mispost → delete instead: `gh api -X DELETE repos/<owner>/<repo>/pulls/comments/<databaseId>`). New findings → step 9. "N번 다시 봐줘" → conversational deep-dive; same posting gate.

## Limits

- Anchoring = 3-stage approx (floor: file-level); re-runs non-deterministic.
- Inline `line` must exist in the PR diff and `commit_id` must be the current head — stale head → 422; step 9 re-checks `headRefOid` before posting.
- `gh pr diff` fallback has no truncation control — gate by file count/size first.
