---
name: audit
description: Use when the wiki must be swept after unattended updates or on a schedule ("위키 정리", "위키 감사", "문서 정리", "중복 정리") — flags fragments, duplicate facts, over-long descriptions and contract violations, then applies the rows you approve. Adds no new facts. NOT for landing new material or merged code (/llm-wiki:add, /llm-wiki:update).
---

기존 문서만 고치고 새 사실을 들이지 않습니다. 규약은 `${CLAUDE_PLUGIN_ROOT}/references/doc-contract.md`이며 서브에이전트에게는 절대 경로로 넘깁니다. 인자: `--scope {domain}|{domain}/{slug}`(기본 현재 도메인 루트 + 현재 레포), `--docs {경로...}`(지목 문서만).

## 1. 측정

- **동기화**: `git -C {WIKI_ROOT} pull --ff-only`, 실패 시 중단
- **검사·목록**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/catalog.py" --check --root {WIKI_ROOT}/knowledge` 에러와 `catalog.py --root {WIKI_ROOT}/knowledge/{domain} --shallow`·`--root {WIKI_ROOT}/knowledge/{domain}/{slug}` 목록을 `{스크래치}/catalog.md`로 저장
- **그래프**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/graph.py" check --wiki {WIKI_ROOT}`의 에러·contracts 형식 경고와 `contracts`가 상한 3건에 닿은 간선을 같은 `catalog.md`에 이어 저장 — 노드·간선은 메인이 봄
- **묶음**: 대상 문서를 폴더별 5~6건으로 나누고 문서마다 검사 줄을 힌트로 — 메인은 문서 본문을 열지 않음

## 2. 진단 — 묶음 1개 = 에이전트 1회

한 메시지에 병렬 Agent 호출, 모델은 메인 상속. 응답 없는 묶음은 재실행합니다.

````
위키 문서를 진단합니다. 문서를 고치거나 커밋하지 마세요.

입력: 대상 {절대 경로 5~6건}, 목록 {catalog.md}, 힌트 {문서별 --check 에러 또는 "없음"}.
기준: `sed -n '/^## 1\./,/^## 8\./p' {doc_contract_path}` — 1~7장.
금지: 코드 저장소 조회, 사전 지식.

문서마다 아래 신호를 판정하고 조치 행을 씀. 값이 어긋나는 불릿 쌍은 통합하지 않고 `충돌`.

| 신호 | 조치 |
|---|---|
| 같은 문서 안 같은 주장 불릿 둘 | `통합` — 후: 조건·수치·근거를 합집합한 한 줄 |
| 한 레포 코드 검색 한 번으로 참이 확인되는 불릿(규약 1장) | `삭제` — 비고에 확인 위치 |
| 변경 서사 불릿("A에서 B로", "추후", "폐기") | 현재 상태로 쓸 수 있으면 `재작성`, 없으면 `삭제` |
| 다른 위키 문서 링크·이름 참조 | 접점 사실로 `재작성`, 남는 것이 "다른 곳에 있다"뿐이면 `삭제` |
| 레포 소관·책임·의존을 본문으로 적은 절 | `삭제` — 비고에 원문 줄(노드·간선 후보) |
| `--check` 힌트의 description 길이 에러·"때" 미종결·범주어만 | `설명` — 후: 새 문장, 상한에 안 덮이면 `분할 후보` |
| 40줄 미만이고 다른 문서 description이 이미 그 주제를 덮음 | `흡수` — 후: 소유 문서 경로와 절, 비고에 옮길 불릿 |
| 절 제목과 다른 질문에 답하는 불릿 | `이동` — 후: 대상 절 |

출력: 표 행만 — `| 조치 | 문서:절 | 전 | 후 | 비고 |`. 전·후는 원문 그대로(여러 줄은 <br>). 신호 없는 문서는 `없음` 한 행.
````

## 3. 승인 — 정지점 하나

- **책임 중복 행**: 같은 도메인에서 뜻이 겹치는 책임 문장 쌍을 메인이 `| 통합 | registry.json:responsibilities | {두 문장} | {남길 문장} | {고칠 노드} |` 행으로 더함
- **승인 대상**: `삭제`·`통합`·`흡수`·`이동`·`분할 후보` — 번호·조치·문서:절·전·후를 채팅에 싣고 사용자가 제외한 번호 외는 전부 승인
- **승인 불필요**: `재작성`·`설명`은 `{스크래치}/approval.md`에만 두고 적용
- **적용 제외**: `충돌`은 적용하지 않고 6장 건너뜀 표에만
- **0행**: 승인 대상이 없으면 표 없이 4장으로

## 4. 적용 — 문서 1장 = 에이전트 1회

한 메시지에 병렬 Agent 호출, `model: sonnet`. 흡수 행은 소유 문서의 에이전트가 맡고, 책임 중복 행은 메인이 `registry.json`을 직접 편집합니다.

````
위키 문서 한 장에 승인된 조치를 적용합니다. 이 문서와 지시된 흡수 조각 밖의 파일을 고치거나 커밋하지 마세요.

입력: 문서 {절대 경로}, 행 {이 문서의 행} — `전` 줄을 `후`로 치환하고 그 밖의 문장은 바꾸지 않음, `후`가 빈 행은 삭제.
흡수: 조각 {조각 경로}의 불릿만 이 문서의 지정 절 끝에 옮기고 조각 파일 삭제.
문체: `sed -n '/^## 5\./,/^## 6\./p' {doc_contract_path}`.
검사: 행마다 `grep -cF '{후 첫 줄}' {문서}`, `python3 {catalog_py} --check --root {knowledge_root} {문서}` — 못 고치면 `git -C {WIKI_ROOT} checkout -- {문서}`로 되돌리고 blocked에 사유.

응답: 적용 행 번호, 건너뛴 행과 사유, 삭제·생성 파일, check 결과, blocked 사유.
````

## 5. 검증·커밋·push

- **전수 검사**: 삭제·흡수 뒤 `catalog.py --check --root {WIKI_ROOT}/knowledge` 재실행 — description 중복은 문서 단위 검사가 보지 못함
- **커밋**: 본문이 바뀐 문서마다 `docs({domain}): {도메인 루트 기준 상대경로} audit {조치 요약}`, 책임 통합은 `docs(graph): audit 책임 통합 N건` 한 커밋
- **push**: `git -C {WIKI_ROOT} pull --rebase && git push` — 실패는 로컬 커밋 상태와 함께 보고

## 6. 보고

- **처리**: 문서 수·조치별 건수·삭제 파일
- **승인**: 승인 행 수·제외 번호
- **건너뜀**: 3장 적용 제외 행을 규약 8장 건너뜀 표로
- **분할 후보**: 문서와 내용
- **그래프 경고**: `graph.py check` 에러·contracts 형식 경고와 상한에 닿은 간선
- **검사**: 남은 에러와 그 문서
