---
name: audit
description: Use when the wiki must be swept after unattended updates or on a schedule ("위키 정리", "위키 감사", "문서 정리", "중복 정리") — flags fragments, duplicate facts, over-long descriptions and contract violations, then applies the rows you approve. Adds no new facts. NOT for landing new material or merged code (/llm-wiki:add, /llm-wiki:update).
---

기존 문서만 고치고 새 사실을 들이지 않습니다. 규약은 `${CLAUDE_PLUGIN_ROOT}/references/doc-contract.md`이며 서브에이전트에게는 절대 경로로 넘깁니다. 인자: `--scope {domain}|{domain}/{slug}`(기본 현재 도메인 루트 + 현재 레포), `--docs {경로...}`(지목 문서만).

## 1. 측정

- **동기화**: `git -C {WIKI_ROOT} pull --ff-only`, 실패 시 중단
- **검사·목록**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/catalog.py" --check --root {WIKI_ROOT}/knowledge` 에러와 `catalog.py --root {WIKI_ROOT}/knowledge/{domain} --shallow`·`--root {WIKI_ROOT}/knowledge/{domain}/{slug}` 목록을 `{스크래치}/catalog.md`로 저장
- **그래프**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/graph.py" check --wiki {WIKI_ROOT}`의 에러·contracts 형식 경고와 `contracts`가 상한 3건에 닿은 간선을 같은 `catalog.md`에 이어 저장 — 노드·간선은 메인이 봄
- **레포**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/update.py" mirror --repo {slug}... --wiki {WIKI_ROOT}`를 대상 도메인 레포 전부로 실행해 출력(`{slug} {미러}@{브랜치}` 또는 `{slug} 없음 — {사유}`)을 그대로 같은 `catalog.md`에 이어 저장
- **묶음**: 대상 문서를 폴더별 5~6건으로 나누고 문서마다 검사 줄을 힌트로 — 메인은 문서 본문을 열지 않음

## 2. 진단 — 묶음 1개 = 에이전트 1회

한 메시지에 병렬 Agent 호출, 모델은 메인 상속. 응답 없는 묶음은 재실행합니다.

````
위키 문서를 진단합니다. 문서를 고치거나 커밋하지 마세요.

입력: 대상 {절대 경로 5~6건}, 목록 {catalog.md}, 힌트 {문서별 --check 에러 또는 "없음"}.
기준: `sed -n '/^## 1\./,/^## 8\./p' {doc_contract_path}` — 1~7장, 1장 판정은 목록의 레포 줄로 `git -C {경로} grep {패턴} {브랜치}`·`git -C {경로} show {브랜치}:{파일}`을 실행해 수행, `없음` 레포의 불릿은 판정 생략.
금지: 레포 편집·1장 판정 밖 레포 조회, 사전 지식.

문서마다 아래 신호를 판정하고 조치 행을 씀. 값이 어긋나는 불릿 쌍은 통합하지 않고 `충돌`.

| 신호 | 조치 |
|---|---|
| 같은 문서 안 같은 주장 불릿 둘 | `통합` — 후: 조건·수치·근거를 합집합한 한 줄 |
| 규약 1장 판정에 걸리는 불릿 | `삭제` — 비고에 확인 위치 |
| 변경 서사 불릿("A에서 B로", "추후", "폐기") | 현재 상태로 쓸 수 있으면 `재작성`, 없으면 `삭제` |
| 다른 위키 문서 링크·이름 참조 | 접점 사실로 `재작성`, 남는 것이 "다른 곳에 있다"뿐이면 `삭제` |
| 레포 소관·책임·의존을 본문으로 적은 절 | `삭제` — 비고에 원문 줄(노드·간선 후보) |
| `--check` 힌트의 description 길이 에러·"때" 미종결·범주어만 | `설명` — 후: 새 문장, 상한에 안 덮이면 남길 주제로 `설명`, 떼어낼 주제마다 `옮김` |
| `--check` 힌트의 `type 없음`·type 값 에러 | `유형` — 후: 규약 1장 유형 표로 판정한 type(`adr/`는 `adr`), 본문이 두 유형이면 다수 쪽 |
| 문서 `type`과 다른 유형의 질문에 답하는 불릿 묶음 | `옮김` — 그 유형 문서로 |
| 40줄 미만이고 다른 문서 description이 이미 그 주제를 덮음 | `옮김` — 불릿 전부를 소유 문서로 |
| 절 제목과 다른 질문에 답하는 불릿 | `이동` — 후: 대상 절 |
| 레포 폴더 불릿(`adr/` 제외)이 규약 3장 위치 판정상 도메인 루트 사실 | 루트에 같은 값이 있으면 `삭제`, 다른 값이면 `충돌`, 없으면 `옮김` — 루트 문서로 |

`옮김` 행은 전: 옮길 불릿, 후: 대상에 쓸 불릿(대상 층·유형에 맞게 고쳐 씀), 비고: 규약 7장 대조로 고른 대상 `{문서 경로}:{절}`(신규면 경로·type·description)과 원 문서에 남길 잔여 불릿.

출력: 표 행만 — `| 조치 | 문서:절 | 전 | 후 | 비고 |`. 전·후는 원문 그대로(여러 줄은 <br>). 신호 없는 문서는 `없음` 한 행.
````

## 3. 승인 — 정지점 하나

- **책임 중복 행**: 같은 도메인에서 뜻이 겹치는 책임 문장 쌍을 메인이 `| 통합 | registry.json:responsibilities | {두 문장} | {남길 문장} | {고칠 노드} |` 행으로 더함
- **옮김 정리**: 묶음 사이에서 같은 주제의 신규 대상이 다른 경로·description으로 나오면 하나로 맞추고, 같은 대상에 같은 값을 넣는 `옮김`이 여럿이면 하나만 두고 나머지는 원본 `삭제`로 바꿈
- **승인 대상**: `삭제`·`통합`·`옮김`·`이동` — 번호·조치·문서:절·전·후(`옮김`은 비고의 대상까지)를 채팅에 싣고 사용자가 제외한 번호 외는 전부 승인
- **승인 불필요**: `재작성`·`설명`·`유형`은 `{스크래치}/approval.md`에만 두고 적용
- **적용 제외**: `충돌`은 적용하지 않고 6장 건너뜀 표에만
- **0행**: 승인 대상이 없으면 표 없이 4장으로

## 4. 적용 — 문서 1장 = 에이전트 1회

한 메시지에 병렬 Agent 호출, `model: sonnet`. `옮김` 행은 원본·대상 문서 에이전트 양쪽에 싣고, 책임 중복 행은 메인이 `registry.json`을 직접 편집합니다.

````
위키 문서 한 장에 승인된 조치를 적용합니다. 이 문서 밖의 파일을 고치거나 커밋하지 마세요.

입력: 문서 {절대 경로}, 행 {이 문서의 행} — `옮김` 외 행은 `전` 줄을 `후`로 치환하고 그 밖의 문장은 바꾸지 않음, `후`가 빈 행은 삭제, `유형` 행은 frontmatter `type` 줄을 `후` 값으로 넣거나 고침.
옮김: 이 문서가 대상이면 `후`를 비고의 절 끝에 추가하고 파일이 없으면 비고의 type·description으로 규약 2·4장에 맞춰 생성, 원본이면 `전`을 잔여 불릿으로 바꾸거나 지우고 불릿이 남지 않으면 파일 삭제.
문체: `sed -n '/^## 5\./,/^## 6\./p' {doc_contract_path}`.
검사: 행마다 `grep -cF '{후 첫 줄}' {문서}`(`유형` 행은 `grep -c '^type: {후}$' {문서}`, `옮김` 원본은 `grep -cF '{전 첫 줄}' {문서}`가 0), `python3 {catalog_py} --check --root {knowledge_root} {문서}` — 못 고치면 `git -C {WIKI_ROOT} checkout -- {문서}`(신규는 삭제)로 되돌리고 blocked에 사유.

응답: 적용 행 번호, 건너뛴 행과 사유, 삭제·생성 파일, check 결과, blocked 사유.
````

## 5. 검증·커밋·push

- **옮김 묶음**: `옮김` 행으로 이어진 원본·대상 문서 전체를 한 묶음으로 보고, 묶음 안 문서 하나라도 blocked이거나 `옮김` 행을 건너뛰었으면 묶음 전체를 `git -C {WIKI_ROOT} checkout -- {문서}`(신규는 삭제)로 되돌리고 6장 검사에 보고
- **전수 검사**: 삭제·옮김 뒤 `catalog.py --check --root {WIKI_ROOT}/knowledge` 재실행 — description 중복은 문서 단위 검사가 보지 못함
- **커밋**: 본문이 바뀐 문서마다 `docs({domain}): {도메인 루트 기준 상대경로} audit {조치 요약}`, 책임 통합은 `docs(graph): audit 책임 통합 N건` 한 커밋
- **push**: `git -C {WIKI_ROOT} pull --rebase && git push` — 실패는 로컬 커밋 상태와 함께 보고

## 6. 보고

- **처리**: 문서 수·조치별 건수·삭제·생성 파일
- **승인**: 승인 행 수·제외 번호
- **건너뜀**: 3장 적용 제외 행을 규약 8장 건너뜀 표로
- **그래프 경고**: `graph.py check` 에러·contracts 형식 경고와 상한에 닿은 간선
- **검사**: 남은 에러와 그 문서
