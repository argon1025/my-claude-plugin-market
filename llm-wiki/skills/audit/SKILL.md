---
name: audit
description: Use when the wiki must be swept after unattended updates or on a schedule ("위키 정리", "위키 감사", "문서 정리", "중복 정리", "낡은 문서 확인") — measures the wiki with catalog.py --check, fans out subagents over 5–6 docs per batch to flag fragments, duplicate facts, stale docs, over-long descriptions and contract violations, presents one approval table with before/after lines, applies per doc, re-checks, commits and pushes. Adds no new facts. NOT for landing new material or merged code (that is /llm-wiki:add and /llm-wiki:update's job).
---

기존 문서만 고치고 새 사실을 들이지 않습니다. 규약은 `${CLAUDE_PLUGIN_ROOT}/references/doc-contract.md`가 정본이며 서브에이전트에게는 절대 경로로 넘깁니다. 인자: `--scope {domain}|{domain}/{slug}`(기본 현재 도메인 루트 + 현재 레포), `--docs {경로...}`(지목 문서만).

## 1. 측정

- **동기화**: `git -C {WIKI_ROOT} pull --ff-only`, 실패 시 중단
- **검사·목록**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/catalog.py" --check --root {WIKI_ROOT}/knowledge`의 에러와 `catalog.py --root {WIKI_ROOT}/knowledge/{domain} --shallow`·`--root {WIKI_ROOT}/knowledge/{domain}/{slug}` 목록을 `{스크래치}/catalog.md`로 저장 — `!` 낡음·60자 초과·description 중복이 여기서 나옴
- **그래프**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/graph.py" check --wiki {WIKI_ROOT}`의 에러와 `graph.py map --domain {domain}` 출력의 `!` 간선 목록, `areas`가 빈 `active` 노드 목록을 같은 `catalog.md`에 이어 저장 — 노드·간선은 서브에이전트에 보내지 않고 메인이 봄
- **인박스**: 스코프 도메인의 `inbox/{domain}.md` 행 수를 세고 "처리는 `/llm-wiki:add`" 안내
- **묶음**: 대상 문서를 폴더별 5~6건으로 나누고 문서마다 검사 줄을 힌트로 붙임 — 메인은 문서 본문을 열지 않음

## 2. 진단 fan-out — 묶음 1개 = 에이전트 1회

한 메시지에 병렬 Agent 호출, 모델은 메인 상속(삭제·통합 판정은 품질이 갈리는 자리). 응답 없는 묶음은 재실행합니다.

````
위키 문서를 진단하는 작업입니다. 판정만 하고 문서를 고치지 마세요. 커밋하지 마세요.

- 대상: {절대 경로 5~6건}. 목록 전체는 {catalog.md}. 힌트: {문서별 --check 에러 — 없으면 "없음"}.
- 읽을 수 있는 것은 대상 문서·목록·규약 `sed -n '/^## 1\./,/^## 7\./p' {doc_contract_path}`뿐입니다. 코드 저장소 조회 금지, 사전 지식으로 공백 채우기 금지.
- 오늘은 {today}입니다.

문서마다 아래 신호를 판정하고 조치 행을 쓰세요. 값이 어긋나는 불릿 쌍은 통합하지 않고 `충돌`로 적으세요.

| 신호 | 조치 |
|---|---|
| 같은 문서 안에서 같은 주장을 하는 불릿 둘 | `통합` — 전: 두 줄 원문, 후: 조건·수치·근거를 합집합한 한 줄 |
| 코드 검색 한 번으로 참이 확인되는 불릿 | `삭제` — 후 비움, 비고에 확인 위치 |
| 변경 서사 불릿("A에서 B로", "추후", "폐기") | 현재 상태로 다시 쓸 수 있으면 `재작성`, 없으면 `삭제` |
| 다른 위키 문서 링크·이름 참조 | 접점 사실로 `재작성`, 남는 것이 "다른 곳에 있다"뿐이면 `삭제` |
| 레포 소관·역인덱스·의존 방향을 본문으로 적은 절(규약 3장 예약 파일 없음) | `삭제` — 후 비움, 비고에 원문 줄(노드·간선으로 옮길 후보) |
| description 60자 초과·"때" 미종결·범주어만 | `설명` — 후: 새 문장. 한 주제로 60자에 안 덮이면 `분할 후보` |
| 40줄 미만이고 목록의 다른 문서 description이 이미 그 주제를 덮음(조각) | `흡수` — 후: 소유 문서 경로와 절, 비고에 옮길 불릿 원문 |
| 절 제목과 다른 질문에 답하는 불릿 | `이동` — 후: 대상 절 |
| `!` 낡음 문서 | 위 점검을 마쳤으면 `검증`, 코드 대조가 필요한 값은 `확인 필요` |

응답은 표 행만 — `| 조치 | 문서:절 | 전 | 후 | 비고 |`. 전·후는 원문 줄 그대로(여러 줄은 <br>), 요약 금지. 신호 없는 문서는 `없음` 행 하나.
````

## 3. 승인 — 정지점 하나

- **영역 통합 행**: `graph.py check`가 낸 영역 키 유사 중복 쌍과 같은 도메인에서 구두점·공백만 다른 키 쌍을 메인이 직접 `| 통합 | registry.json:areas | {두 키} | {남길 키} | {옮길 노드} |` 행으로 만들어 표에 더함 — 서브에이전트에는 보내지 않음
- **승인 대상**: `삭제`·`통합`·`흡수`·`이동`·`분할 후보` 행 — 번호·조치·문서:절·전·후를 채팅에 그대로 싣고, 사용자가 제외한 번호 외는 전부 승인
- **승인 불필요**: `재작성`·`설명`·`검증`은 `{스크래치}/approval-{날짜}.md`에만 두고 적용
- **충돌·확인 필요**: 적용하지 않고 스코프 도메인의 `inbox/{domain}.md`에 append — `!` 낡은 간선과 `areas`가 빈 `active` 노드도 `확인 필요` 행으로 남김
- **0행**: 승인 대상이 없으면 표를 제시하지 않고 4장으로

## 4. 적용 fan-out — 문서 1장 = 에이전트 1회

한 메시지에 병렬 Agent 호출, `model: sonnet`(전사와 검사만 남음). 흡수 행은 소유 문서의 에이전트가 맡고, 에이전트는 커밋하지 않습니다. 영역 통합 행은 에이전트에 보내지 않고 메인이 `registry.json`을 직접 편집합니다.

````
위키 문서 한 장에 승인된 조치를 적용하는 작업입니다. 이 문서와 지시된 흡수 조각 밖의 파일을 고치지 말고 커밋하지 마세요.

- 문서: {절대 경로}. 행: 아래 표가 편집의 전부 — `전` 줄을 찾아 `후`로 바꾸고 그 밖의 문장은 한 글자도 바꾸지 마세요. `후`가 빈 행은 `전` 줄 삭제입니다.
{이 문서의 행}
- 흡수 행: 조각 {조각 경로}의 불릿을 이 문서의 지정 절 끝에 옮기고 조각의 출처 줄을 이 문서 블록 끝으로 옮긴 뒤 조각 파일을 삭제하세요.
- 문체는 `sed -n '/^## 5\./,/^## 6\./p' {doc_contract_path}`. frontmatter updated는 {today}, verified는 `검증` 행이 있을 때만 {today}.
- 적용 뒤 행마다 `grep -cF '{후 첫 줄}' {문서}`로 반영을 확인하고(흡수는 옮긴 불릿마다), `python3 {catalog_py} --check --root {knowledge_root} {문서}` 에러가 남으면 고치고 못 고치면 `git -C {WIKI_ROOT} checkout -- {문서}`로 되돌려 blocked에 사유.

응답: 적용 행 번호, 건너뛴 행과 사유, 삭제·생성 파일, check 결과, blocked 사유.
````

## 5. 검증·커밋

- **전수 검사**: 삭제·흡수 뒤 `catalog.py --check --root {WIKI_ROOT}/knowledge` 재실행 — description 충돌은 문서 단위 검사가 보지 못함
- **커밋**: 본문이 바뀐 문서마다 `docs({domain}): {도메인 루트 기준 상대경로} audit {조치 요약}`, `verified`만 바뀐 문서는 `docs: verified 갱신 N건 (audit)` 한 커밋, 영역 통합이 있으면 `docs(graph): audit 영역 통합 N건` 한 커밋, `git pull --rebase && git push`

## 6. 보고

- **처리**: 문서 수·조치별 건수·삭제 파일
- **승인**: 승인 행 수·제외 번호
- **충돌·확인 필요·분할 후보**: 문서와 내용 — `inbox/{domain}.md`에 남긴 다음 작업
- **검사**: 남은 에러와 그 문서
