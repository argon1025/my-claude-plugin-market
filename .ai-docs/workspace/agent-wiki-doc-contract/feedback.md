# agent-wiki-doc-contract 작업 기록

- `context` agent-wiki 문서 규약은 llm-wiki `references/doc-contract.md`에서 이관 검토하며, 요구는 "문서는 결국 사용하는 에이전트 입장에서 쓰여야함 (예: 코드 계획, 코드 리뷰 등)", "기존 문서는 참고 하되 그대로 인용은 금지 인용에는 이유가 있어야함", "이후 코드의 diff 기반으로 원하는 내용과 파일이 나오는지 검증 (코드 diff 기반으로 문서를 업데이트할 예정이기 때문)"임
  - source: 사용자 확인 2026-09-29
- `context` 회사 위키 `onestore-devcenter-claude-plugin-marketplace/knowledge`는 "골든 문서는 아님 어떤 유형의 문서들이 있을 수 있는지 정도만 확인"하는 참고 자료이며 규약의 정답 표본으로 쓰지 않음
  - source: 사용자 확인 2026-09-29
- `constraint` agent-wiki 세션 주입의 문서 목록은 `knowledge/{domain}/*.md`와 `knowledge/{domain}/{slug}/*.md`를 한 단계만 glob하고 frontmatter `description` 한 줄만 읽으므로, 문서 규약은 하위 폴더(`policy/`·`adr/` 등)와 `description` 외 frontmatter 키에 기댈 수 없음
  - evidence: agent-wiki/scripts/generate_document_list.py
- `constraint` 회사 레포 로컬 사본(`~/Desktop/Projects/onestorecorp/onestore-cmsapp-*`)에는 회사 위키 문서의 출처 머지(`onestore-cmsapp-agent` b3a65b9·`onestore-cmsapp-api` a50dbaf·`onestore-cmsapp-integration-admin` d765b08·`onestore-cmsapp-client` dffa94a)가 있어, 같은 diff로 새 규약의 산출물을 기존 문서와 대조 검증할 수 있음
- `context` agent-wiki 문서 규약은 업무 주제 1개를 문서 1장으로 두고 규칙·코드값·상태와 전이·절차·함정·외부 참조·결정을 절로 가르며, frontmatter는 `description` 하나만 두고 사실의 출처는 본문이 아니라 커밋 메시지에만 남김 — 사용자가 주제 통합·`description`만·커밋 메시지만 3안과 사례 2종(국가 판매상태 변경 사유 도메인 루트 문서, cmsapp-agent 커밋 후 리스너 레포 문서)을 베스트 케이스로 확정함
  - source: 사용자 확인 2026-09-29
- `why` agent-wiki 문서는 llm-wiki처럼 유형(`type`)마다 문서를 나누지 않음 — 회사 위키에서 국가 판매상태 변경 사실이 `product-status-code`·`deploy-history-rows`·`deploy-country-identifier`로 흩어져 계획 에이전트가 여러 장을 열어야 했고, diff 반영 에이전트가 사실마다 유형을 먼저 판정해야 했기 때문이며, 대가는 주제 경계 판단이 description 한 문장 기준에 기대고 문서가 길어질 수 있다는 점임
- `why` agent-wiki 문서의 `## 함정` 절은 버그처럼 보이는 정상 동작을 담음 — 리뷰 에이전트가 의도된 동작(사유 null 이력, 배치 전체 롤백 등)을 수정 대상으로 지적하는 것을 막기 위함
- `constraint` my-claude-plugin-market은 PUBLIC 저장소이므로 `agent-wiki/references/doc-contract.md`의 예시는 회사 레포명·공통코드가 아닌 가상 도메인(`example-shop`)으로 쓰고, 사용자가 확정한 회사 사례 2종은 이 작업 기록과 대화에만 남김
- `correction` agent-wiki 문서 규약은 "diff에 다른 레포가 보이는가"로 위치를 가르지 않고 사실이 다루는 대상으로 가름 — DB 테이블에 남는 값·API·메시지·공통코드의 뜻과 밖에서 겪는 동작은 도메인 루트로 보냄. 이 경계 판정이 없던 초안으로 cmsapp-agent b3a65b9·cmsapp-integration-admin d765b08 diff를 반영했을 때 공유 테이블 적재 방식·배포 대기 동작이 전부 레포 폴더로 갔고, 경계 판정을 넣은 뒤 재실행에서는 도메인 루트로 올라감
  - evidence: agent-wiki/references/doc-contract.md
- `constraint` 공유 라이브러리 enum에 코드 한 줄만 더한 diff(cmsapp-client dffa94a)는 그 값이 DB·공통코드로 레포 밖에 넘어가는지 diff만으로 알 수 없어, 새 규약에서는 문서 없이 끝남 — diff 밖 코드를 읽지 않는 update에서 공유 코드값 표를 채우려면 소비 레포 코드 확인이 필요함
- `why` llm-wiki 규약과 같은 diff 5건을 비교한 결과, agent-wiki 규약을 택한 이유는 문서 수(B 17장 대비 V·T 13장), 변경 서사 혼입(B1 5건 대비 V1 1건), 의도된 동작 표시, 라이브러리 함정 재현(d765b08 AntD 함정 4/4 대비 1/4), 추측 문서 미생성(B4는 근거 없는 비고가 달린 1행 코드 문서 생성)임. 대가는 도메인 루트 승격 판단이 llm-wiki 규약보다 보수적이라는 점이며, 이 약점은 경계 판정 조항으로 보완함
