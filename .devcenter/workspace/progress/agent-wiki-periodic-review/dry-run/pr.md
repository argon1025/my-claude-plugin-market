## 사실 목록

| # | 사실 | 문서 | 액션 | 기존 값 | 출처 |
| --- | --- | --- | --- | --- | --- |
| F1 | 파트너 인수 알림에 보관함 식별자 lockerId를 포함한다. | partner-handoff-notice.md | 추가 | 문서 없음 | batch-api@910ddf6 specs/notice.md, 인수 알림 규격 v1 §1 |
| F2 | 온라인 주문은 구매 다음 날부터 8일 동안 환불 접수를 허용한다. | refund-window.md | 교체 | 3일 | MARKET-17#42 r4. 20일 제안(#41)과 완료 알림(#43)은 제외 |
| F3 | 파트너 보관 영수증은 완료 후 14일까지 HTTP 200, 이후 HTTP 410을 반환한다. | archive-receipt-access.md | 추가 | 문서 없음 | archive-api@68fd090 specs/receipt-v4.md, 영수증 열람 규격 제4판 §2 |
| F4 | 어드민 영수증 목록을 라벨순으로 정렬하는 코드에는 이를 보장하는 결정이 없다. | — | 제외 | — | archive-api@68fd090 src/archive.py, specs/receipt-v4.md |
| F5 | 온라인 가맹점 증빙 재전송의 기준은 생성 후 72시간이다. | delivery-window.md, batch-api/delivery-retry.md | 공통 원문 유지, 옛 사본을 상대 링크로 교체 | 온라인 사본 24시간 | batch-api@910ddf6 specs/delivery.md v3 §1 |
| F6 | 망분리 단말에는 별도 24시간 기한이 적용된다. | field-console/delivery-retry.md | 유지 | 24시간 | field-console@d2e243c specs/offline.md 부속 규격 v1 §3 |
| F7 | 야간 거래 파일은 UTF-8을 사용한다. | export-encoding.md, batch-api/export-batch.md | 공통 원문 유지, 사본을 상대 링크로 교체 | 동일 정책의 사본 | batch-api@910ddf6 specs/export.md v1 §2 |
| F8 | 수요일 02:00~03:00 송신 제한과 전용 회선 재처리의 당직 2인 승인을 한 작업 문서에서 읽을 수 있다. | batch-api/export-batch.md, batch-api/export-replay.md | 두 고유 제약과 각각의 출처를 보존해 병합 | 두 문서에 분산 | batch-api@910ddf6 ops/nightly.md v3 §§1–2 |
| F9 | 배치 함수 호출 순서와 시연용 JAR 확인 기록을 제거한다. | batch-api/export-batch.md, batch-api/export-replay.md | 두 문장 삭제 | normalize → flush, demo-3.jar 시연 | batch-api@910ddf6 src/workflows.py, 기존 문서 원문 |
| F10 | 당직 인계 문서의 증빙 보관 조건과 두 링크가 유지된다. | batch-api/shift-handover.md | 기존 송신 링크 유지, 승인 링크를 병합 문서의 함정 절로 교체 | export-replay.md#함정 | batch-api@910ddf6 ops/nightly.md v3 §3, 기존 인계 문서 |
| G1 | batch-api가 파트너 인수 알림 본문을 만든다. | registry.json | 책임 추가 | 정산 파일과 환불 접수 | batch-api@910ddf6 src/notice.py |
