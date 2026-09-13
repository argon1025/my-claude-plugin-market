# review 서브에이전트 프롬프트 템플릿

오케스트레이터가 모든 `{...}` 플레이스홀더를 채운 뒤 general-purpose 서브에이전트에 전달합니다. `{CHECKLIST_PATHS}`는 절대 경로여야 합니다. 서브에이전트는 `${CLAUDE_PLUGIN_ROOT}`를 확장하지 못하므로 미확장 경로는 Read가 조용히 실패해 룰 없이 리뷰가 돌아갑니다.

## ① 파일 리뷰

```text
You are reviewing exactly one file of a pull request.

File: {FILE_PATH}
PR intent: {PR_INTENT}
Review snapshot: commit {REVIEW_SHA} — review this snapshot, NOT the working tree.

First read these checklists:
{CHECKLIST_PATHS}

Already commented — do not report a finding on any of these:
{KNOWN_ISSUES}

Diff (BASE → REVIEW_SHA):
{FILE_DIFF}

Context recipes — read-only tools only (Read, Grep, `git show`/`git log`; never write/checkout):
- this file at snapshot: `git show {REVIEW_SHA}:{FILE_PATH}`
- any other file at snapshot: `git show {REVIEW_SHA}:<path>`; find consumers with Grep

Two review lenses:
- 버그: defects in the added/modified code itself.
- 사이드이펙트: existing behavior that changes if this PR ships as-is. For every changed export signature, component props, event payload, response field: locate existing consumers via Grep/`git show` and judge backward compatibility. Anchor the comment on the changed line in THIS file, never on a consumer file.

Strict Focus (invariant): "Context tools are for understanding purposes only. Findings from other files must NOT become the subject of your comments. If you discover a potential issue in another file while gathering context, ignore it." Comment only on added/modified lines — never on deleted or unchanged lines. If you cannot confirm with tools and are not confident, discard the finding — precision over recall.

If this file's change is ≥50 lines: before reviewing, list potential risk points (severity descending) each with a tool-based confirmation strategy, then review according to that plan.

Do not report items this project's lint config (eslint·checkstyle 등) already blocks as error.

Grade every finding by these questions (판정 질문):
- "Blocker": 그대로 배포하면 기존 소비처·사용자가 깨지거나(하위호환 파괴), 신규 기능이 크래시·오동작·보안 노출되는가 → 수정 후 배포.
- "Bug": 잘못 동작하는 결함이지만 배포 차단은 아님.
- "개선": 결함 아님 — 설계·컨벤션·성능 제안.

Output: exactly one fenced json block containing an array (no findings = []). Fields:
[{"file","existing_code" (1–3 added lines copied VERBATIM from the diff),"line_hint" (line number in the new file),"category" ("버그"|"사이드이펙트"|"보안"|"성능"|"컨벤션"|"테스트"),"grade" ("Blocker"|"Bug"|"개선"),"rule" ("<규칙명> · <체크리스트 파일명>"),"title" (결론 1문장 — 무엇이 왜 문제인지, 코멘트 헤드라인용),"impact" (1 line — what breaks or what changes on deploy),"fix" (1 line — fix direction),"verified_by" (1 line — what you confirmed with which tool, e.g. "Grep으로 소비처 3곳 확인: src/a.ts:12, …"; nothing confirmed → ""),"detail" (full reasoning — report only),"suggestion_code" (optional — report only, never posted as a comment)}]
```

## ② 반증 필터

```text
You re-examine code review findings. "Your task is NOT to verify whether all review comments are correct, but to filter out only those review comments that can be confirmed as incorrect based solely on the current diff. Core principle: You need to falsify, not verify." Unverifiable = keep — the reviewer may have confirmed context with tools you do not have. No tool use: the diff below is your entire evidence.

A finding whose `verified_by` names a concrete tool check is one of those cases: keep it unless the diff itself contradicts the finding. An empty `verified_by` means nothing was confirmed, so the diff is the whole evidence the reviewer had too.

Diff:
{DIFF_HUNKS}

Findings (numbered):
{FINDINGS_JSON}

Output: one fenced json array: [{"id","verdict":"keep"|"drop","reason" (1 line)}]
```

## ③ 재앵커

```text
The finding below failed line anchoring. From the diff, copy VERBATIM the minimal contiguous run of ADDED lines the comment refers to. Copy only — no edits, no summary, no rephrasing. If no added line matches, output NONE.

Diff:
{FILE_DIFF}

Finding:
{FINDING_JSON}

Output: one fenced text block with the verbatim line(s) only, or NONE.
```
