---
name: add
description: Use when material the user hands over or a decision settled in conversation must become wiki facts — a pasted spec, a read file, a fetched page, "we agreed X", or rows left in inbox.md ("위키에 정리해줘", "위키에 추가", "이거 문서로 남겨줘", "정책으로 기록해줘", "확인 필요 처리") — extracts durable facts, routes each to the domain root or the repo folder, checks against existing docs, applies grounded revisions without stopping and asks once only where a replacement states no grounds, treats the grounds rather than the preference as canonical, keeps the old value and files an inbox.md row when no grounds surface, lands the rest as 확인-tier facts with one commit per doc. NOT for merged code (that is /llm-wiki:update's job) and NOT for sweeping existing docs (that is /llm-wiki:audit's job).
---

사용자가 건넨 자료와 대화에서 확정된 사실을 위키에 반영합니다. 판정 기준은 `${CLAUDE_PLUGIN_ROOT}/references/doc-contract.md`를 먼저 읽고 따르며, 이 스킬은 순서와 정지점만 정합니다.

## 1. 입력 확정

- **입력 집합**: 붙여넣은 텍스트, 읽은 파일, 가져온 페이지, 대화에서 사용자가 직접 정한 문장, `inbox.md`의 미처리 행 — 이 밖의 사실 기록 금지
- **부재 시 질문**: 건넨 것이 없으면 무엇을 기록할지 묻고 추측하지 않음
- **큰 자료**: 한 세션에 못 담으면 장 단위로 나눠 실행하고 사실을 요약으로 줄이지 않음
- **저장소 상태**: `{WIKI_ROOT}/registry.json`이 없으면 `/llm-wiki:init`, 현재 레포가 미등록이면 `/llm-wiki:register` 안내 후 중단, 있으면 `git -C {WIKI_ROOT} pull --ff-only`

## 2. 사실 추출

- **번호 목록**: 오래 남을 사실을 번호를 매겨 나열하고 각 사실에 원문 위치(장·절·페이지)를 붙임
- **근거 표시**: 사실마다 그 값을 정한 근거(자료·판본·결정 자리와 개정·재논의·정정 중 무엇인지)를 함께 적고 입력에서 읽히지 않으면 `근거 없음`으로 둠 — 3장 교체 판정이 이 값으로 갈림
- **제외 적용**: 규약 1장의 grep 테스트·제외 판정선·자료 필터를 사실마다 적용
- **구조 분리**: 원문의 절 구조를 문서 구조로 옮기지 않고 규약 2장의 한 주제 기준으로 문서 수를 정함 — 대개 원문 하나가 문서 여럿
- **원문 내부 충돌**: 같은 주제에 두 값이 있으면 원문에 명시된 개정 일자·판본으로 신구를 가리고, 가려지지 않으면 4장 질문에 올림 — 뒤쪽이 최신이라 가정하지 않음

## 3. 위치와 대조

- **위치**: 규약 3장의 위치 판정 "이 레포를 지워도 참인가"로 도메인 루트와 레포 폴더를 가름 — 기본은 현재 레포 폴더
- **대조**: 주입된 목록의 `description` 전수와 grep으로 대상 문서를 찾고 사실마다 동일·보강·충돌을 판정
- **교체 판정**: 충돌 중 기존 값을 덮는 건은 규약 7장 근거 판정으로 근거 있음·없음을 가르고, 근거 있는 건은 4장을 거치지 않고 5장으로 감
- **기존 문서 우선**: 덮는 문서가 있으면 신규 생성 대신 그 문서 수정

## 4. 질문 — 정지점 하나

- **묻는 것**: 근거 없는 교체 행(기존 값·기존 출처·새 값 병기, 코드로 확인 가능한 값은 현재 값을 함께 제시), 원문 내부 미결 충돌, 위치가 갈리지 않는 사실을 AskUserQuestion 한 라운드로 물음 — 교체 행은 어느 값을 쓸지가 아니라 무엇이 그 값을 뒤집었는지를 묻고, 나머지 행에는 권장안을 포함
- **근거가 정본**: 답에서 개정·재논의·정정의 근거가 나오면 그 근거를 `확인` 식별자로 기록하고 다시 묻지 않음
- **미판정**: 근거가 나오지 않은 교체 행(`모름`·`알아서` 포함)은 기존 값을 유지하고 규약 7장 형식으로 `inbox.md`에 기재 — 교체가 아닌 행의 `모름`·`알아서`는 권장안 채택
- **0건 통과**: 물을 것이 없으면 멈추지 않음

## 5. 반영 — 승인 하나

- **초안**: 문서별 경로·`description`·바뀌는 절과 불릿을 보이고 승인을 받음 — 삭제·분할·이동이 있으면 그 항목을 따로 표시
- **병합**: 기존 본문을 유지하고 해당 절 끝에 불릿 추가 또는 값 교체 — 문서 전체 재작성 금지, 변경 서사 금지
- **frontmatter**: 보강·교체는 `updated`·`verified` 오늘, 동일은 `verified`만
- **출처 줄**: `> 출처: 확인 — {그 값을 정한 자료 판본 또는 결정}, {날짜}` — 근거를 댈 수 없는 값에만 `> 출처: 확인 — 사용자 확인, {오늘}`
- **신규 문서**: 규약 3·4장의 위치·골격·description으로 세우고 40자 한 문장으로 안 덮이면 나눔 — 생성한 문서가 다루는 업무 영역과 레포를 도메인 `index.md`의 `## 역인덱스`에 행으로 추가
- **index.md 보강**: 접근 좌표(호스트·환경·계정 이름)·레포 소관이 자료에서 확정되면 규약 9장 템플릿 안에서 `확인` 출처로 보강 — 사실 불릿은 index.md에 두지 않고 일반 문서로
- **deps.json**: 자료·대화에서 레포 간 의존이 확정되면 규약 10장 형식의 `확인` 간선을 추가하고 기존 간선 삭제·방향 변경은 3장 교체 판정을 거침 — 초안 승인 표에 간선 행을 `from → to — note` 꼴로 포함하고 커밋은 `docs(deps): {요약}`
- **검사·커밋**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/catalog.py" --check --root {WIKI_ROOT}/knowledge {바꾼 파일}` 에러 0 확인 후 문서마다 커밋하되 기존 값을 덮은 커밋은 규약 8장 교체 사유 한 줄을 본문에 담고, `inbox.md`의 처리한 행 삭제와 4장이 새로 기재한 행을 같은 실행의 마지막 커밋에 담은 뒤 `git pull --rebase && git push`

## 6. 보고

- **파일 목록**: 생성·수정 문서와 보강·교체·동일 건수
- **미기록**: 원본에 없어 기록하지 못한 항목, 사용자가 기존 값 유지로 답한 행, 근거 미확보로 `inbox.md`에 남긴 교체 행
- **반영 시점**: 다음 세션 목록에 반영
