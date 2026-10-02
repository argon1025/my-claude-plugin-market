# 위키 반영 절차

update·add 스킬이 사실을 추출한 뒤 공통으로 따르는 절차입니다. 스킬이 `{work}/facts.json`·`{work}/graph-candidates.json`을 넘기면 1장부터 실행합니다. `{tmp}`는 위키 clone, `{work}`는 추출 산출물 폴더, `{doc_contract_path}`는 규약(`${CLAUDE_PLUGIN_ROOT}/references/doc-contract.md`)의 절대 경로입니다. git 명령은 모두 `GIT_TERMINAL_PROMPT=0`을 붙여 실행합니다. 서브에이전트는 한 메시지에 최대 15개씩 병렬 실행하고 남으면 앞 에이전트가 끝나는 대로 다음 메시지로 띄우며, 어느 서브에이전트도 커밋하지 않습니다. 서브에이전트의 출력 파일이 정해진 경로에 없으면 다음 장 전에 그 에이전트를 다시 실행합니다.

## 0. 입력 형식

- **facts.json**: `{"facts": [{"id", "fact", "topic", "code", "set", "set_total", "quote", "slug", "scope", "deleted", "source", "check", "input"}], "rejected": [{"id", "fact", "source", "reason"}]}` — 행 순서가 문서별 사실 순서이며, 스킬이 정리 단계에서 뺀 사실(update의 대체 등)은 `rejected`에 둠
  - **id**: update `F1`~, add `A1`~
  - **slug**: 사실이 다루는 등록 레포, 없으면 빈 문자열
  - **scope·deleted**: update만 — 위치 `root`(도메인 루트)·`repo`(레포 폴더), diff가 지운 대상을 말하는 사실이면 true이고 add는 빈 문자열·false
  - **source**: 규약 8장 근거 줄 목록
  - **check**: 코드 확인 대상 `[{"repo_path", "rev"}]` — update는 근거 레포마다 그 레포의 가장 늦은 근거 머지 sha, add는 `origin/{defaultBranch}`(등록 레포 파일 근거면 그 sha), 확인할 레포가 없으면 빈 배열
  - **input**: 자료 원문 파일 경로 목록 — update는 빈 배열
  - **quote**: 규약 7장 다른 값의 변경 근거 — update는 근거 머지 목록, add는 `사용자 확인 YYYY-MM-DD 새 값 선택`, 없으면 빈 문자열
- **graph-candidates.json**: `{"candidates": [{"id": "G1~", "slug", "key": "responsibilities|hosts|deps", "op": "add|remove|replace", "value", "old", "code", "source", "check"}]}` — `value`·`old`는 책임 문장, `{"env", "host"}`, `{"to", "desc"}` 중 하나이고 `old`는 교체·삭제일 때만
- **레포 읽기**: `check`와 간선 후보 `to`가 가리키는 레포 중 스킬이 준비하지 않은 레포마다 `{workspace.root}/{slug}`가 없으면 `git clone {remote} {workspace.root}/{slug}`, 있으면 `git -C {workspace.root}/{slug} fetch origin {defaultBranch}` — 작업 트리는 건드리지 않고 `rev`만 `git grep`·`git show`로 읽으며, 실패한 레포는 코드 확인 없이 진행하고 보고에 남김

## 1. 배정

메인이 `facts`를 문서에 배정합니다.

- **위치**: `scope`가 있으면 그 위치, 없으면 규약 2장
- **대조**: 규약 7장 대조 — 목록은 `{tmp}/knowledge/{domain}/*.md`와 `{tmp}/knowledge/{domain}/{slug}/*.md`의 frontmatter `description`, 본문은 `grep -ril '{핵심 식별자}' {tmp}/knowledge/{domain}`
- **신규 문서**: 대상 문서가 없는 사실은 같은 위치끼리 주제로 묶어 규약 3장 한 주제가 서면 신규 문서 1장(규약 2장 파일명), 서지 않으면 `기각 — 한 주제 아님`

`{work}/assign.json`에 쓰며, `rejected`에는 `facts.json`의 `rejected`를 먼저 옮깁니다.

```
{"docs": [{"doc": "knowledge/{domain} 기준 상대 경로", "created": true, "facts": [facts.json 사실 행 그대로]}],
 "rejected": [{"id", "fact", "source", "reason"}]}
```

## 2. 반영

`docs`의 문서마다 Agent 1회를 `model: sonnet`으로 실행합니다.

```
위키 문서 한 장에 사실 여러 건을 반영하라.
입력: {work}/assign.json `docs`에서 `doc`이 "{doc}"인 항목 — 문서 {tmp}/knowledge/{domain}/{doc}, 신규 여부, 사실 행.
기준: `sed -n '/^## 2\./,/^## 8\./p' {doc_contract_path}` — 2~7장, 신규 문서는 2~4장대로 만든다.
판정: 사실을 주어진 순서대로 7장으로 판정한다 — 동일·추가·교체는 본문에 반영하고, deleted 사실은 같은 대상의 문장을 지워 삭제로 적으며(대상 문장이 없으면 동일), 건너뜀(7장 다른 값의 근거 없음)은 본문을 고치지 않는다.
코드값: set이 있는 사실은 4장 집합 표기대로 `## 코드값` 표에 사실이 뜻을 말한 원소만 담고, 표 위에 set_total이 0이면 `원본: \`{set}\` — 일부`, 아니면 `원본: \`{set}\` 전 {set_total}종`을 둔다. 기존 표에 원소를 더할 때는 기존 원본 줄의 `전 N종`을 `— 일부`로 낮추지 않되, 더한 원소로 N이 맞지 않으면 `— 일부`로 바꾼다.
금지: 이 문서 밖 파일 편집, 코드 저장소 조회, 사전 지식.
출력: {work}/applied/{doc_slug}.json에 Write —
{"doc": "{doc}", "created",
 "verdicts": [{"id", "verdict": "동일|추가|교체|삭제|건너뜀", "summary": "추가·교체면 `{절}`에 반영한 내용 한 구", "old": "교체·건너뜀이면 기존 값, 삭제면 지운 문장"}]}
응답은 판정별 건수만.
```

`{doc_slug}`는 `doc`의 `/`를 `__`로, `.md`를 뺀 이름입니다.

## 3. 검토

`docs`의 문서마다 Agent 1회를 메인 모델로 실행합니다. 검토가 쓰기 스킬의 유일한 품질 게이트이므로 형식 검사 스크립트로 대신하지 않습니다. `{check}`는 사실 id별 `check`, `{input}`은 사실 행 `input`의 합집합입니다.

```
방금 사실을 반영한 위키 문서 한 장을 끝까지 읽고 규약 위반을 고쳐라.
입력: 문서 {tmp}/knowledge/{domain}/{doc}, 이번 반영 사실 {id·fact 목록}, 이번 변경 `git -C {tmp} diff -- knowledge/{domain}/{doc}`(신규 문서는 파일 전체), 사실별 코드 확인 대상 {check}, 자료 원문 {input}, 다른 문서 목록 `grep -H '^description:' {tmp}/knowledge/{domain}/*.md {tmp}/knowledge/{domain}/*/*.md`.
기준: `sed -n '/^## 1\./,/^## 8\./p' {doc_contract_path}` — 1~7장을 의미(1장 판정, 5장 문장, 6장 겹침)와 형식(2장 위치·파일명, 3장 description, 4장 절 이름·순서, `## 코드값` 표마다 `원본:` 줄, `전 N종`이면 표 행 수 N) 모두 판정한다.
코드 확인: 1장 판정, 식별자, `전 N종` 원소 수는 사실마다 그 사실의 rev를 `git -C {repo_path} grep {패턴} {rev}`·`git -C {repo_path} show {rev}:{경로}`로 읽어 확인한다. `— 일부` 표는 원소를 채우지 않는다.
자료 대조: `input`이 있는 사실은 원문 파일과 대조해 원문에 없는 값·식별자를 지우고 `removed`에 `자료에 없음`으로 적는다. 원문에 있는 값이 check 시점 코드와 다르면 7장 시간 순으로 판정한다 — 그 코드를 바꾼 커밋(`git -C {repo_path} log -S'{식별자}' {rev}`)의 메시지·작업 기록이 변경 의도를 밝히면 불릿을 코드 값으로 고치고 `edited`에 `시간 순 — {sha7}`로 적는다. 의도를 찾지 못하거나 코드가 잘못 작성된 것으로 보이면 불릿을 지우고 `conflicts`에 두 값을 적는다.
범위: 이번 변경 줄, description, 이번에 손댄 코드값 표만 고친다. 예외로 `전 N종` 표의 원소가 원본 정의와 다르면 원본에 맞추고, 도메인 루트 문서에 없는 `## 적용 대상`은 문서에 이미 있는 사실의 레포·모듈로만 채운다.
위치: 2장 위치에 맞지 않는 불릿은 삭제하고 removed에 reason `위치`, fact(원 사실의 조건·식별자를 담아 단독으로 읽히는 한 문장), target(옮길 문서의 knowledge/{domain} 기준 경로, 맞는 문서가 없으면 2장 파일명으로 정한 새 경로)을 적는다.
고칠 수 없는 문서(한 주제가 서지 않음, 남길 불릿이 없음 등)는 reject를 true로 두고 사유를 적는다.
금지: 새 사실 추가, 이 문서 밖 편집.
출력: {work}/review/{doc_slug}.json에 Write —
{"doc": "{doc}", "removed": [{"bullet", "reason", "ids": ["그 불릿이 담던 사실 id"], "fact": "위치만", "target": "위치만"}],
 "fixed_sets": [{"set", "before": "고치기 전 원본 줄과 행 수", "after": "고친 뒤"}],
 "edited": [{"bullet": "고친 뒤 불릿 또는 절", "reason": "고친 규약 조항과 이유 한 구"}],
 "conflicts": [{"ids": ["사실 id"], "doc_value": "지운 자료 값", "code_value": "check 시점 코드 값과 근거 경로"}],
 "reject": false, "reject_reason": ""}
응답은 삭제·맞춤·수정·불일치 건수와 reject 여부만.
```

## 4. 재배정

검토가 reason `위치`로 삭제한 항목마다 `fact`는 그 항목 값으로, 나머지 키는 `ids`의 사실 행 그대로 둔 행을 `target` 문서에 배정해(없는 문서는 1장 신규 문서 규칙) `{work}/assign-re.json`에 쓰고, 그 문서에만 2·3장을 다시 실행합니다. 입력은 `{work}/assign-re.json`, 출력은 `{work}/applied/{doc_slug}.re.json`·`{work}/review/{doc_slug}.re.json`이며, 재배정한 사실은 `.re` 판정이 앞 판정보다 우선합니다. 두 번째 검토도 위치로 삭제한 사실은 `위치 재배정`으로 넘깁니다.

## 5. 원복

`reject`가 true인 문서와 검토로 본문이 빈 신규 문서는 원복하고(`git -C {tmp} checkout -- {경로}`, 신규는 삭제) 그 사실을 `검토 기각`으로 넘깁니다 — 4장에서 다른 문서로 재배정한 사실은 그 문서의 판정을 따름.

## 6. 지도 갱신

`graph-candidates.json`에 후보가 있는 `slug`마다 Agent 1회를 `model: sonnet`으로 실행합니다. 후보가 없으면 이 장을 건너뜁니다.

```
레포 {slug}의 지도 변경 후보를 코드로 확인해 적용할 변경만 남겨라.
입력: {work}/graph-candidates.json 중 slug가 "{slug}"인 행, 현재 노드 {registry 노드 JSON}, 현재 간선 {deps 블록 JSON}, 등록 레포 {domain/slug·remote·defaultBranch·hosts 목록}.
기준: `sed -n '/^## 9\./,$p' {doc_contract_path}`
코드 확인: 현재 레포는 후보 check의 rev를 `git -C {repo_path} grep|show {rev}`로, 간선 대상은 준비된 `{workspace.root}/{target}`의 `origin/{defaultBranch}`를 읽는다.
판정: 후보마다 동일·추가·삭제·교체·기각 — 9장 변경 근거·교체를 적용하고 확인하지 못하면 기각 `코드 미확인`, 대상이 등록 레포가 아니면 기각 `상대 미등록`. 현재 간선에 같은 to가 있으면 add가 아니라 그 간선 desc에 사용처를 더한 replace로 둔다.
금지: 파일 편집, 9장 편집 주체 밖 키 변경.
출력: {work}/graph/{slug}.json에 Write — {"slug", "ops": [{"id", "key", "op", "value", "old", "reason"}], "rejected": [{"id", "reason"}]}
동일 판정은 ops에도 rejected에도 적지 않는다. 응답은 판정별 건수만.
```

메인이 `ops`를 `{tmp}/registry.json`·`{tmp}/deps.json`에 Edit으로 반영합니다. 해당 노드·블록 줄만 고치고 서식을 유지하며, 간선 블록이 없으면 `deps.{domain}/{slug}` 키를 만들고 간선이 비면 키를 삭제합니다. 바꾼 slug마다 아래 검증이 `ok`일 때까지 고칩니다.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify_register_file.py {tmp} {domain}/{slug}
```

## 7. 커밋

`--dry-run`이면 커밋하지 않습니다. 그 밖에는 문서마다 규약 8장대로 커밋합니다. 근거 줄은 그 문서 사실 행의 `source`이고, 교체 판정이 있으면 `기존 {old} / 새 {값}` 줄을 둡니다.

```
git -C {tmp} add knowledge/{domain}/{doc}
git -C {tmp} commit -m "docs({domain}): {doc} {요약}" -m "{근거}"
```

지도 변경이 있으면 이어서 규약 9장 커밋 한 개를 남깁니다. 근거 줄은 적용한 `ops` 후보의 `source`이고, 교체면 `기존 {old} / 새 {값}` 줄을 둡니다.

```
git -C {tmp} add registry.json deps.json
git -C {tmp} commit -m "docs(graph): {domain} 책임 N건 · 간선 M건 · 호스트 K건" -m "{근거}"
```
