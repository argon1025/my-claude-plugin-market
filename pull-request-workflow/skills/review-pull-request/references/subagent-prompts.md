# pr-review subagent prompt templates

Orchestrator fills every `{...}` placeholder before dispatch. Subagent type: general-purpose.

## ① File review

```text
You are reviewing exactly one file of a GitHub PR.

File: {FILE_PATH}
PR intent: {PR_INTENT}
Review snapshot: commit {REVIEW_SHA} — review this snapshot, NOT the working tree.

First read these rule sources in order; on conflict, project docs (Layer 2) override the checklists:
1. {CHECKLIST_PATHS} (Layer 1 — stack-matched checklists)
2. {MATCHED_DOCS}

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

Do not report items this project's lint config (eslint·checkstyle 등) already blocks as error — see the checklists' lint 제외 notes.

Grade every finding by these questions (판정 질문):
- "Blocker": 그대로 배포하면 기존 소비처·사용자가 깨지거나(하위호환 파괴), 신규 기능이 크래시·오동작·보안 노출되는가 → 수정 후 배포.
- "Bug": 잘못 동작하는 결함이지만 배포 차단은 아님.
- "개선": 결함 아님 — 설계·컨벤션·성능 제안.

Output: exactly one fenced json block containing an array (no findings = []). Fields:
[{"file","existing_code" (1–3 added lines copied VERBATIM from the diff),"line_hint" (line number in the new file),"category" ("버그"|"사이드이펙트"|"보안"|"성능"|"컨벤션"|"테스트"),"grade" ("Blocker"|"Bug"|"개선"),"rule" (rule name · source doc),"title" (결론 1문장 — 무엇이 왜 문제인지, 코멘트 헤드라인용),"impact" (1 line — what breaks or what changes on deploy),"fix" (1 line — fix direction),"detail" (full reasoning — report only),"suggestion_code" (optional — report only)}]
```

## ② Falsify filter

```text
You re-examine code review findings. "Your task is NOT to verify whether all review comments are correct, but to filter out only those review comments that can be confirmed as incorrect based solely on the current diff. Core principle: You need to falsify, not verify." Unverifiable = keep — the reviewer may have confirmed context with tools you do not have. No tool use: the diff below is your entire evidence.

Diff:
{DIFF_HUNKS}

Findings (numbered):
{FINDINGS_JSON}

Output: one fenced json array: [{"id","verdict":"keep"|"drop","reason" (1 line)}]
```

## ③ Re-anchor (RE_LOCATION)

```text
The finding below failed line anchoring. From the diff, copy VERBATIM the minimal contiguous run of ADDED lines the comment refers to. Copy only — no edits, no summary, no rephrasing. If no added line matches, output NONE.

Diff:
{FILE_DIFF}

Finding:
{FINDING_JSON}

Output: one fenced text block with the verbatim line(s) only, or NONE.
```
