---
name: update
description: Use when merged code in registered repos must be reflected into the wiki ("위키 업데이트", "무인 갱신", "머지 반영", "최근 머지 위키에 반영", a scheduled run, or a pointed --domain/--repo/--range) — asks once which domains to document then walks that domain's registered repos from their cursors (skipping the question for --domain/--repo/--range/--all runs), fans out one subagent per merge batch (5 merges or 500KB of diff) to extract facts, assigns facts to the domain root, the repo folder and index.md against the catalogs, fans out one subagent per doc to apply, runs --check, commits per doc, advances the cursor, pushes. 관찰-tier only: confirms and adds, never overwrites; conflicts go to inbox/{domain}.md. NOT for material the user hands over (that is /llm-wiki:add's job) and NOT for sweeping existing docs (that is /llm-wiki:audit's job).
disable-model-invocation: true
---

등록된 레포의 머지된 코드를 도메인 루트와 레포 폴더에 반영합니다. 대상 도메인 확인 1회 외에는 사용자 응답 없이 진행합니다. 판정 기준은 `${CLAUDE_PLUGIN_ROOT}/references/doc-contract.md`가 정본이며 서브에이전트에게는 `${CLAUDE_PLUGIN_ROOT}`를 전개한 절대 경로로 넘깁니다. 이 스킬은 `관찰` 출처만 만들므로 기존 값을 지우거나 바꾸지 않습니다.

인자: `--domain {name}`(대상 도메인 한정, 반복 가능), `--all`(전체 도메인, 질문 생략), `--repo {slug}`(대상 한정), `--range {rev-range}`(지목 범위, 커서 불변), `--max-merges N`(레포별 예산, 기본 20), `--batch-merges N`·`--batch-bytes N`(추출 묶음 상한, 기본 5건·500,000바이트), `--baseline-days N`(커서 없는 레포 소급), `--dry-run`(3장까지).

## 1. 범위 확정

- **동기화**: `git -C {WIKI_ROOT} pull --ff-only` — 실패하면 보고 후 중단(팀원 커밋과 갈라진 상태에서 무인 편집 금지)
- **대상 도메인**: `--domain`·`--repo`·`--range`·`--all` 중 하나라도 있으면 생략, 없으면 `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/update.py" domains --wiki {WIKI_ROOT}` 출력을 그대로 보이고 AskUserQuestion으로 도메인을 고르게 함(복수 선택 가능) — 고른 이름을 `--domain`으로 다음 불릿에 넘기며, 등록 도메인이 하나뿐이어도 묻고, 사용자가 답하지 않으면 실행하지 않음
- **실행**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/update.py" pending --wiki {WIKI_ROOT} --out {스크래치} {인자}` — 레포별 커서 이후 first-parent 커밋 목록·머지별 diff 파일·추출 묶음(`batches[{id, shas, bytes}]`)을 만들고 `work.json` 경로를 마지막 줄에 냄. 묶음 경계는 이 스크립트가 정하며 스킬이 다시 묶지 않음
- **종료 코드**: 0 작업 또는 부트스트랩 있음(`work.json`만 Read), 10 미처리 없음(한 줄 보고 후 종료), 1 오류·미등록 도메인(stderr 전달 후 중단)
- **건너뜀**: `work.json`의 `skipped`(로컬 경로 없음·force-push 의심·대상 ref 없음)와 `notes`는 그대로 보고에 옮김
- **부트스트랩**: 커서 없던 레포는 커밋 0건이라도 5장에서 HEAD를 커서로 기록함
- **입력 집합**: 추출된 diff와 그 범위의 커밋 메시지·함께 커밋된 노트만 — 범위 밖 작업 트리·사전 지식·현재 코드 재조회로 채우지 않음

## 2. 추출 fan-out — 묶음 1개 = 에이전트 1회

`work.json`의 레포별 `batches`마다 한 메시지에 병렬 Agent 호출, `model: sonnet`, 출력은 파일 Write, 응답은 건수만 — 사실이 메인 컨텍스트를 지나지 않아야 한 세션이 수십 건을 처리합니다. 묶음이 하나뿐이고 머지 3건 이하면 메인이 직접 처리하고, 응답 없는 묶음은 3장 전에 재실행합니다.

````
머지 묶음 1개에서 오래 남을 사실을 추출하는 작업입니다. 위키 문서 작성이 아니라 사실 목록 기록입니다.

- diff: 아래 파일 {N}개를 순서대로 Read로 읽으세요 — {diff_path 목록}. 각 머리말에 커밋 메시지·변경 파일 목록·절단 여부가 있습니다.
- 커밋 메시지와 diff에 함께 실린 .md 노트도 근거입니다 — 결정 근거 문장은 원문 그대로 quote에 옮기세요.
- 코드 저장소의 다른 파일을 열지 마세요. 사전 지식으로 공백을 채우지 마세요.
- 묶음 안에서 같은 주장을 하는 사실은 하나로 합치고 shas에 근거 머지를 모두 적으세요. 값이 다른 두 사실은 합치지 말고 둘 다 남기세요.

기록 기준은 규약 원문입니다 — `sed -n '/^## 1\. 담는 것/,/^## 2\./p' {doc_contract_path}`를 읽고 후보 문장마다 적용하세요.
코드 검색 한 번으로 확인되는 문장(시그니처·타입·enum·파일 위치·호출 관계·한 심볼의 내부 동작)과
이번 변경의 서사("A를 B로 바꿈")는 사실이 아닙니다. 남는 것은 코드에 없는 결정·제약·금지·외부 계약·컨벤션입니다.

출력: {facts_dir}/{slug}/{batch_id}.json에 Write — 객체 1개 = 사실 1건.
[{"fact": "현재 상태를 말하는 한 문장(업무 낱말 우선, 식별자는 괄호 병기, 줄바꿈 금지)",
  "topic": "2~4낱말 주제",
  "code": "저장소 상대 경로 또는 파일#심볼 — 필수",
  "quote": "커밋 메시지·노트의 결정 근거 원문 — 있을 때만",
  "shas": ["근거 머지 sha7 — 1개 이상"]}]
사실 0건이면 []을 쓰세요. 응답은 사실 건수만 반환하세요.
````

## 3. 배정 — 메인 세션 전담

- **입력**: `{facts_dir}/**/*.json`을 전부 읽음 — 사실 문장이 메인을 지나는 유일한 지점
- **중복 병합**: 묶음 사이에서 같은 주장을 하는 사실은 하나로 합치고 `shas`를 합집합으로 — 묶음 안 병합은 2장이 이미 함
- **위치**: 규약 3장 위치 판정 "이 레포를 지워도 참인가"를 사실마다 한 번 물어 도메인 루트와 레포 폴더를 가르고 둘 다 직접 편집
- **대조**: 도메인 루트 목록(`catalog.py --root {WIKI_ROOT}/knowledge/{domain} --shallow`)과 레포 목록(`--root {WIKI_ROOT}/knowledge/{domain}/{slug}`)의 `description` 전수와 grep으로 대상 문서를 찾음 — 후보가 둘이면 범위가 좁은 문서
- **신규 문서**: 대상이 없는 사실은 주제로 묶어 40자 한 문장으로 덮이면 신규 1장, 덮이지 않으면 나누고 그래도 서지 않으면 `기각 — 한 주제 아님`
- **배치 내 상충**: 같은 주제에 값이 다른 사실 둘은 둘 다 그 레포 도메인의 `inbox/{domain}.md`
- **index.md 배정**: 신규 문서가 생기면 그 업무 영역·레포를 `## 역인덱스` 행으로, diff에서 레포 역할·접근 좌표(호스트·환경 이름)가 확정되면 `## 레포 구성`·`## 접근 좌표` 보강으로 도메인 `index.md`에 배정 — index.md도 문서 1장으로 4장 에이전트 1회
- **deps.json 배정**: diff에서 레포 간 의존(빌드 파일의 모듈 의존·HTTP·Feign 클라이언트·AMQP 발신·DB 공유)이 확정되고 양 끝이 등록 레포면 규약 10장 형식의 `관찰` 간선으로 배정하고, 한쪽이 미등록이면 `기각 — 미등록 레포`
- **배정표**: `{스크래치}/assign.json`에 문서별 사실 목록·신규 여부를 씀 — `--dry-run`이면 배정표를 보고하고 종료

## 4. 반영 fan-out — 문서 1장 = 에이전트 1회

한 메시지에 병렬 Agent 호출, `model: sonnet`. 같은 파일을 두 에이전트가 고치지 않게 문서 단위로 묶고, 에이전트는 커밋하지 않습니다. `deps.json`은 문서가 아니므로 에이전트에 보내지 않고 메인이 규약 10장의 유일성·정렬 규칙대로 직접 편집합니다.

````
위키 문서 한 장에 사실 여러 건을 대조·반영하는 작업입니다. 이 문서 밖의 파일을 고치지 말고 커밋하지 마세요.

- 배정: {assign_path}의 "{doc}" 항목을 읽으세요 — 문서 경로·신규 여부·사실 행(fact·topic·code·quote·slug·shas·머지 날짜).
- 입력 집합은 이 파일이 전부입니다. 코드 저장소를 조회하지 말고 사전 지식으로 채우지 마세요. 오늘은 {today}입니다.
- 규약 전문을 Read {doc_contract_path}로 읽고 4·5·7장을 그대로 적용하세요. 문서가 index.md면 9장 템플릿 안에서만 행을 더하고 사실 불릿을 넣지 마세요.

기존 문서: 본문을 열어 사실마다 값 단위로 판정하세요.
- 동일 — 본문 유지, frontmatter verified만 {today}. code가 그 값 자체를 짚었을 때만이며 주제가 겹친다는 이유로 올리지 마세요.
- 보강 — 해당 절 끝에 불릿 추가, updated·verified {today}. 문서 전체 재작성 금지.
- 충돌 — 기존 값과 다르면 본문을 고치지 말고 excluded에 {기존 값(절), 기존 출처 줄 전사, 새 값, code}를 적으세요. 관찰은 기존 값을 지우지 못합니다.
신규 문서: description은 40자 목표·60자 상한·"때" 종결·이 문서에서만 참인 낱말 1개, 
채울 사실 없는 절은 두지 않고, 제목은 사실이 실제로 답하는 범위로만 — 조각에 주제 이름을 붙이지 마세요. 레포 폴더 문서의 description에 레포명을 넣지 마세요.

공통: 다른 위키 문서 이름·링크 금지, 변경 서사 금지, 업무 낱말 먼저. 업무 낱말을 붙일 수 없는 식별자만 남는 행은 blocked "내부 동작 서술".
출처 줄: 블록 끝에 `> 출처: 관찰 — {slug} @{sha7} 머지, {머지 날짜}`(shas 중 최신 머지)를 두고 같은 레포의 옛 관찰 줄은 이 줄로 대체하세요.
검사: `python3 {catalog_py} --check --root {knowledge_root} {doc_abs}` — 에러가 남으면 고치고, 못 고치면 편집을 되돌리고 blocked에 사유.

출력: {applied_dir}/{doc_slug}.json에 Write —
{"doc","created","verdicts":[{"id","verdict":"동일|보강","heading"}],"excluded":[{"id","기존 값","기존 출처","새 값","code"}],"blocked":null|"사유","check":"pass|fail"}
응답은 판정별 건수만 반환하세요.
````

## 5. 검증·커밋·커서

- **전수 검사**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/catalog.py" --check --root {WIKI_ROOT}/knowledge` — 이번에 손대지 않은 문서의 에러는 고치지 않고 보고에 남김
- **되돌림**: `blocked`·`check: fail` 문서는 `git -C {WIKI_ROOT} checkout -- {경로}`로 원복하고 그 사실은 보고의 `기각`, 되돌린 머지가 있으면 커서는 그 머지 직전까지만
- **inbox/{domain}.md**: `excluded`(충돌)·배치 내 상충 행만 `- [{날짜}] [{domain}] {주제} — 기존 {값} ({파일:절}, {출처}) / 새 {값} ({slug} @{sha7} {code})` 형식으로 그 레포 도메인 파일에 append — 파일이 없으면 만들고, 여러 도메인을 한 실행에서 처리하면 도메인별 파일에 각각 씀
- **커밋**: 문서마다 `docs({domain}): {도메인 루트 기준 상대경로} {요약}`, 그 뒤 `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/update.py" advance {slug} {sha} --wiki {WIKI_ROOT}`로 `state/{slug}.json` 갱신 + 그 도메인의 `inbox/{domain}.md`를 `chore(update): {slug} 커서 {sha7} · 머지 N건 · 문서 M건` 한 커밋(N·M은 스킬이 셈) — 사실 0건 머지도 전진, 예산으로 잘린 머지 앞에서 멈춤, 되돌린 묶음이 있으면 그 묶음 첫 머지 직전까지만, `--range` 실행은 커서 불변
- **deps.json 커밋**: 간선이 바뀌면 `docs(deps): 간선 N건 · {slug} @{sha7}` 한 커밋 — 문서 커밋과 섞지 않음
- **push**: `git -C {WIKI_ROOT} pull --rebase && git push` — 재시도 2회, 실패는 로컬 커밋 상태와 함께 보고

## 6. 보고

- **범위**: 이번 실행의 대상 도메인과 그 선택이 질문·인자 중 무엇으로 정해졌는지 한 줄
- **레포별**: 처리 머지 수·사실 수·커서 전후·건너뜀 사유
- **문서**: 생성·수정 목록과 동일·보강 건수, `deps.json` 간선 추가 건수
- **확인 필요**: `inbox/{domain}.md`에 남긴 행 전부 — 이 실행이 사람에게 남기는 판정 요청이며 `/llm-wiki:add`로 집음
- **기각**: 사유별 건수(담지 않는 것·한 주제 아님·내부 동작 서술·검사 실패)
- **후속**: 신규 문서 목록과 `/llm-wiki:audit` 권고
