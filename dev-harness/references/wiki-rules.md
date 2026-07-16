# Wiki Rules — `.harness/docs/` contract (SSOT)

This file lives in the dev-harness plugin and governs each project's `.harness/docs/` wiki. Single source of truth for what enters the wiki, where it lives, and how it is written. Consumers: writing-docs (per-branch write), harvest-docs (corpus audit). Read this file before authoring or restyling any wiki doc.

## Goal

Record what the next agent cannot learn from code alone. Every doc is read by an LLM — maximize fact density per token.

## Record

- Non-code context: domain policy, team convention, external infra, legal/contract constraints.
- Decision history: decisions with a real trade-off, non-obvious rejected alternatives and why (ADR).
- Pitfalls a future agent or worker would likely repeat.
- Background of core logic that will raise "why was it designed this way?".
- Code conventions invisible in the code itself: agreed style, naming, architecture patterns.
- Repeated procedures: order/checklist of recurring work (e.g. API add: DTO → Service → Controller → wiki upload; page add; pre-deploy checks).

## Exclude

- State/metadata checkable via `ls`/`grep`/`cat`.
- SSOT duplicates — logic or specs whose single source lives in code or another system.
- Local environment: per-user dev setup, temp files.
- Model general knowledge: framework/protocol/language standard behavior the LLM already knows (postMessage, OAuth, App Router, `httpOnly`). Record only this project's own rules.
- Migration narrative: "old X → new Y rename", "changed on day N". Record current state only — `updated` carries the when, git carries old names. A decision leaving future doubt → ADR.
- TODO/unimplemented: "next task", "unverified temp value" (issue tracker's domain).

Exception: an external-contract table not derivable from code by a simple transform (e.g. a route↔path map) is NOT code-checkable → keep.

## Layout + folder decision

```
.harness/docs/
├── {slug}.md                 # flat free markdown
├── procedures/{slug}.md      # procedure, order, recovery
├── external/{topic}.md       # external resource / infra / MCP pointers
└── adr/NNNN-{slug}.md        # architecture decision records
```

Folder is decided by body *shape*, not topic:

| Body answers | Folder |
|---|---|
| when, in what order, recovery on failure | `procedures/` |
| external URL or MCP location | `external/` |
| hard-to-reverse + future-reader doubt + real trade-off (all three) | `adr/` |
| otherwise | flat |

ADR gate: all three conditions or it stays flat. Even within one domain, extract a chunk whose shape differs; keep together only if it reads as one flow.

## Frontmatter (parsed by `wiki_index.py` — all four required)

```yaml
description: domain + when to reference (80–150 chars, noun-phrase ending, no keyword list)
scope: ["src/<real-path>/**"]   # applied paths only; "**" org-wide policy only
created: YYYY-MM-DD
updated: YYYY-MM-DD
```

- `description`: one physical line (parser requirement). If trimming the ending drops it under 80 chars, extend with a concrete domain noun phrase, never filler.
- On body change: verify `description` still covers the change; bump `updated`.
- `harvested: YYYY-MM-DD` optional — written and managed only by harvest-docs. Never set it when authoring.
- BAD: `scope: ["src/**/*.entity.ts"]` (one domain generalized to all entities)
  GOOD: `scope: ["src/feedback-post/**"]` (real applied paths only)

## Body principles

- **One file = one domain.** Domain = an independently-consumed concern. Accumulated foreign-domain concerns = a separate domain. No duplicates — a known fact merges into its existing file.
- **Business language.** Domain vocabulary over implementation tokens (class/method/table names). Citable: user-visible state names, public contracts (event names, headers, routes), external SDK public APIs.
- **Logic-independent.** A refactor must not invalidate the doc; the doc alone must reproduce the domain's policy.
- **Adopted rules only** in flat docs. Rejected alternatives → ADR when the gate holds, else drop. Never transcribe feedback's decision prose.
- **Domain ownership.** Another domain's facts have their SSOT in that domain's doc. Short contextual cite OK; never copy a whole fact-cluster (no snapshot).

## Style (body text + frontmatter `description` only)

Boundary: agent↔user reporting is the session-injected communication rule's domain — its `상태:`/`원인:` labels and Decision skeleton do NOT apply to wiki bodies.

- Noun endings (음/함/됨) or bare noun-phrase endings everywhere. 한다체/합니다체/해요체 full sentences banned. "빈 문자열을 반환한다" ❌ → "빈 문자열 반환" ⭕
- Headings are noun phrases. Never reword a heading another doc cites via `§` — cited heading text is frozen (anchor integrity).
- One bullet = one fact. Rule + condition + exception in one sentence → split.
- Causal prose → rule + rationale notation. Rule first; keep a load-bearing "why" as a ` — <noun phrase>` tail or nested `근거:` sub-bullet. Never the "~때문에 ~한다" order; never drop a load-bearing rationale to save tokens.
  - "캐시 dedupe가 파괴되기 때문에 contextLogger를 스레딩할 수 없다" ❌ → "contextLogger 스레딩 불가 — 캐시 dedupe 파괴" ⭕
- Preserve verbatim (never restyle): code blocks/spans; technical identifiers (function/route/field/error-code names, env vars, file paths); quoted UI string literals (합니다체 inside quotes is data); table structures; `§` anchors and their target headings.
- No hedging, no vague words — forbidden (source: session-injected communication rule): `TBD`, `적절히`, `필요시`, `유사하게 처리`, `가능성이 있다`, `일부 경우` — replace with concrete conditions/numbers.
- Style compression never changes the fact set: conditions, exceptions, numbers, rationales all survive. Fact deletion is governed solely by the Exclude list above.

## Folder skeletons

`procedures/` — When/Sequence/Rollback only; no policy, security, option, or follow-up prose (flat doc's job):

```md
# {name}

## When

## Sequence

## Rollback (없음 if none)
```

`external/` — 4-column table required; never cache external content (the source is SSOT); no schema, field names, event names, response values, or source policy in prose below the table. `접근 방법` notation: local file → absolute path; Confluence → `get_page` + pageId:

```md
| 리소스 | 플랫폼 | 접근 방법 | 참조 시점 |
| ------ | ------ | --------- | --------- |
```

`adr/` — filename `NNNN-{slug}.md`, N = max + 1:

```md
# {short decision title}

## 컨텍스트

## 결정

## Why

## Apply when
```

## Index

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wiki_index.py"` from the project root before accessing docs — once per session, cache. Columns: PATH | SCOPE | UPDATED | HARVESTED | LINES | DESCRIPTION. `--scope GLOB` filters. `harvested` blank = never cleaned.
