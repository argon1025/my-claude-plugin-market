---
name: add
description: Use when material the user hands over or a decision settled in conversation must become facts in the wiki — a pasted spec, a read file, a fetched page, "we agreed X", or a row skipped in an update report ("위키에 정리해줘", "위키에 추가", "이거 문서로 남겨줘", "정책으로 기록해줘", "건너뜀 처리"). New facts land directly; a fact that differs from an existing value shows both values and lets you choose. NOT for merged code (/llm-wiki:update) and NOT for sweeping existing docs (/llm-wiki:audit).
---

사용자가 건넨 자료와 대화에서 확정된 사실을 위키에 반영합니다. 판정 기준은 `${CLAUDE_PLUGIN_ROOT}/references/doc-contract.md`이며 이 스킬은 순서와 정지점만 정합니다.

## 1. 입력 확정

- **입력 집합**: 붙여넣은 텍스트, 읽은 파일, 가져온 페이지, 대화에서 사용자가 정한 문장, update 보고의 건너뜀 표 행 — 이 밖의 사실 기록 금지
- **부재 시 질문**: 건넨 것이 없으면 무엇을 기록할지 묻고 추측하지 않음
- **큰 자료**: 한 세션에 못 담으면 장 단위로 나눠 실행하고 요약으로 줄이지 않음
- **저장소 상태**: `{WIKI_ROOT}/registry.json`이 없으면 `/llm-wiki:init`, 현재 레포가 미등록이면 `/llm-wiki:register` 안내 후 중단, 있으면 `git -C {WIKI_ROOT} pull --ff-only` — 충돌·분기는 멈추고 보고

## 2. 사실 추출

- **번호 목록**: 사실마다 번호와 원문 위치(장·절·페이지)
- **제외 적용**: 규약 1장을 사실마다 적용하고 화면 시안, UI 문구 원문, 일정·담당자, "검토 중" 항목도 제외
- **구조 분리**: 원문 절 구조를 옮기지 않고 규약 2장 한 주제 기준으로 문서 수를 정함
- **원문 내부 충돌**: 같은 주제에 두 값이 있으면 원문의 개정 일자·판본으로 가리고, 가려지지 않으면 4장 질문 — 뒤쪽이 최신이라 가정하지 않음

## 3. 위치와 대조

- **위치**: 규약 3장 위치 판정과 레포 편차 — 기본은 현재 레포 폴더
- **대조**: 규약 7장으로 동일·추가·교체 후보를 가름
- **기존 문서 우선**: 덮는 문서가 있으면 신규 대신 그 문서 수정

## 4. 질문 — 정지점 하나

- **묻는 것**: 교체 후보 행(기존 값·새 값과 코드로 확인 가능한 현재 값 병기), 원문 내부 미결 충돌, 위치가 갈리지 않는 사실을 AskUserQuestion 한 라운드로 — 교체 외 행에는 권장안 포함
- **모름**: 교체 행의 `모름`은 기존 값 유지 후 보고에만, 그 밖의 행은 권장안 채택
- **0건 통과**: 물을 것이 없으면 멈추지 않음

## 5. 반영 — 승인 하나

- **초안**: 문서별 경로·`description`·바뀌는 절과 불릿, 노드 변경 행과 간선 행(`{kind} {from} → {to} — {contracts}`)을 보이고 승인 — 삭제·분할·이동은 따로 표시
- **병합**: 규약 7장 병합 방식, 신규 문서는 규약 2~4장
- **노드·간선**: 레포 소관·책임·호스트·프로젝트와 레포 간 의존이 확정되면 규약 9·10장 형식으로 `registry.json`·`deps.json` 편집 — 기존 값 교체·삭제는 4장 선택을 거침, 커밋은 `docs(graph): {요약}`
- **검사·커밋**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/catalog.py" --check --root {WIKI_ROOT}/knowledge {바꾼 파일}`(노드·간선을 고쳤으면 `{WIKI_ROOT}/registry.json`·`{WIKI_ROOT}/deps.json`도) 에러 0 뒤 문서마다 커밋, 본문은 규약 8장
- **push**: `git -C {WIKI_ROOT} pull --rebase && git push` — 실패는 로컬 커밋 상태와 함께 보고

## 6. 보고

- **파일 목록**: 생성·수정 문서와 동일·추가·교체 건수
- **미기록**: 원본에 없어 기록하지 못한 항목, 기존 값을 유지한 교체 행은 규약 8장 건너뜀 표로
- **반영 시점**: push 뒤 다음 세션 목록에 반영
