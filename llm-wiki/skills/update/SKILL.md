---
name: update
description: Use when merged code in repos registered in the wiki must be reflected ("위키 업데이트", "무인 갱신", "머지 반영", "최근 머지 위키에 반영", a scheduled run, or a pointed --repo/--range) — unattended; takes pending merges across all domains in merge-time order, adds new facts, replaces an existing value only when a plan·feedback·commit message quote states the intent, skips the rest into the final report, and advances cursors. NOT for material the user hands over (/llm-wiki:add) and NOT for sweeping existing docs (/llm-wiki:audit).
disable-model-invocation: true
---

등록 레포의 머지된 코드를 위키에 무인으로 반영합니다. 사용자에게 묻지 않습니다. 판정 기준은 `${CLAUDE_PLUGIN_ROOT}/references/doc-contract.md`이며 서브에이전트에게는 `${CLAUDE_PLUGIN_ROOT}`를 전개한 절대 경로로 넘깁니다.

인자: `--repo {slug}`(대상 한정, 반복 가능), `--range {rev-range}`(지목 범위, 커서 불변), `--max-merges N`(전역 예산, 기본 40), `--batch-merges N`·`--batch-bytes N`(추출 묶음 상한, 기본 5건·500,000바이트), `--baseline-days N`(커서 없는 레포 소급), `--dry-run`(3장까지).

## 1. 범위

- **동기화**: `git -C {WIKI_ROOT} pull --ff-only` — 실패하면 보고 후 중단(팀원 커밋과 갈라진 상태에서 무인 편집 금지)
- **유형 검사**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/catalog.py" --check --root {WIKI_ROOT}/knowledge`에 `type`이 들어간 에러(없음·규약에 없는 값·adr 위치 불일치)가 있으면 해당 문서 목록과 "먼저 `/llm-wiki:audit`"를 보고 후 중단 — type 에러 문서에 반영하면 6장 되돌림에 걸려 사실이 보고 없이 사라짐
- **실행**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/update.py" pending --wiki {WIKI_ROOT} --out {스크래치} {인자}` — 전 도메인 미처리 머지를 시각 순으로 골라 diff 파일·레포별 `commits`·`batches[{id, shas, bytes}]`·`remaining`과 전역 순서 `order[{slug, sha7, date}]`를 `work.json`에 씀, 묶음은 다시 나누지 않음
- **종료 코드**: 0 작업 또는 부트스트랩 있음(`work.json`만 Read), 10 미처리 없음(한 줄 보고 후 종료), 1 오류(stderr 전달 후 중단)
- **이월**: `skipped`(로컬 경로 없음·force-push 의심·대상 ref 없음·휴면)와 `notes`는 그대로 보고로
- **부트스트랩**: 커서 없던 레포는 머지 0건이어도 6장에서 HEAD를 커서로 기록

## 2. 추출 — 묶음 1개 = 에이전트 1회

레포별 `batches`마다 한 메시지에 병렬 Agent 호출, `model: sonnet`, 출력은 파일, 응답은 건수만. 묶음이 하나뿐이고 머지 3건 이하면 메인이 직접 처리하고, 응답 없는 묶음은 3장 전에 재실행합니다. 스키마 자리에는 `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/graph.py" schema --for facts --domain {그 레포의 도메인}` 출력을 그대로 싣습니다.

````
머지 묶음 1개에서 위키에 남길 사실을 추출합니다.

입력: 아래 diff 파일 {N}개를 순서대로 Read — {diff_path 목록}. 머리말에 커밋 메시지·변경 파일 목록·절단 여부가 있음.
기준: `sed -n '/^## 1\. 담는 것/,/^## 2\./p' {doc_contract_path}` — 후보 문장마다 적용. 레포 간 호출·소비는 facts가 아니라 deps.
금지: 다른 파일 열기, 사전 지식으로 채우기.
병합: 묶음 안 같은 주장은 하나로 합치고 shas에 모두 적음, 값이 다른 두 사실은 둘 다 남김.

{graph.py schema --for facts 출력}

출력: {facts_dir}/{slug}/{batch_id}.json에 Write — 위 키에 facts를 더한 객체 1개.
{"facts": [{"fact": "현재 상태 한 문장(업무 낱말 우선, 식별자 괄호 병기, 줄바꿈 금지)",
            "type": "policy|domain|convention|external|procedure — 기준의 유형 표에서 하나",
            "topic": "2~4낱말 주제",
            "code": "저장소 상대 경로 또는 파일#심볼",
            "quote": "기존 동작을 바꾸는 사실이면 그 의도를 밝힌 plan·feedback·커밋 메시지 원문 — 그 레포만의 사정인지 합의 변경인지 드러나는 문장 우선, 없으면 빈 문자열",
            "shas": ["근거 머지 sha7"]}]}
빈 항목은 []. 응답은 키별 건수만.
````

## 3. 배정 — 메인 전담

- **입력**: `{facts_dir}/**/*.json` 전부 — 묶음 사이 같은 주장은 하나로 합치고 `shas`는 합집합, `type`이 다르면 다른 사실
- **시각 순**: 사실마다 `order`에서 가장 늦은 근거 머지의 `date`를 붙이고 문서별로 오름차순 정렬
- **위치·대조**: 규약 3장으로 층(도메인 루트·레포 폴더)을 정하고 그 층에서 7장 대조·레포 편차 — 목록은 `catalog.py --root {WIKI_ROOT}/knowledge/{domain} --shallow`와 `--root {WIKI_ROOT}/knowledge/{domain}/{slug}`, 후보는 그 층에서 행의 `[type]`이 사실의 `type`과 같은 문서만
- **신규 문서**: 대상이 없는 사실은 같은 층·같은 `type`끼리 주제로 묶어 규약 2장 한 주제가 서면 신규 1장(행에 `type` 기록), 서지 않으면 `기각 — 한 주제 아님`
- **간선 상대**: 규약 10장 대상 판정 — 못 정하면 `기각 — 상대 미정`과 식별자 원문, 규약 10장 선언 위치를 어기면 `기각 — 선언 위치`
- **간선 배정**: `from_me`로 끝점을 잡아 간선을 더하거나 같은 `(to, kind)`의 `contracts`에 식별자를 보탬 — 상한 3건을 넘으면 접거나 `기각 — contracts 상한`, 기존 식별자 교체는 규약 7장 조건
- **책임·호스트**: 현재 노드에 없으면 추가, 뜻이 다른 기존 값은 규약 7장 판정
- **배정표**: `{스크래치}/assign.json`에 문서별 `type`·사실 목록(시각 순)·신규 여부와 `graph` 배정 — `--dry-run`이면 보고하고 종료

## 4. 반영 — 문서 1장 = 에이전트 1회

한 메시지에 병렬 Agent 호출, `model: sonnet`, 에이전트는 커밋하지 않습니다. `registry.json`·`deps.json`은 메인이 규약 9·10장과 `graph.py check` 규칙대로 직접 편집합니다.

````
위키 문서 한 장에 사실 여러 건을 반영합니다.

입력: {assign_path}의 "{doc}" 항목 — 문서 경로·type·신규 여부·사실 행(id·fact·type·topic·code·quote·slug·shas·date).
기준: `sed -n '/^## 3\./,/^## 8\./p' {doc_contract_path}` — 3~7장.
판정: 사실을 주어진 순서대로 7장 판정 적용 — 동일·추가·교체는 본문에 반영, 건너뜀은 본문을 고치지 않고 skipped에.
신규 문서: 규약 2장, frontmatter `type`은 항목의 type.
금지: 이 문서 밖 파일 편집, 코드 저장소 조회, 사전 지식.

출력: {applied_dir}/{doc_slug}.json에 Write —
{"doc","created","verdicts":[{"id","verdict":"동일|추가|교체","heading"}],"skipped":[{"id","기존 값","새 값","slug","sha"}]}
응답은 판정별 건수만.
````

## 5. 검토 — 문서 1장 = 에이전트 1회

한 메시지에 병렬 Agent 호출, 모델은 메인 상속, 에이전트는 커밋하지 않습니다. 근거 자리에는 그 문서 사실 행의 `slug`마다 `work.json` `repos[slug].path`와 `shas` 중 가장 늦은 머지를 싣습니다.

````
방금 사실을 반영한 위키 문서 한 장에서 규약 위반만 고칩니다.

입력: 문서 {doc_abs}, 이번 변경 `git -C {WIKI_ROOT} diff -- {doc_abs}`(신규 문서는 전체), 근거 레포·머지 {repo_path}@{sha} 목록, 도메인 루트 목록 `python3 {catalog_py} --root {WIKI_ROOT}/knowledge/{domain} --shallow`.
기준: `sed -n '/^## 1\./,/^## 8\./p' {doc_contract_path}` — 1~7장, 1장 판정은 `git -C {repo_path} grep {패턴} {sha}`·`git -C {repo_path} show {sha}:{경로}`로 머지 시점 레포를 읽어 수행.
범위: 이번 변경 줄과 description만 — 기존 줄은 audit 몫.
금지: 새 사실 추가, 이 문서 밖 편집.

유형: 새 불릿이 문서 frontmatter `type`과 다른 유형의 질문(규약 1장 유형 표)에 답하면 삭제하고 reason `유형 불일치`.

출력: {review_dir}/{doc_slug}.json에 Write — {"doc","removed":[{"bullet","reason"}]}. 응답은 건수만.
````

## 6. 검증·커밋·커서·push

- **전수 검사**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/catalog.py" --check --root {WIKI_ROOT}/knowledge` — 손대지 않은 문서의 에러는 고치지 않고 보고
- **되돌림**: `--check` 에러가 남은 편집 문서는 `git -C {WIKI_ROOT} checkout -- {경로}`로 원복(신규는 삭제)해 `검사 실패` 기각으로, 검토로 본문이 빈 신규 문서도 삭제
- **문서 커밋**: 문서마다 `docs({domain}): {도메인 루트 기준 상대경로} {요약}`, 본문은 규약 8장
- **커서**: 레포마다 전역 선택 안에서 처리한 마지막 머지까지 `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/update.py" advance {slug} {sha} --wiki {WIKI_ROOT}` — 되돌린 묶음이 있으면 그 첫 머지 직전까지, 사실 0건 머지도 전진, `--range`는 불변, 레포마다 `chore(update): {slug} 커서 {sha7} · 머지 N건`
- **그래프 커밋**: 노드·간선이 바뀌면 `docs(graph): 간선 N건 · 책임 M건 · 호스트 K건` 한 커밋, 본문은 규약 8장
- **push**: `git -C {WIKI_ROOT} pull --rebase && git push` — 재시도 2회, 실패는 로컬 커밋 상태와 함께 보고

## 7. 보고

- **레포별**: 처리 머지 수·커서 전후·`skipped` 사유
- **문서**: 생성·수정 목록과 동일·추가·교체 건수
- **그래프**: 간선·책임·호스트 건수와 `상대 미정` 목록
- **건너뜀**: 반영 에이전트의 `skipped`와 3장 건너뜀을 규약 8장 건너뜀 표로 — `/llm-wiki:add`로 처리
- **삭제**: 5장 `removed`를 `| 문서 | 삭제 불릿 | 사유 |` 표로 — 오삭제 복구 근거
- **기각**: 사유별 건수(한 주제 아님·선언 위치·상대 미정·검사 실패)
