# 위키 반영 절차

update·add 스킬이 사실을 추출한 뒤 공통으로 따르는 절차입니다. 스킬이 `{work}/facts.json`·`{work}/graph-candidates.json`을 넘기면 1장부터 실행합니다. `{tmp}`는 위키 clone, `{work}`는 추출 산출물 폴더, `{doc_contract_path}`는 규약(`{PLUGIN_ROOT}/references/doc-contract.md`)의 절대 경로입니다. git 명령은 모두 `GIT_TERMINAL_PROMPT=0`을 붙여 실행합니다. 서브에이전트는 한 메시지에 최대 15개씩 병렬 실행하고 남으면 앞 에이전트가 끝나는 대로 다음 메시지로 띄우며, 어느 서브에이전트도 커밋하지 않습니다. 서브에이전트의 출력 파일이 정해진 경로에 없으면 다음 장 전에 그 에이전트를 다시 실행합니다.

## 0. 입력 형식

- **facts.json**: `{"facts": [{"id", "fact", "topic", "code", "set", "set_total", "quote", "slug", "scope", "deleted", "source", "check", "input"}], "rejected": [{"id", "fact", "source", "reason"}]}` — 행 순서가 문서별 사실 순서이며, 스킬이 정리 단계에서 뺀 사실(update의 대체 등)은 `rejected`에 둠
  - **id**: update `F1`~, add `A1`~
  - **slug**: 사실이 다루는 등록 레포, 없으면 빈 문자열
  - **scope·deleted**: 두 스킬 모두 규약 1·2장에 따라 root 또는 repo를 지정한다. deleted는 7장의 폐지 결정이나 제약 해소 근거가 있는 사실만 true다
  - **source**: 규약 8장 근거 줄 목록
  - **check**: 코드 확인 대상 `[{"repo_path", "rev"}]` — update 문서 검토는 해당 레포에서 이번 수집에 포함한 마지막 커밋 sha, 지도 후보 확인은 해당 후보의 근거 sha, add는 `origin/{defaultBranch}`(등록 레포 파일 근거면 그 sha), 확인할 레포가 없으면 빈 배열
  - **input**: 진술을 확인할 원문 파일 경로 목록(머지에서 찾은 결정이면 해당 diff나 규격 사본)
  - **quote**: 규약 7장의 결정을 뒷받침하는 문구 또는 프로젝트 지식의 근거 문구. source로 원문 위치를 찾을 수 있어야 함
- **graph-candidates.json**: `{"candidates": [{"id": "G1~", "slug", "key": "responsibilities|hosts|deps", "op": "add|remove|replace", "value", "old", "code", "source", "check"}]}` — `value`·`old`는 책임 문장, `{"env", "host"}`, `{"to", "desc"}` 중 하나이고 `old`는 교체·삭제일 때만
- **레포 읽기**: `check`와 간선 후보 `to`가 가리키는 레포 중 스킬이 준비하지 않은 레포마다 `{workspace.root}/{slug}`가 없으면 `git clone {remote} {workspace.root}/{slug}`, 있으면 `git -C {workspace.root}/{slug} fetch origin {defaultBranch}` — 작업 트리는 건드리지 않고 `rev`만 `git grep`·`git show`로 읽으며, 실패한 레포는 코드 확인 없이 진행하고 보고에 남김

## 1. 배정

메인이 `facts`를 문서에 배정합니다.

- **위치**: 규약 1·2장에 따라 scope와 근거를 대조한다. root는 대상과 보장할 동작이 명시된 결정·규격, repo는 등록 레포의 반복 가능한 코드 밖 지식만 배정한다. 둘 다 충족하지 않으면 배정 전에 기각한다.
- **대조**: 규약 7장 대조 — 목록은 `{tmp}/knowledge/{domain}/*.md`와 `{tmp}/knowledge/{domain}/{slug}/*.md`의 frontmatter `description`, 본문은 `grep -ril '{핵심 식별자}' {tmp}/knowledge/{domain}`
- **신규 문서**: 대상 문서가 없는 사실은 같은 위치끼리 주제로 묶어 규약 3장 한 주제가 서면 신규 문서 1장(규약 2장 파일명), 서지 않으면 `기각 — 한 주제 아님`

`{work}/assign.json`에 쓰며, `rejected`에는 `facts.json`의 `rejected`를 먼저 옮깁니다.

```
{"docs": [{"doc": "knowledge/{domain} 기준 상대 경로", "created": true, "facts": [facts.json 사실 행 그대로]}],
 "rejected": [{"id", "fact", "source", "reason"}]}
```

## 2. 반영

`docs`의 문서마다 서브에이전트 1회를 실행 환경 연결에 따라 실행합니다.

```
위키 문서 한 장에 사실 여러 건을 반영하라.
입력: {work}/assign.json `docs`에서 `doc`이 "{doc}"인 항목 — 문서 {tmp}/knowledge/{domain}/{doc}, 신규 여부, 사실 행.
기준: `sed -n '/^## 2\./,/^## 8\./p' {doc_contract_path}` — 2~7장, 신규 문서는 2~4장대로 만든다.
판정: 규약 7장에 따라 기존 문장의 적용 대상·조건·근거와 사실의 quote·source를 대조한다. 동일하면 유지하고 추가·교체·삭제는 해당 근거가 뒷받침하는 범위만 편집한다. 기존 값과 다르면 규약 7장의 대체 근거를 확인하고, 같은 조건에서 함께 참일 수 없는 기존 문장만 함께 고친다. deleted는 같은 대상의 폐지·해소가 확인될 때만 적용한다. 근거가 부족하면 기존 문장을 보존하고 건너뜀으로 적는다. 정책 출처는 4장대로 문장이나 표 곁에 붙인다.
코드값: set이 있는 사실은 4장 집합 표기대로 `## 코드값` 표에 사실이 뜻을 말한 원소만 담고, 표 위에 set_total이 0이면 `원본: \`{set}\` — 일부`, 아니면 `원본: \`{set}\` 전 {set_total}종`을 둔다. 기존 표에 원소를 더할 때는 기존 원본 줄의 `전 N종`을 `— 일부`로 낮추지 않되, 더한 원소로 N이 맞지 않으면 `— 일부`로 바꾼다.
금지: 이 문서 밖 파일 편집, 코드 저장소 조회, 사전 지식.
출력: {work}/applied/{doc_slug}.json에 Write —
{"doc": "{doc}", "created",
 "verdicts": [{"id", "verdict": "동일|추가|교체|삭제|건너뜀", "summary": "추가·교체면 `{절}`에 반영한 내용 한 구", "old": "교체·건너뜀이면 기존 값, 삭제면 지운 문장"}]}
응답은 판정별 건수만.
```

`{doc_slug}`는 `doc`의 `/`를 `__`로, `.md`를 뺀 이름입니다.

## 3. 검토

`docs`의 문서마다 서브에이전트 1회를 실행 환경 연결에 따라 메인 모델로 실행합니다. 검토가 쓰기 스킬의 유일한 품질 게이트이므로 형식 검사 스크립트로 대신하지 않습니다.

```
방금 사실을 반영한 위키 문서 한 장을 끝까지 읽고 규약 위반을 고쳐라.
입력: {work}/assign.json `docs`에서 `doc`이 "{doc}"인 항목의 사실 행(id·fact, 코드 확인 대상 check, 자료 원문 input), 문서 {tmp}/knowledge/{domain}/{doc}, 이번 변경 `git -C {tmp} diff -- knowledge/{domain}/{doc}`(신규 문서는 파일 전체), 다른 문서 목록 `grep -H '^description:' {tmp}/knowledge/{domain}/*.md {tmp}/knowledge/{domain}/*/*.md`.
기준: `sed -n '/^## 1\./,/^## 8\./p' {doc_contract_path}` — 1~7장을 의미(1장 판정, 5장 문장, 6장 겹침)와 형식(2장 위치·파일명, 3장 description, 4장 절 이름·순서, `## 코드값` 표마다 `원본:` 줄, `전 N종`이면 표 행 수 N) 모두 판정한다.
원문 대조: 각 사실의 input·quote·source를 읽고 정책의 적용 대상, 필수 동작, 규격 판본 또는 결정이 실제로 명시됐는지 확인한다. 프로젝트 지식은 해당 레포에 반복해서 적용되는 코드 밖 제약인지 확인한다. 근거가 없거나 결정끼리 충돌하면 그 사실이 만든 편집만 원복하고 이유와 두 근거를 conflicts에 적는다. 교체·삭제 전의 유효한 문장과 같은 문서의 다른 유효한 변경을 보존한다.
코드 대조: 필요한 식별자와 현재 동작은 check의 rev에서 git grep·show로 확인한다. 코드가 확정된 결정과 달라도 정책 문장과 코드값 표는 결정 원문을 따른다. 같은 경계에서 확인한 차이는 differences에 두 값과 근거를 적어 실행 결과로 돌려준다. 코드 일치를 정책 반영 조건으로 삼지 않는다. 차이를 위키의 적용 상태로 적지 않는다.
범위: 이번 변경 줄, description, 손댄 표만 검토한다. 전 N종 표는 해당 사실의 원문이 보장한 집합과 대조한다. 도메인 루트의 적용 대상은 결정 근거로 확인된 범위만 적는다.
위치: 기록 요건을 충족하고 목적지만 잘못된 이번 변경은 기존 문장을 보존한 채 되돌리고 removed에 reason `위치`, fact(원 사실의 조건·식별자를 담아 단독으로 읽히는 한 문장), target(옮길 문서의 knowledge/{domain} 기준 경로, 맞는 문서가 없으면 2장 파일명으로 정한 새 경로)을 적는다.
겹침: 6장 한 곳 소유와 위치 판정에서 다른 문서가 같은 사실을 가졌는지는 이번 실행 전 내용(`git -C {tmp} show HEAD:knowledge/{domain}/{경로}`)으로만 판단한다 — 다른 문서의 이번 실행 변경은 병렬로 도는 다른 검토가 지우고 있을 수 있다. 프로젝트 문서에 정책 사본이 있어도 공통 문서를 소유 문서로 삼고, 사본 정리는 5장에서 한다.
기존 문서의 마지막 사실을 삭제했으면 원래 문장과 폐지 결정 또는 제약 해소 근거를 대조한다. 근거가 확인되고 유효한 사실이 하나도 남지 않았으면 문서 파일을 삭제하고 reject=false로 둔다. 다른 사실이 남으면 해당 사실과 출처를 보존한다. 근거 부족으로 비게 된 문서나 주제가 성립하지 않는 신규 문서는 reject=true로 두고 이유를 적는다.
금지: 새 사실 추가, 이 문서 밖 편집.
출력: {work}/review/{doc_slug}.json에 Write —
{"doc": "{doc}", "removed": [{"bullet", "reason", "ids": ["그 불릿이 담던 사실 id"], "fact": "위치만", "target": "위치만"}],
 "fixed_sets": [{"set", "before": "고치기 전 원본 줄과 행 수", "after": "고친 뒤"}],
 "edited": [{"bullet": "고친 뒤 불릿 또는 절", "reason": "고친 규약 조항과 이유 한 구"}],
 "differences": [{"id", "policy": "보장할 값과 출처", "observed": "코드 값과 근거 rev·경로"}],
 "conflicts": [{"ids": ["사실 id"], "old": "기존 문장과 출처", "proposed": "새 값과 출처", "reason": "미해결 이유"}],
 "reject": false, "reject_reason": ""}
응답은 삭제·맞춤·수정·불일치 건수와 reject 여부만.
```

## 4. 재배정

검토가 reason `위치`로 삭제한 항목마다 `fact`는 그 항목 값으로, 나머지 키는 `ids`의 사실 행 그대로 둔 행을 `target` 문서에 배정해(없는 문서는 1장 신규 문서 규칙) `{work}/assign-re.json`에 쓰고, 그 문서에만 2·3장을 다시 실행합니다. 입력은 `{work}/assign-re.json`, 출력은 `{work}/applied/{doc_slug}.re.json`·`{work}/review/{doc_slug}.re.json`입니다. 이 검토는 위치를 판정하지 않습니다 — 검토 지시에서 `위치:` 줄을 빼고 `기준:` 줄의 `2장 위치·파일명`을 `2장 파일명`으로 바꿔 실행하며, 사실은 첫 검토가 지정한 문서에 남습니다. 재배정에도 원문 대조와 정책·프로젝트 지식의 기록 요건을 그대로 적용합니다.

## 5. 원복

`reject`가 true인 문서와 검토로 본문이 빈 신규 문서는 원복하고(`git -C {tmp} checkout -- {경로}`, 신규는 삭제) 그 사실을 `검토 기각`으로 넘깁니다 — 4장에서 다른 문서로 재배정한 사실은 그 문서의 판정을 따름.

메인은 검토·원복 후, 이번에 확정한 공통 정책과 같은 대상·조건을 다루는 프로젝트 문서를 기존 값·식별자·링크로 찾는다. 중복된 정책 문장은 검토를 통과한 공통 문서의 상대 링크로 바꾼다. 폐지가 확인된 정책은 사본과 폐지된 참조를 제거한다. 다른 적용 대상의 정책과 프로젝트 고유 제약은 보존한다. 마지막 사실의 폐지·해소로 삭제한 파일은 복구하지 않는다. 함께 고친 문서도 해당 결정의 출처로 7장의 커밋과 PR 내역에 포함한다.

## 6. 지도 갱신

`graph-candidates.json`에 후보가 있는 `slug`마다 서브에이전트 1회를 실행 환경 연결에 따라 실행합니다. 후보가 없으면 이 장을 건너뜁니다.

```
레포 {slug}의 지도 변경 후보를 코드로 확인해 적용할 변경만 남겨라.
입력: {work}/graph-candidates.json 중 slug가 "{slug}"인 행, 현재 지도 {tmp}/registry.json의 `domains.{domain}.repos`(현재 노드는 `{slug}`, 키 목록이 등록 레포와 그 remote·defaultBranch·hosts)와 {tmp}/deps.json의 `deps."{domain}/{slug}"` 블록(현재 간선).
기준: `sed -n '/^## 9\./,$p' {doc_contract_path}`
코드 확인: 현재 레포는 후보 check의 rev를 `git -C {repo_path} grep|show {rev}`로, 간선 대상은 준비된 `{workspace.root}/{target}`의 `origin/{defaultBranch}`를 읽는다.
판정: 후보마다 동일·추가·삭제·교체·기각 — 9장 변경 근거·교체를 적용하고 확인하지 못하면 기각 `코드 미확인`, 대상이 등록 레포가 아니면 기각 `상대 미등록`. 현재 간선에 같은 to가 있으면 add가 아니라 그 간선 desc에 사용처를 더한 replace로 둔다.
금지: 파일 편집, 9장 편집 주체 밖 키 변경.
출력: {work}/graph/{slug}.json에 Write — {"slug", "ops": [{"id", "key", "op", "value", "old", "reason"}], "rejected": [{"id", "reason"}]}
동일 판정은 ops에도 rejected에도 적지 않는다. 응답은 판정별 건수만.
```

메인이 `ops`를 `{tmp}/registry.json`·`{tmp}/deps.json`에 Edit으로 반영합니다. 해당 노드·블록 줄만 고치고 서식을 유지하며, 간선 블록이 없으면 `deps.{domain}/{slug}` 키를 만들고 간선이 비면 키를 삭제합니다. 바꾼 slug마다 아래 검증이 `ok`일 때까지 고칩니다.

```
python3 {PLUGIN_ROOT}/scripts/verify_register_file.py {tmp} {domain}/{slug}
```

## 7. 커밋

`--dry-run`이면 커밋하지 않습니다. 그 밖에는 실제 diff가 남은 문서만 규약 8장대로 커밋합니다. 동일·건너뜀·원복으로 편집이 없으면 다음 문서로 넘어갑니다. 근거 줄은 그 문서 사실 행의 `source`이고, 교체 판정이 있으면 `기존 {old} / 새 {값}` 줄을 둡니다.

```
git -C {tmp} add knowledge/{domain}/{doc}
git -C {tmp} commit -m "docs({domain}): {doc} {요약}" -m "{근거}"
```

지도 변경이 있으면 이어서 규약 9장 커밋 한 개를 남깁니다. 근거 줄은 적용한 `ops` 후보의 `source`이고, 교체면 `기존 {old} / 새 {값}` 줄을 둡니다.

```
git -C {tmp} add registry.json deps.json
git -C {tmp} commit -m "docs(graph): {domain} 책임 N건 · 간선 M건 · 호스트 K건" -m "{근거}"
```
