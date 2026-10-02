# 위키 PR 본문

update·add가 같은 본문을 쓰며 `--dry-run`에서도 씁니다. 행이 없는 절은 생략하고, 장 번호는 `references/apply.md` 기준이며, 재배정한 사실(4장)은 `.re` 판정을 씁니다. add에서 사용자가 `기존 유지`로 고른 사실은 싣지 않습니다.

## 채우는 법

- **레포**: update만 — `work.json`의 `repos`와 `skipped` 레포마다 1행, 처리 머지는 sha7과 `subject`(여러 건이면 `N건` 뒤 마지막 1건), `skipped` 사유·`remaining`(예산 밖 이월 N건)은 비고에
- **사실 목록**: `id` 있는 사실 전부를 `id` 순으로 1행(동일 포함) — 문서는 반영·제외 대상 문서(`knowledge/{domain}` 기준, 없으면 —), 판정은 아래 판정 표, 출처는 `source`를 쉼표로
- **제외된 사실 목록**: 아래 제외 표의 세 판정 사실마다 1행 — 머지 후 `/agent-wiki:add {PR 링크}`가 행 전부를 처리함
- **문서별 적용 내역**: 편집 문서마다 `### {doc} · 신규|수정` 아래 `**추가|교체**: {summary} (번호)`, `**삭제**: {old} (번호)`, `` **원본 맞춤**: `{set}` {before} → {after} ``(3장 `fixed_sets`), `**검토 수정**: {bullet} — {reason}`(3장 `edited`), `**검토 삭제**: {bullet} — {reason} (번호)`(3장 `removed`) 순
- **레포 지도**: 6장 `ops`마다 `- **{추가|삭제|교체}**: {slug} {key} {value} (G번호)`, `rejected`마다 `- **기각**: {slug} {key} {value} — {reason} (G번호)`

판정 표 (위가 먼저 적용됨)

| 판정 칸 | 원천 |
|---|---|
| `검토 기각 · {reject_reason}` | 5장 `검토 기각` 사실 |
| `위치 재배정` | 4장 두 번째 검토도 위치로 삭제 |
| `미해결 충돌` | 3장 `conflicts[].ids` |
| `검토 삭제 · {reason}` | 3장 `removed[].ids` 중 reason이 `위치`가 아닌 행 |
| `추가`·`동일`·`삭제`·`건너뜀` | 2장 `verdicts` |
| `교체 · 기존 {old} · 근거 {quote}` | 2장 `verdicts` |
| `대체 · {id}로 대체` | 1장 `rejected` 중 `대체 — {id}` — 같은 실행의 뒤 머지 사실이 값을 바꿈 |
| `기각 · {reason}` | 1장 `rejected`의 그 밖 사유 |

제외 표

| 구분 | 문서 | 기존 값 | 새 값 |
|---|---|---|---|
| 건너뜀 | 대상 문서 | 2장 `old` | 사실 |
| 위치 재배정 | 3장 `target` | — | 3장 `fact` |
| 미해결 충돌 | 대상 문서 | 3장 `code_value` | 3장 `doc_value` |

## 본문

````markdown
## 레포
| 레포 | 처리 머지 | 커서 | 비고 |
|---|---|---|---|
| shop-api | c61a8ab 주문 취소 사유 코드 검증 | 1c7f783 → c61a8ab | — |
| shop-admin | 0건 | 변화 없음 | 대상 ref 없음 (origin/main) |
| shop-worker | 10건 · 마지막 3ab7c55 이력 적재 재시도 | 9d2e0f1 → 3ab7c55 | 예산 밖 이월 12건 |

## 사실 목록
| # | 사실 | 문서 | 판정 | 출처 |
|---|---|---|---|---|
| F1 | 취소 요청의 사유 코드(cancelReasonCd)는 CR 공통코드 문자열이며 미등록 코드는 요청 단계에서 거부됨 | order-cancel-reason.md | 추가 | shop-api@c61a8ab |
| F2 | 주문 상태 DELETE는 운영자 삭제만 뜻하며 조회 API가 404를 반환함 | order-status.md | 교체 · 기존 `모든 삭제` · 근거 shop-api@c61a8ab | shop-api@c61a8ab |
| F3 | 취소 요청 DTO는 orderId·cancelReasonCd·memo 필드를 가짐 | order-cancel-reason.md | 검토 삭제 · 코드 전사 | shop-api@c61a8ab |
| F4 | 취소 이력 적재는 최대 5회 재시도함 | order-cancel-history.md | 건너뜀 | shop-worker@1a2b3c4 |
| F5 | 취소 사유 코드 CR09(시스템 취소)를 받음 | order-cancel-reason.md | 삭제 | shop-api@c61a8ab |
| F6 | shop-worker 이력 적재 리스너는 새 트랜잭션에서 실행함 | shop-worker/after-commit-listener.md | 위치 재배정 | shop-worker@3ab7c55 |

## 제외된 사실 목록
| # | 구분 | 문서 | 기존 값 | 새 값 | 출처 |
|---|---|---|---|---|---|
| F4 | 건너뜀 | order-cancel-history.md | 최대 3회 재시도 | 취소 이력 적재는 최대 5회 재시도함 | shop-worker@1a2b3c4 |
| F6 | 위치 재배정 | shop-worker/after-commit-listener.md | — | shop-worker 취소 이력 적재 리스너(CancelHistoryListener)는 새 트랜잭션(REQUIRES_NEW)에서 실행함 | shop-worker@3ab7c55 |

## 문서별 적용 내역

### order-cancel-reason.md · 신규
- **추가**: `규칙` 절에 사유 코드 문자열 수신과 미등록 코드 거부 (F1)
- **삭제**: CR09 시스템 취소 행 (F5)
- **검토 삭제**: 취소 요청 DTO 필드 목록 — 코드 전사 (F3)

### order-status.md · 수정
- **교체**: `코드값` 절의 DELETE 뜻 `모든 삭제` → `운영자 삭제, 조회 404` (F2)
- **원본 맞춤**: `OrderStatus` 전 3종 2행 → 전 3종 3행
- **검토 수정**: DELETE 불릿의 조회 API 식별자를 `GET /orders/{id}`로 교정 — 5장 식별자 병기, 머지 시점 코드와 불일치

## 레포 지도
- **추가**: shop-api deps `{"to": "example-shop/shop-worker", "desc": "취소 이력 적재 토픽을 취소 서비스에서 발행"}` (G1)
- **기각**: shop-admin responsibilities `취소 사유 일괄 등록` — 코드 미확인 (G2)
````
