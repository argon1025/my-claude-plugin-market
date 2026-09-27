# update PR 본문 템플릿

`/llm-wiki:update` 7장이 `{스크래치}/pr.md`를 쓸 때 따르는 구조와 규칙입니다. 메인 에이전트가 `work.json`·`assign.json`·`{applied_dir}`·`{review_dir}` JSON을 한 번 순회해 채웁니다.

## 작성 규칙

- **사실 원장**: 추출 사실 전부를 `F{n}` 번호 순 1행씩(동일 포함) — 사유는 교체면 기존 값·인용, 건너뜀이면 기존 값과 사유, 기각·검토 삭제면 사유, 그 외 `—`, 출처는 `{slug}@{sha7}`(근거 여러 개면 쉼표)
- **판정 값**: 추가·교체·동일·건너뜀·검토 삭제·기각 중 하나 — 검토 삭제는 5장 `removed[].ids`에 든 사실, 기각은 `assign.json` `rejected`와 6장 `검사 실패`
- **문서 절**: 편집 문서마다 `### {도메인 루트 기준 상대경로} · 신규|수정`, 불릿은 `**추가|교체|삭제**: {절}에 {무엇} (F번호)`로 판정별 한 줄 — 원천은 4장 `verdicts[].summary`와 5장 `removed`, 동일은 적지 않음
- **레포 행**: 처리 머지는 커밋 링크(`https://{registry.json remote}/commit/{sha}`)와 제목(`work.json` `commits[].subject`)(여러 건이면 `N건` 뒤 대표 1건), 머지 0건·`skipped` 레포도 1행으로 비고에 사유
- **생략**: 행이 없는 절(그래프·문서 등)은 절째 생략
- **길이**: 60,000바이트를 넘으면 `## 추출 사실` 절을 PR 첫 코멘트로 옮기고 그 자리에 "사실 원장은 첫 코멘트" 한 줄

## 본문

````markdown
## 요약
- **레포**: {slug} 머지 {N}건 외 레포별 한 구
- **집계**: 사실 {n}건 — 추가 {a} · 교체 {r} · 동일 {s} · 건너뜀 {k} · 검토 삭제 {d} · 기각 {j}, 문서 신규 {c} · 수정 {m}, 그래프 {변경 요약 또는 "변경 없음"}

## 레포
| 레포 | 처리 머지 | 커서 | 비고 |
|---|---|---|---|
| pigeon-trade | [c61a8ab](https://{remote}/commit/{sha}) {커밋 제목} | 1c7f783 → c61a8ab | — |
| pigeon-trade-dashboard | 0건 | 변화 없음 | 대상 브랜치 main 없음 — registry `defaultBranch` 수정 필요 |

## 추출 사실
| # | 사실 | 판정 | 사유 | 출처 |
|---|---|---|---|---|
| F1 | 도메인 모듈은 위임 전용 외부 노출 서비스(`{Domain}ExternalService`) 하나만 export | 추가 | — | pigeon-trade@c61a8ab |
| F4 | 통화 타입 이름은 `Currency` | 교체 | 기존 `BrokerageCurrency` · 인용 "…" | pigeon-trade@c61a8ab |
| F6 | 외부 노출 서비스 파일 위치는 `service/{domain}-external.service.ts` | 검토 삭제 | 코드로 확인 가능, 기각 대안 없음 | pigeon-trade@c61a8ab |
| F9 | … | 기각 | 한 주제 아님 | pigeon-trade@c61a8ab |

## 문서

### pigeon-trade/domain-module-exports.md · 신규
- **추가**: `외부 노출` 절에 외부 노출 서비스 단일 export 규칙과 기각한 DI 파사드 설계 (F1)
- **추가**: `검증` 절에 모듈 연결 변경 시 로컬 기동 확인 절차 (F2)
- **삭제**: 외부 노출 서비스 파일 위치 불릿 — 코드로 확인 가능 (F6)

### pigeon-trade/brokerage-market-data-strategy.md · 수정
- **교체**: 통화 타입 이름 `BrokerageCurrency` → `Currency` (F4)

## 그래프
- **간선**: {추가·보탠 간선 `from → to (kind)` 목록}
- **책임·호스트**: {추가·교체 항목}

## 검토 방법
- **승인**: rebase 또는 merge commit으로 머지 — squash는 문서별 커밋 근거를 지우므로 금지
- **부분 수정**: 이 브랜치에서 해당 불릿을 고친 뒤 머지
- **전체 거절**: PR close — 커서가 `main`에 반영되지 않아 다음 실행이 같은 머지를 다시 처리
- **건너뜀 처리**: 판정 `건너뜀` 행은 머지 후 `/llm-wiki:add`로 반영
````
