# 위키 PR 본문

update·add가 같은 본문을 쓰며 `--dry-run`에서도 씁니다. 본문은 `## 사실 목록` 표 하나이고, 장 번호는 `references/apply.md` 기준입니다. add에서 사용자가 `기존 유지`로 고른 사실은 싣지 않습니다.

## 채우는 법

- **행**: `facts.json`의 `facts`·`rejected`와 `graph-candidates.json` 후보마다 1행을 `id` 순(F·A 다음 G)으로
- **사실**: 사실 행 `fact` — 위치 재배정은 두 번째 검토의 `removed.fact`, 지도 후보는 `{slug} {key} {value}`
- **문서**: 반영하거나 제외한 문서(`knowledge/{domain}` 기준) — 재배정은 거친 문서를 ` → `로 잇고 위치 재배정은 두 번째 검토의 `target`으로 끝냄, 지도 후보는 `registry.json`·`deps.json`, 배정 전 기각은 —
- **액션**: 사실이 거친 판정을 장 순서대로 ` → `로 이음 — 아래 액션 표, 검토가 불릿 일부만 지웠어도 같은 표기
- **기존 값**: 수정·건너뜀은 2장 `old`, 삭제는 지운 문장, 미해결 충돌은 3장 `code_value`, 지도 수정·삭제는 `old`, 그 밖은 —
- **출처**: `source`를 쉼표로

액션 표

| 액션 | 원천 |
|---|---|
| `추가`·`수정`·`삭제`·`동일`·`건너뜀` | 2장 `verdicts` — 교체는 `수정` |
| `검토 삭제 · {reason 한 구}` | 3장 `removed` 중 reason이 `위치`가 아닌 행 |
| `위치` | 3장 `removed` reason `위치` — 뒤에 4장 재배정 문서의 `.re` 반영·검토 판정을 이음 |
| `위치 재배정` | 4장 두 번째 검토도 위치로 삭제 |
| `미해결 충돌` | 3장 `conflicts` |
| `검토 기각 · {reject_reason}` | 5장 원복 — 다른 문서로 재배정한 사실은 붙이지 않음 |
| `대체 · {id}로 대체`·`기각 · {reason}` | 1장 `rejected` |
| `추가`·`삭제`·`수정`·`기각 · {reason}`·`동일` | 6장 `ops`·`rejected`, 둘 다 없으면 `동일` |

머지 후 `/agent-wiki:add {PR 링크}`는 마지막 액션이 `건너뜀`·`위치 재배정`·`미해결 충돌`인 행을 처리합니다.

## 본문

````markdown
## 사실 목록
| # | 사실 | 문서 | 액션 | 기존 값 | 출처 |
|---|---|---|---|---|---|
| F1 | 취소 요청의 사유 코드(cancelReasonCd)는 CR 공통코드 문자열이며 미등록 코드는 요청 단계에서 거부됨 | order-cancel-reason.md | 추가 | — | shop-api@c61a8ab |
| F2 | 주문 상태 DELETE는 운영자 삭제만 뜻하며 조회 API가 404를 반환함 | order-status.md | 수정 | 모든 삭제 | shop-api@c61a8ab |
| F3 | 취소 요청 DTO는 orderId·cancelReasonCd·memo 필드를 가짐 | order-cancel-reason.md | 추가 → 검토 삭제 · 코드 전사 | — | shop-api@c61a8ab |
| F4 | 취소 이력 적재는 최대 5회 재시도함 | order-cancel-history.md | 건너뜀 | 최대 3회 재시도 | shop-worker@1a2b3c4 |
| F5 | 취소 사유 코드 CR09(시스템 취소)를 받음 | order-cancel-reason.md | 삭제 | CR09 시스템 취소 행 | shop-api@c61a8ab |
| F6 | shop-worker 취소 이력 적재 리스너(CancelHistoryListener)는 새 트랜잭션(REQUIRES_NEW)에서 실행함 | order-cancel-history.md → shop-worker/after-commit-listener.md → shop-worker/cancel-history-listener.md | 추가 → 위치 → 추가 → 위치 재배정 | — | shop-worker@3ab7c55 |
| G1 | shop-api deps {"to": "example-shop/shop-worker", "desc": "취소 이력 적재 토픽을 취소 서비스에서 발행"} | deps.json | 추가 | — | shop-api@c61a8ab |
| G2 | shop-admin responsibilities 취소 사유 일괄 등록 | registry.json | 기각 · 코드 미확인 | — | shop-admin@9d2e0f1 |
````
