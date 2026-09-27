# /llm-wiki:update PR 본문

행이 없는 절은 절째 생략합니다.

## 채우는 법

- **레포**: `work.json`의 `repos`와 `skipped` 레포마다 1행 — 처리 머지는 `https://{registry.json remote}/commit/{sha}` 링크와 `subject`(여러 건이면 `N건` 뒤 마지막 1건), `skipped` 사유·`notes`·`remaining`(예산 밖 이월 N건)은 비고에
- **추출 사실**: `id` 순으로 `id` 있는 사실 전부 1행(동일 포함) — 판정·사유는 아래 표, 출처는 `{slug}@{sha7}`를 쉼표로
- **문서**: 편집 문서마다 `### {도메인 루트 기준 상대경로} · 신규|수정` 아래 `**추가|교체**: {summary} (F번호)`와 `**삭제**: {bullet} — {reason} (F번호)`, 동일·건너뜀은 적지 않음
- **그래프**: 3장 `graph` 배정 중 반영된 간선·책임·호스트와 `id` 없는 `rejected`(사유·식별자 원문)

| 판정 | 원천 | 사유 칸 |
|---|---|---|
| 추가·동일 | 4장 `verdicts` | — |
| 교체 | 4장 `verdicts` | 기존 `{old}` · 인용 "{3장 사실 행 quote}" |
| 건너뜀 | 4장 `verdicts` | 기존 `{old}` · 의도 인용 없음 |
| 검토 삭제 | 5장 `removed[].ids` — 4장 판정보다 우선 | `{reason}` |
| 기각 | 3장 `rejected`, 6장 되돌림 | `{reason}` 또는 `검사 실패` |

## 본문

````markdown
## 요약
- **집계**: 사실 {n}건 — 추가 {a} · 교체 {r} · 동일 {s} · 건너뜀 {k} · 검토 삭제 {d} · 기각 {j}, 문서 신규 {c} · 수정 {m}, 그래프 {변경 요약 또는 "변경 없음"}

## 레포
| 레포 | 처리 머지 | 커서 | 비고 |
|---|---|---|---|
| pigeon-trade | [c61a8ab](https://github.com/{owner}/pigeon-trade/commit/{sha}) {subject} | 1c7f783 → c61a8ab | — |
| pigeon-trade-dashboard | 0건 | 변화 없음 | 대상 브랜치 main 없음 — registry `defaultBranch` 수정 필요 |
| pigeon-broker | 40건 | 9d2e0f1 → 3ab7c55 | 예산 밖 이월 12건 |

## 추출 사실
| # | 사실 | 판정 | 사유 | 출처 |
|---|---|---|---|---|
| F1 | 도메인 모듈은 위임 전용 외부 노출 서비스(`{Domain}ExternalService`) 하나만 export | 추가 | — | pigeon-trade@c61a8ab |
| F4 | 통화 타입 이름은 `Currency` | 교체 | 기존 `BrokerageCurrency` · 인용 "…" | pigeon-trade@c61a8ab |
| F6 | 외부 노출 서비스 파일 위치는 `service/{domain}-external.service.ts` | 검토 삭제 | 코드로 확인 가능 | pigeon-trade@c61a8ab |
| F9 | … | 기각 | 한 주제 아님 | pigeon-trade@c61a8ab |

## 문서

### pigeon-trade/domain-module-exports.md · 신규
- **추가**: `외부 노출` 절에 외부 노출 서비스 단일 export 규칙과 기각한 DI 파사드 설계 (F1)
- **삭제**: 외부 노출 서비스 파일 위치 불릿 — 코드로 확인 가능 (F6)

### pigeon-trade/brokerage-market-data-strategy.md · 수정
- **교체**: `타입` 절의 통화 타입 이름 `BrokerageCurrency` → `Currency` (F4)

## 그래프
- **간선**: pigeon-trade → pigeon-broker (http) `contracts`에 `GET /quotes` 보탬
- **기각**: 상대 미정 — `ORDER_FILLED` 큐 소비

## 검토 방법
- **승인**: rebase 또는 merge commit으로 머지 — squash는 문서별 커밋 근거를 지우므로 금지
- **부분 수정**: 이 브랜치에서 해당 불릿을 고친 뒤 머지
- **전체 거절**: PR close — 커서가 `main`에 반영되지 않아 다음 실행이 같은 머지를 다시 처리
- **건너뜀 처리**: 판정 `건너뜀` 행은 머지 후 `/llm-wiki:add`로 반영
````
