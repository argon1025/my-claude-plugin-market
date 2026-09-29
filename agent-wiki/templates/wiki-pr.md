# 위키 PR 본문

update·add가 같은 본문을 씁니다. 행이 없는 절은 절째 생략합니다. 장 번호는 `references/apply.md` 기준입니다.

## 채우는 법

- **레포**: update만 — `work.json`의 `repos`와 `skipped` 레포마다 1행, 처리 머지는 sha7과 `subject`(여러 건이면 `N건` 뒤 마지막 1건), `skipped` 사유·`remaining`(예산 밖 이월 N건)은 비고에
- **추출 사실**: `id` 순으로 `id` 있는 사실 전부 1행(동일 포함) — `#`은 update `F`·add `A` 번호, 판정·사유는 아래 표, 출처는 사실 행 `source`를 쉼표로
- **문서**: 편집 문서마다 `### {doc} · 신규|수정` 아래 `**추가|교체**: {summary} (F·A번호)`, `**원본 맞춤**`, `**검토 수정**`, `**미해결 충돌**`, `**삭제**: {bullet} — {reason} (F·A번호)` 순, 동일·건너뜀은 적지 않음
- **원본 맞춤**: 3장 `fixed_sets`마다 `` **원본 맞춤**: `{set}` {before} → {after} ``
- **검토 수정**: 3장 `edited`마다 `**검토 수정**: {bullet} — {reason}`
- **미해결 충돌**: 3장 `conflicts`마다 `**미해결 충돌**: 자료 {doc_value} / 코드 {code_value} (F·A번호)` — 변경 의도를 찾지 못해 문서에 기록하지 않음, 머지 후 `/agent-wiki:add`로 현재 값을 정함
- **레포 지도**: 6장 `ops`마다 `- **{추가|삭제|교체}**: {slug} {key} {value} (G번호)`, `rejected`마다 `- **기각**: {slug} {key} {value} — {reason} (G번호)`
- **add 기존 유지**: add에서 사용자가 `기존 유지`로 고른 사실은 PR에 싣지 않고 스킬 보고로만 남김

재배정한 사실(4장)은 `.re` 파일의 판정을 씁니다.

| 판정 | 원천 | 사유 칸 |
|---|---|---|
| 추가·동일 | 2장 `verdicts` | — |
| 교체 | 2장 `verdicts` | 기존 `{old}` · 인용 "{사실 행 quote}" |
| 건너뜀 | 2장 `verdicts` | 기존 `{old}` · 의도 인용 없음 · 머지 후 `/agent-wiki:add {PR 링크}`로 교체 여부 결정 |
| 검토 삭제 | 3장 `removed[].ids` — 2장 판정보다 우선, reason이 `위치 — `로 시작하는 행 제외 | `{reason}` |
| 위치 재배정 | 4장 두 번째 검토도 위치로 삭제 — 머지 후 `/agent-wiki:add {PR 링크}`로 반영 | `{올바른 위치}` |
| 기각 | 1장 `rejected` 중 `대체 — `로 시작하지 않는 사유 | `{reason}` |
| 대체 | 1장 `rejected` 중 `대체 — {id}` — 같은 실행의 뒤 머지 사실이 값을 바꿈 | `{id}`로 대체 |
| 검토 기각 | 3장 `reject_reason` — 5장에서 원복한 문서의 사실 전부 | `{reject_reason}` |

## 본문

````markdown
## 요약
- **집계**: 사실 {n}건 — 추가 {a} · 교체 {r} · 동일 {s} · 건너뜀 {k} · 대체 {v} · 검토 삭제 {d} · 위치 재배정 {l} · 기각 {j} · 검토 기각 {x}, 문서 신규 {c} · 수정 {m}, 지도 {g}건

## 레포
| 레포 | 처리 머지 | 커서 | 비고 |
|---|---|---|---|
| shop-api | c61a8ab 주문 취소 사유 코드 검증 | 1c7f783 → c61a8ab | — |
| shop-admin | 0건 | 변화 없음 | 대상 ref 없음 (origin/main) |
| shop-worker | 40건 · 마지막 3ab7c55 이력 적재 재시도 | 9d2e0f1 → 3ab7c55 | 예산 밖 이월 12건 |

## 추출 사실
| # | 사실 | 판정 | 사유 | 출처 |
|---|---|---|---|---|
| F1 | 취소 요청의 사유 코드(cancelReasonCd)는 CR 공통코드 문자열이며 미등록 코드는 요청 단계에서 거부됨 | 추가 | — | shop-api@c61a8ab |
| F2 | 주문 상태 DELETE는 운영자 삭제만 뜻하며 조회 API가 404를 반환함 | 교체 | 기존 `모든 삭제` · 인용 "…" | shop-api@c61a8ab |
| F3 | 취소 요청 DTO는 orderId·cancelReasonCd·memo 필드를 가짐 | 검토 삭제 | 코드 전사 | shop-api@c61a8ab |
| F4 | … | 기각 | 한 주제 아님 | shop-worker@3ab7c55 |
| F5 | 취소 이력 적재는 최대 3회 재시도함 | 대체 | F6으로 대체 | shop-worker@1a2b3c4 |
| F7 | shop-worker 이력 적재 리스너는 새 트랜잭션에서 실행함 | 위치 재배정 | shop-worker 레포 폴더 | shop-worker@3ab7c55 |

## 문서

### order-cancel-reason.md · 신규
- **추가**: `규칙` 절에 사유 코드 문자열 수신과 미등록 코드 거부 (F1)
- **삭제**: 취소 요청 DTO 필드 목록 — 코드 전사 (F3)

### order-status.md · 수정
- **교체**: `코드값` 절의 DELETE 뜻 `모든 삭제` → `운영자 삭제, 조회 404` (F2)
- **원본 맞춤**: `OrderStatus` 전 3종 2행 → 전 3종 3행
- **검토 수정**: DELETE 불릿의 조회 API 식별자를 `GET /orders/{id}`로 교정 — 5장 식별자 병기, 머지 시점 코드와 불일치

## 레포 지도
- **추가**: shop-api deps `{"to": "example-shop/shop-worker", "desc": "취소 이력 적재 토픽을 취소 서비스에서 발행"}` (G1)
- **기각**: shop-admin responsibilities `취소 사유 일괄 등록` — 코드 미확인 (G2)

## 검토 방법
- **승인**: rebase 또는 merge commit으로 머지 — squash는 문서별 커밋 근거를 지우므로 금지
- **부분 수정**: 이 브랜치에서 해당 불릿을 고친 뒤 머지
- **전체 거절**: PR close — update는 커서가 기준 브랜치에 반영되지 않아 다음 실행이 같은 머지를 다시 처리
- **남은 행**: 건너뜀·위치 재배정 행은 머지 후 이 PR 링크를 `/agent-wiki:add`에 건네 처리
````
