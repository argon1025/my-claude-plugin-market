# agent-wiki update 범위 안 변경 전사 정확도 보강과 PR 본문 간결화 0.7.0

## 의도

- **왜**: onestore-cmsapp 첫 `update --dry-run`(커서 `0a4560e`, 머지 40건)에서 update가 범위 안 변경을 정확히 전사하지 못함 — 검토의 코드 확인 rev 오류, 위치 재배정 입력이 문장 조각, 간선 중복 추가, 큰 diff 미독, diff가 지운 대상의 삭제 경로 없음이 드러났고 프롬프트·절차와 PR 본문이 장황함
- **누가**: 위키 운영자가 `/agent-wiki:update`를 실행하고 위키 PR을 리뷰하며, 머지 뒤 `/agent-wiki:add`가 그 PR의 제외 행을 처리함
- **완료**: 아래 확정 결정 13건과 간결한 PR 템플릿(레포·사실 목록·제외된 사실 목록·문서별 적용 내역·레포 지도)이 agent-wiki 0.7.0으로 개인판에 반영되고 사내판에 미러링되며, onestore-cmsapp 드라이런이 검증 기준을 통과한 상태

## 배경

- **관찰 기록**: `/Users/a1000377/Desktop/Projects/onestorecorp/onestore-devcenter-claude-plugin-marketplace/agent-wiki-update-improvements.md` — 이번 개선의 원천이며 15개 항목 번호(1~15)를 아래에서 그대로 씀
- **front 브랜치**: onestore-cmsapp-front는 기능 PR이 `develop`에 머지되고 `master` first-parent는 `Release/…`·`Hotfix/…` 묶음뿐이라 커서(`77bad80`, develop first-parent 위)와 어긋났음 — 사용자가 registry `defaultBranch`를 `develop`으로 전환 완료함
- **병합 사실의 check**: update `SKILL.md` 4장은 `check`를 `[{"repo_path": repos[slug].path, "rev": 가장 늦은 근거 머지 sha}]` 한 항목으로만 정의하지만, 레포를 넘는 병합 사실(이번 실행 208건 중 11건)은 레포별 check를 가짐 — `apply.md` 3장이 문서 단위로 `repo_path`별 rev 하나("뒤 사실 행의 rev")로 모아 오래된 rev를 넘김
- **diff 머리말**: `collect_update_merges.py`의 diff 파일 머리말에는 머지 커밋 제목(Bitbucket `Pull request #N: {PR 제목}`)과 딸린 커밋 메시지 최대 20건이 들어 있고, PR 본문은 수집하지 않음
- **삭제 경로 부재**: 추출은 규약 1장 변경 서사 금지로 "제거됨" 사실을 내지 않고, 반영 판정은 `동일|추가|교체|건너뜀`뿐이라 diff가 지운 코드·값을 말하는 위키 문장이 남음
- **간선 검증**: `verify_register_file.py`는 같은 `to` 간선 두 개를 `unregistered, self or duplicate`로 실패시키고, 미등록 대상 간선은 `apply.md` 6장이 항상 `상대 미등록`으로 기각함
- **Read 상한**: 추출 에이전트는 Read 1회(기본 2000줄·토큰 상한)에서 멈춰 큰 묶음 diff를 끝까지 읽지 않았음(agent `dbdfb45` 711행 이후)
- **세션 목록 따옴표**: `generate_document_list.py`는 `description:` 뒤 문자열을 그대로 실어, YAML상 따옴표가 필요한 description(`"@Async …"`)은 세션 목록에 따옴표가 노출됨
- **템플릿 공유**: `templates/wiki-pr.md`는 update·add가 함께 쓰고, add는 `skills/add/SKILL.md` 2·3·4장, `references/publish.md` 3장, `README.md` 스킬 표에서 update PR의 `건너뜀`·`위치 재배정` 행을 이름으로 참조함
- **버전 관례**: 개인판은 플러그인 버전을 올릴 때 `.claude-plugin/marketplace.json` `metadata.version`도 함께 올림(현재 4.0.1), 사내판은 `plugin.json`과 `marketplace.json`의 agent-wiki 항목 `version`(현재 0.6.1)·`metadata.version`(현재 4.1.1)을 올림 — 이전 미러링 커밋 `612bc1b` 방식

## 확정 결정 (사용자 확인 2026-10-02)

- **update 범위**: 커서부터 `origin/{defaultBranch}` first-parent 중 예산 안 머지의 변경 줄·커밋 메시지·작업 기록이 직접 말하는 사실을 머지 순서대로 전사함 — 사실은 근거 머지 시점 코드로만 확인하고 현재 기본 브랜치와의 정합, 닫힌 집합 완결, 문서 조각화·병합, 기존 줄 규약 위반은 audit 몫
- **채택 기준**: 단순한 구조와 간결한 프롬프트가 최우선
- **다른 값(A)**: 위키에 없으면 추가, diff가 지운 대상을 말하는 문장은 근거 없이 삭제, 값이 다른 수정은 PR 제목·딸린 커밋 메시지·diff 속 plan·feedback에서 의도를 확인할 때만 교체하고 없으면 건너뜀 — PR 본문은 수집하지 않음
- **간선 대상(B)**: 현행 유지 — 대상 레포 `origin/{defaultBranch}`에서 실재 확인
- **재배정(C)**: `apply.md` 4장 루프 유지, 검토 `removed`에 위치 사유일 때 `fact`·`target`을 두고 4장이 그 값으로 배정하며 재배정에도 1장 신규 문서 규칙 적용
- **추출 경로(E)**: 메인 직접 처리 분기 삭제, 모든 묶음을 sonnet 서브에이전트로 추출
- **수용 항목**: 1(사실별 check rev), 2(first-parent 밖 커서 `skipped` 가드), 3·4(C), 5(같은 `to`면 `replace`), 7(변경 줄이 직접 말하는 사실만), 8(`scope` 필드, `scope_reason` 없음), 10(`BATCH_BYTES` 200KB, offset으로 끝까지 Read), 12(한 메시지 최대 15개), 13(기본 `--max-merges` 20), 14(간선 `to`는 등록 레포만), A, E
- **기각 항목**: 6(집합 이름 충돌, audit), 9(신규 문서 최소 기준, audit), 11(정리·배정 스크립트), B 변경안, 7의 질문형 문구, 8의 `scope_reason`, 10의 릴리스 펼침·diff 분할·`읽은 범위` 필드, 12의 다문서 묶음, 13의 단계별 드라이런·검토 모델 변경, 15의 파일 변경 알림·150자 상한
- **PR 본문**: 절은 `## 레포`, `## 사실 목록`, `## 제외된 사실 목록`, `## 문서별 적용 내역`, `## 레포 지도`만 두고 `## 요약`·`## 검토 방법`은 삭제
- **제외 목록 범위**: 머지 후 add가 처리할 행(건너뜀·위치 재배정·미해결 충돌)을 모두 담고, add는 그 절의 행을 고르지 않고 전부 처리함 — 사용자 문장 "이것때문에 add 처리 대상을 판단해야한다면 제외, 아니라면 함께 넣어도됨"
- **미러링**: 사내판 `plugins/agent-wiki` 미러링을 마지막 커밋으로 포함, 사내 고유 3파일(`config.json`·`references/publish.md`·`README.md`)은 유지하되 그 안의 `건너뜀·위치 재배정` 참조 문구만 맞춤

## 선행 읽기

- `agent-wiki/references/doc-contract.md` — 모든 프롬프트가 장 번호로 인용하는 판정 기준, 7장을 고침
- `agent-wiki/references/apply.md` — update·add 공용 절차, 장 번호가 `SKILL.md`·`wiki-pr.md`에서 인용됨

## 작업

| 파일 | 변경 | 사다리 |
|---|---|---|
| `agent-wiki/scripts/collect_update_merges.py` | `BATCH_BYTES` 200KB, `--max-merges` 기본 20, first-parent 밖 커서 `skipped` | 기존 파일 수정 |
| `agent-wiki/scripts/generate_document_list.py` | description 양끝 따옴표 제거 | ⑥ 한 줄 |
| `agent-wiki/references/doc-contract.md` | 7장 `**제거**` 불릿 추가 | 기존 파일 수정 |
| `agent-wiki/references/apply.md` | 서두 병렬 상한, 0장 `scope`·`deleted`·check, 1장 위치, 2장 삭제 판정, 3장 사실별 check·`removed.fact/target`, 4장 target 배정, 6장 같은 `to` | 기존 파일 수정 |
| `agent-wiki/skills/update/SKILL.md` | 인자 기본값, 3장 추출 프롬프트, 4장 check·필드 전달 | 기존 파일 수정 |
| `agent-wiki/templates/wiki-pr.md` | 5개 절 구조로 재작성 | 기존 파일 수정 |
| `agent-wiki/skills/add/SKILL.md`, `agent-wiki/references/publish.md`, `agent-wiki/README.md` | `건너뜀`·`위치 재배정` 행 참조를 `제외된 사실 목록` 행으로 | 기존 파일 수정 |
| `agent-wiki/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | agent-wiki 0.7.0, `metadata.version` 4.1.0 | 기존 파일 수정 |
| 사내판 `plugins/agent-wiki/**`, `.claude-plugin/marketplace.json` | 개인판 변경 미러링, agent-wiki 0.7.0, `metadata.version` 4.2.0 | 기존 파일 수정 |

### agent-wiki/scripts/collect_update_merges.py

- **상수**: `BATCH_BYTES = 500_000` → `200_000`, `--max-merges` `default=40` → `20`
- **first-parent 가드**: `first_parent()`가 `parents` 문자열의 첫 sha를 행의 `_parent`로 함께 담고, `main()`에서 `rows = first_parent(...)` 직후 `rows and rows[0]["_parent"] != cursor`이면 `work["skipped"][slug] = f"커서 {cursor[:7]}가 origin/{branch} first-parent 밖 — registry defaultBranch 확인"` 후 `continue` — 커서가 first-parent 위에 있으면 범위 첫 행의 첫 부모가 커서이고, 행이 없으면 커서가 head임
- **출력 필터**: `entry["commits"]`의 키 제외를 `k != "_key"` → `not k.startswith("_")`로 바꿔 `_parent`가 `work.json`에 실리지 않게 함
- **머리말**: 머리 주석 3줄은 유지

### agent-wiki/scripts/generate_document_list.py

- `return line[len("description:"):].strip()` → `.strip().strip('"\'')`

### agent-wiki/references/doc-contract.md

- **7장**: `**현재 값만**` 불릿 뒤에 `- **제거**: diff가 지운 코드·값·동작을 말하는 문장은 다른 값 근거 없이 지움 — 대상이 코드에서 사라져 남은 문장이 거짓이 됨` 추가

### agent-wiki/references/apply.md

- **서두**: 마지막 문장 뒤에 `"한 메시지에 병렬 실행"은 한 메시지에 최대 15개이며, 남으면 앞 에이전트가 끝나는 대로 다음 메시지로 띄웁니다.` 추가
- **0장 facts.json**: 키 목록에 `scope`·`deleted` 추가, 하위 불릿 추가 — `**scope**: 사실의 위치 `root`(도메인 루트)·`repo`(레포 폴더), update만 채우고 add는 빈 문자열` · `**deleted**: diff가 지운 대상을 말하는 사실이면 true — update만`
- **0장 check**: `update는 머지 sha` → `update는 근거 레포마다 그 레포의 가장 늦은 근거 머지 sha`
- **1장 위치**: `규약 2장으로 도메인 루트·레포 폴더를 정함` → `사실 행 `scope`가 있으면 그 위치, 없으면 규약 2장으로 정함`
- **2장 판정 문장**: `동일·추가·교체는 본문에 반영하고, 건너뜀(7장 다른 값의 근거 없음)은 본문을 고치지 않는다.` → `동일·추가·교체는 본문에 반영하고, deleted 사실은 같은 대상의 문장을 지워 삭제로 적으며(대상 문장이 없으면 동일), 건너뜀(7장 다른 값의 근거 없음)은 본문을 고치지 않는다.`
- **2장 출력**: `"verdict": "동일|추가|교체|삭제|건너뜀"`, `"old": "교체·건너뜀이면 기존 값, 삭제면 지운 문장"`
- **3장 서두**: `` `{check}`는 그 문서 사실 행의 `check`를 `repo_path`별로 모은 것이며 같은 `repo_path`가 여럿이면 뒤 사실 행의 `rev`를 쓰고, `` → `` `{check}`는 사실 id별 `check` 목록이고, ``
- **3장 프롬프트 입력**: `코드 확인 대상 {check}` → `사실별 코드 확인 대상 {check}`, 코드 확인 줄의 `check 시점 레포를 읽는다` → `사실마다 그 사실의 rev로 읽는다`
- **3장 위치 줄**: `위치: 2장 위치에 맞지 않는 불릿은 삭제하고 reason을 `위치 — {올바른 위치}`로 적는다.` 뒤에 `그 removed 항목에 fact(원 사실의 조건·식별자를 담아 단독으로 읽히는 한 문장)와 target(knowledge/{domain} 기준 문서 경로, 맞는 문서가 없으면 2장 파일명으로 제안한 새 경로)을 둔다.` 추가
- **3장 출력**: `"removed": [{"bullet", "reason", "ids": [...], "fact": "위치 사유일 때만", "target": "위치 사유일 때만"}]`
- **4장**: `삭제한 불릿 문장을 `fact`로, 나머지 키는 `ids`의 사실 행 그대로 둔 행으로 만들어 그 위치로 1장 배정을 한 번 더 하고` → `` `removed`의 `fact`를 `fact`로, 나머지 키는 `ids`의 사실 행 그대로 둔 행으로 만들어 `target` 문서에 배정하고(없는 문서는 1장 신규 문서 규칙으로 만듦) `` — 뒤 문장(2·3장 재실행, `.re` 파일, `위치 재배정`)은 유지
- **6장 판정 줄**: 끝에 `현재 간선에 같은 to가 있으면 add가 아니라 그 간선 desc에 사용처를 더한 replace로 둔다.` 추가

### agent-wiki/skills/update/SKILL.md

- **인자**: `기본 40` → `기본 20`
- **3장 서두**: `레포별 `batches`마다 Agent 1회를 `model: sonnet`으로 한 메시지에 병렬 실행합니다. 묶음이 1개이고 머지 3건 이하면 메인이 같은 기준으로 직접 처리하고, 출력 파일이 없는 묶음은` → `레포별 `batches`마다 Agent 1회를 `model: sonnet`으로 한 메시지에 최대 15개씩 병렬 실행하고, 출력 파일이 없는 묶음은`
- **3장 프롬프트 입력 줄**: 끝에 ` 파일이 길면 offset으로 나눠 끝까지 Read한다.` 추가
- **3장 프롬프트 대상 줄 신설**(입력 줄 뒤): `대상: diff의 변경 줄, 커밋 메시지(PR 제목 포함), 작업 기록이 직접 말하는 사실만 — 바뀌지 않은 문맥에서 추론한 사실(부재 주장 등)은 담지 않는다.`
- **3장 기준 줄**: `sed -n '/^## 1\./,/^## 2\./p'` → `sed -n '/^## 1\./,/^## 3\./p'`, 설명 `— 후보 문장마다 1장을 적용하고 2장으로 위치를 정한다.`
- **3장 graph 줄**: `간선 to는 등록 레포의 `{domain}/{slug}`로 쓰고, 등록되지 않은 레포는 이름 그대로 둔다.` → `간선 to는 등록 레포의 `{domain}/{slug}`만 쓰고, 등록되지 않은 대상은 후보로 내지 않는다.`
- **3장 프롬프트 신설 줄**(set 줄 앞): `scope: 2장 위치로 root(도메인 루트) 또는 repo(레포 폴더) — 한 사실이 두 성격이면 2장 분리대로 둘로 나눈다.` · `deleted: diff가 기존 동작·값·코드값을 지우면 true로 두고 fact는 지워진 대상을 지우기 전 상태 한 문장으로 쓴다.`
- **3장 출력 형식**: 사실 행에 `"scope": "root|repo"`, `"deleted": false` 추가, `quote` 설명을 `기존 동작을 바꾸는 사실이면 그 의도를 밝힌 PR 제목·커밋 메시지·plan·feedback 원문, 없으면 빈 문자열`로
- **4장 facts.json 문장**: `` `check`는 `[{"repo_path": repos[slug].path, "rev": 가장 늦은 근거 머지 sha}]` `` → `` `check`는 `source`의 레포마다 `{"repo_path": repos[레포].path, "rev": 그 레포의 가장 늦은 근거 머지 sha}`, `scope`·`deleted`는 추출 값 그대로 `` — 병합할 때 `deleted`가 다른 두 사실은 병합하지 않음

### agent-wiki/templates/wiki-pr.md

`## 채우는 법`과 `## 본문`을 아래 구조로 다시 씀. 장 번호는 `references/apply.md` 기준이고 재배정한 사실(4장)은 `.re` 판정을 쓴다는 문장, 행이 없는 절은 생략한다는 문장, add `기존 유지` 사실은 PR에 싣지 않는다는 문장은 유지함.

- **`## 레포`**: update만 — 현행 규칙 그대로(`| 레포 | 처리 머지 | 커서 | 비고 |`)
- **`## 사실 목록`**: `| # | 사실 | 문서 | 판정 | 출처 |` — `id` 순 전부, 문서 칸은 반영·삭제·제외 대상 문서(`knowledge/{domain}` 기준, 없으면 —), 판정 칸은 `{판정}` 또는 `{판정} · {사유}`
- **`## 제외된 사실 목록`**: `| # | 구분 | 문서 | 기존 값 | 새 값 | 출처 |` — 머지 후 `/agent-wiki:add {PR 링크}`가 행 전부를 처리함
  - 건너뜀: 문서 = 대상 문서, 기존 값 = 2장 `old`, 새 값 = 사실
  - 위치 재배정: 문서 = 3장 `removed.target`, 기존 값 = —, 새 값 = `removed.fact`
  - 미해결 충돌: 문서 = 대상 문서, 기존 값 = 3장 `code_value`, 새 값 = `doc_value`
- **`## 문서별 적용 내역`**: 편집 문서마다 `### {doc} · 신규|수정` 아래 `**추가|교체|삭제**: {summary} (번호)`, `**원본 맞춤**: `{set}` {before} → {after}`, `**검토 수정**: {bullet} — {reason}`, `**검토 삭제**: {bullet} — {reason} (번호)` 순, 동일·건너뜀은 적지 않음
- **`## 레포 지도`**: 현행 규칙 그대로
- **판정 표**: `| 판정 | 원천 | 사유 칸 |` — 추가·동일(2장, —), 교체(2장, 기존 `{old}` · 인용 "{quote}"), 삭제(2장, —), 건너뜀(2장, 제외 목록), 검토 삭제(3장 `removed` 중 위치 사유 제외, `{reason}`), 위치 재배정(4장 두 번째 검토도 위치로 삭제, 제외 목록), 미해결 충돌(3장 `conflicts`, 제외 목록), 대체(1장 `rejected` `대체 — {id}`, `{id}`로 대체), 기각(1장 `rejected` 그 밖, `{reason}`), 검토 기각(3장 `reject_reason`·5장 원복, `{reject_reason}`)
- **예시 본문**: 현행 예시를 새 5개 절로 옮기고 `## 요약`·`## 검토 방법` 절은 삭제, 제외 목록 예시에 건너뜀·위치 재배정 행 각 1개

### agent-wiki/skills/add/SKILL.md, references/publish.md, README.md

- **add 2장 입력 집합**: `update PR(링크 또는 붙여 넣은 본문)의 `건너뜀`·`위치 재배정` 행` → `update PR(링크 또는 붙여 넣은 본문)의 `제외된 사실 목록` 행`
- **add 3장 update PR 행**: `` `건너뜀` 행은 사실·기존 값·출처(`{slug}@{sha7}`)를 그대로 옮기고 `check`를 그 레포와 sha로, `위치 재배정` 행은 사실과 올바른 위치를 옮기며 `` → `` `제외된 사실 목록` 행 전부를 구분대로 옮김 — 건너뜀·미해결 충돌은 사실(새 값)·기존 값·출처를 옮기고 `check`를 출처 레포와 sha로, 위치 재배정은 사실과 문서를 옮기며 ``
- **add 4장 질문**: `update PR `건너뜀` 행(교체 후보와 같음)` → `PR 제외 행의 건너뜀·미해결 충돌(교체 후보와 같음)`
- **add 5장**: `위치 재배정 행은 옮긴 올바른 위치로 배정합니다` → `위치 재배정 행은 옮긴 문서로 배정합니다`
- **publish.md 3장**: `add가 update PR의 `건너뜀`·`위치 재배정` 행을 읽을 때` → `add가 update PR의 `제외된 사실 목록` 행을 읽을 때`
- **README 스킬 표 add 행**: `update PR의 건너뜀·위치 재배정 행` → `update PR의 제외된 사실 목록`

### 사내판 미러링

- **위치**: `/Users/a1000377/Desktop/Projects/onestorecorp/onestore-devcenter-claude-plugin-marketplace`, 브랜치 `feat/agent-wiki-update-improvements`를 기본 브랜치에서 만들고 커밋만 하며 push·PR은 하지 않음
- **복사**: 개인판 `agent-wiki/`에서 `config.json`·`references/publish.md`·`README.md`를 뺀 변경 파일을 `plugins/agent-wiki/`로 복사
- **사내 고유 파일**: 사내판 `references/publish.md` 3장과 `README.md` 스킬 표 add 행의 같은 문구만 위 add 참조와 동일하게 고침
- **버전**: `plugins/agent-wiki/.claude-plugin/plugin.json` 0.7.0, `.claude-plugin/marketplace.json` agent-wiki 항목 `version` 0.7.0·`metadata.version` 4.2.0
- **커밋 메시지**: `feat(agent-wiki): update 범위 안 변경 전사 정확도 보강·PR 본문 간결화 미러링, 0.7.0`, 본문 첫 줄 `개인판 my-claude-plugin-market@{개인판 마지막 커밋 sha7} agent-wiki 미러링, 사내 고유 3파일 유지`

## 커밋 분해

개인판은 `feat/agent-wiki-update-improvements` 브랜치에서 작업함. `{fx}`는 검증용 임시 폴더, `{ws}`는 `~/.agent-wiki-workspace`.

| # | 범위 | 검증 |
|---|---|---|
| 1 | `collect_update_merges.py` 상수·가드 | `python3 -m py_compile agent-wiki/scripts/collect_update_merges.py` 통과. `{fx}`에 `registry.json`(도메인 `t`, 레포 `onestore-cmsapp-front`, `remote`는 `git -C {ws}/onestore-cmsapp-front remote get-url origin`, `defaultBranch` `master`, 나머지 노드 키는 아무 값)과 `state/onestore-cmsapp-front.json`(`cursor` `77bad80924db9cb506f85a2f9ce5c2eb89610bb7`)을 두고 `python3 agent-wiki/scripts/collect_update_merges.py --wiki {fx} --workspace {ws} --domain t --out {fx}/out` 실행 시 `건너뜀  onestore-cmsapp-front: 커서 77bad80가 origin/master first-parent 밖` 출력·종료 코드 10. `defaultBranch`를 `develop`으로 바꿔 다시 실행 시 `onestore-cmsapp-front: 머지 N건`(N ≥ 1)·종료 코드 0이고 `{fx}/out/work.json`에 `_parent` 문자열 없음(`grep -c _parent` 0) |
| 2 | `generate_document_list.py` 따옴표 제거 | `{fx}`에 `registry.json`(`{"domains": {"d": {"repos": {}}}}`)과 `knowledge/d/a.md`(frontmatter `description: "@Async 작업을 고칠 때"`)를 두고 `python3 agent-wiki/scripts/generate_document_list.py {fx} d/x` 실행 시 출력에 `- a — @Async 작업을 고칠 때` 행 |
| 3 | `doc-contract.md` 7장 제거 | `grep -n '^- \*\*제거\*\*' agent-wiki/references/doc-contract.md` 1행이고 7장 범위(`sed -n '/^## 7\./,/^## 8\./p'`) 안에 있음 |
| 4 | `apply.md` | `grep -c '뒤 사실 행의' agent-wiki/references/apply.md` 0, `grep -n '최대 15개' …` 1행, `grep -n '삭제|건너뜀' …` 1행(2장 verdict), `grep -n '"target"' …` 1행(3장 출력), `grep -n '같은 to가 있으면' …` 1행(6장) |
| 5 | update `SKILL.md` | `grep -c '메인이 같은 기준으로 직접' agent-wiki/skills/update/SKILL.md` 0, `grep -c '이름 그대로 둔다' …` 0, `grep -n '"scope"' …`·`grep -n '"deleted"' …` 각 1행, `grep -n '기본 20' …` 1행, `grep -c '/^## 1\\./,/^## 3\\./p' agent-wiki/skills/update/SKILL.md` 1 |
| 6 | `wiki-pr.md`·add `SKILL.md`·`publish.md`·`README.md` | `grep -n '^## ' agent-wiki/templates/wiki-pr.md`의 본문 예시 절이 `레포`·`사실 목록`·`제외된 사실 목록`·`문서별 적용 내역`·`레포 지도` 순, `grep -rn '`건너뜀`·`위치 재배정` 행\|건너뜀·위치 재배정 행' agent-wiki` 0행 |
| 7 | 버전 | `agent-wiki/.claude-plugin/plugin.json` `"version": "0.7.0"`, `.claude-plugin/marketplace.json` `"version": "4.1.0"`, `python3 -m json.tool` 두 파일 통과 |
| 8 | 드라이런 검증(커밋 없음) | 새 세션에서 `/agent-wiki:update --domain onestore-cmsapp --dry-run` 실행 — 통과 조건: ① front가 `skipped` 아니고 처리 머지가 develop PR(`Release/`·`Hotfix/` 제목 없음) ② `graph-candidates.json`의 간선 `to`가 모두 등록 레포 ③ 6장 뒤 `verify_register_file.py` 첫 실행이 `ok` ④ `facts.json`에서 근거 레포가 둘 이상인 사실의 `check`가 레포마다 1항목 ⑤ `review/*.json`의 `위치 — ` 사유 항목이 모두 `fact`·`target`을 가짐 ⑥ `{work}/pr.md`가 새 5개 절 구조. 수치(사실 수·검토 삭제·서브에이전트 호출)는 관찰 기록 표와 함께 보고 |
| 9 | 사내판 미러링 | 사내판에서 `diff -rq plugins/agent-wiki {개인판}/agent-wiki` 결과가 `config.json`·`references/publish.md`·`README.md` 3행뿐, `grep -rn '건너뜀·위치 재배정 행\|`건너뜀`·`위치 재배정` 행' plugins/agent-wiki` 0행, `python3 -m json.tool .claude-plugin/marketplace.json` 통과 |

## 특이 사항

- **검토 방법 절 삭제**: PR 본문에서 "squash 금지(문서별 커밋 근거 유지)" 안내가 사라지므로, 위키 원격의 머지 전략 설정으로 squash를 막는 것이 후속 작업임
- **add 미적용**: `scope` 필드와 "등록 레포만 간선 후보" 규칙은 update 추출에만 두고 add 3장 추출 프롬프트는 고치지 않음 — add에서 같은 잡음이 반복되면 같은 문장을 옮김
- **삭제 오판 한계**: `deleted` 사실은 근거 없이 문장을 지우므로 추출이 이동·이름 변경을 제거로 오판하면 맞는 문장이 지워짐 — 검토가 근거 머지 시점 코드로 확인하고 PR `삭제` 행으로 리뷰어가 봄, 오판이 반복되면 삭제에도 검토의 코드 부재 확인을 필수로 둠
- **드라이런 비용**: 커밋 8은 서브에이전트 수십 회를 쓰며, 이전 실행 산출물(`/var/folders/…/tmp.xzR2WSp1IH`)은 비교 기준 수치만 관찰 기록 파일에 남아 있음
- **범위 밖**: 6·9번(집합 이름 충돌, 문서 조각화)과 집합 완결은 audit 스킬 신설 때 다룸

## Re-plan 2026-10-02 — 변경 파일 간결화 재검토

- **계기**: 사용자 지시 "에이전트는 코드나 프롬프트 수정 시 기존것은 최대한 유지하고 줄만 추가나 수정하는 경향이 있음 / 보고 꼭 필요한지 검토후 수정, 삭제할듯 / 더 간결한 구조가 가능하다면 재작성도 권장함 / 꼭 기존 구조를 유지할 필요가 없음"
- **범위**: 이번 계획이 고친 update `SKILL.md`·`apply.md`·`wiki-pr.md`와 add `SKILL.md`·`publish.md`의 해당 줄 — 확정 결정 13건은 유지하고 중복 문장만 걷음
- **update 추출 프롬프트**: `작업 기록`·`scope`·`deleted`·`set`·`set_total` 줄을 `대상`·`기준` 줄과 출력 스키마 설명으로 흡수, 2장 `work.json` 필드 나열과 PR 절 전달 문장 삭제
- **apply.md**: `assign.json` 사실 키 재나열을 "사실 행 그대로"로, 2장 신규 문서 줄을 기준 줄로 흡수, 검토 위치 사유를 `위치 — {올바른 위치}`에서 reason `위치` + `fact`·`target`으로(올바른 위치가 `target`과 중복), 4장 근거 문장 삭제, 서브에이전트 병렬 상한·커밋 금지를 서두 한 곳으로
- **드라이런 보고**: 계획 커밋 8의 ⑥이 드라이런에서 `{work}/pr.md`를 요구하나 기존 드라이런은 `apply.md` 7장 보고로 끝나 `pr.md`를 쓰지 않았음 — 7장 보고 항목(diff·판정 집계·지도)이 PR 본문과 같아 드라이런도 `pr.md`까지 쓰고 그 경로를 보고하도록 update·add 모두 바꿈
- **wiki-pr.md**: 채우는 법과 판정 표 중복을 판정 표(우선순위 순) 하나로, 제외 목록 열 규칙을 제외 표로
- **add 제외 행**: 구분별 분기 대신 모든 행을 "새 값을 사실로, 문서·기존 값·출처 그대로, `check`는 출처 레포·sha"로 처리하고 옮긴 문서로 배정
- **검증 변경**: 커밋 8 ⑤는 `review/*.json`의 reason `위치` 항목이 모두 `fact`·`target`을 가짐으로 읽음
