---
name: walkthrough
description: Use after planning or implementation on a feature branch to walk a developer through the work interactively — one unit per turn, design intent and alternatives, advancing only on confirmed understanding — then triage collected comments and commit a review record ("코드 설명", "온보딩", "워크스루", "walkthrough").
---

Walk the reviewer through the branch's work in conversation, unit by unit. The deliverables are the reviewer's understanding and a committed record of what the review changed — there is no standalone explanatory document. Speak Korean.

## Inputs & mode

Resolve `{branch-slug}`; refuse on develop/main/master. Read `.harness/workspace/progress/{slug}/plan.md` and `feedback.md` when present, plus the branch's log and diff against the integration branch.

- Implementation commits exist → **code mode**: walk through what was built, grounded in the diff.
- Plan snapshot only → **plan mode**: walk through what will be built and why, grounded in the plan.

## Preparing the tour

Build the whole tour before the first turn — internally, not as a document:

- Order units bottom-up: smallest first (types, utils), then their composers (hooks, components, routes), ending with one end-to-end trace of the main scenario.
- Per unit: what it does, why this shape, and which alternatives lost and why. Rationale comes only from plan.md decisions, feedback.md entries, and commit messages — never invent one after the fact.
- Keep a 한계와 아쉬운 점 list (known trade-offs, deferred work) for the closing turn.

## Interactive walkthrough

One unit per turn:

- Present compactly — what it does → why this shape → what lost. Reference code as `path:line`; expand jargon on first use.
- End every turn by asking: questions, comments, or move on. Advance only after the reviewer confirms they've understood.
- Depth follows the reviewer. Answer questions inline; open the code on request. Repeated questions mean the tour is pitched wrong — adjust the remaining units.
- Collect comments at any turn: acknowledge, note which unit they attach to, ask clarifying questions if needed — but do not judge or fix anything during the tour.

Close with the end-to-end trace, then the 한계와 아쉬운 점 list as the explicit invitation for final comments.

## Triage

Triage as the project owner, not a transcriber: for every collected comment decide **수용** or **기각**, each with a reason grounded in the plan's rationale, the wiki, conventions, or the code — a comment is never applied just because it was made. Present one table — 지적 / 수용여부 / 사유 / 수정 계획 (accepted items only) — and get the reviewer's approval of the whole set.

Then execute the accepted items by mode:

- **plan mode** → append `## Re-plan YYYY-MM-DD` to plan.md covering all accepted items; implementation stays with a fresh `/dev-harness:executing-plan` session.
- **code mode** → fix and commit in this session per execution norms.
- Decisions or corrections surfaced by the review that pass the feedback bar → feedback.md (grammar: the session-injected dev-harness guide).

## Review record

Output: `.harness/workspace/progress/{slug}/review.md`, committed after execution. It records what the review changed — not an explanation of the code:

- 리뷰 전 방향을 서너 줄로 요약.
- Per comment, one block: 지적 → 수용/기각 → 사유 → 변경 결과. 변경 결과 states 기존 → 변경 in one or two sentences; code mode cites the fix commit, plan mode cites the Re-plan section.
- No accepted comments → still commit the record; the rejection reasons are the design's defense on file.

A rerun on the same branch appends `## 리뷰 N차 YYYY-MM-DD` instead of overwriting.
