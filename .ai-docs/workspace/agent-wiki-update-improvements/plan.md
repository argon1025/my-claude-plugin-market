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

## Re-plan 2026-10-02 — 0.7.0 드라이런 결과 반영: 근거 없는 교체 허용, diff 분할, 절차 결함 4건

### 의도

- **왜**: 0.7.0 드라이런(onestore-cmsapp 머지 40건)에서 앞 절 개선은 동작했으나, 반영 판정 파일 누락, 재배정된 사실 때문에 커서가 물러나는 원복 규칙, 추출 프롬프트의 치환 변수 충돌, 같은 머지 안 커밋 메시지·코드 값 불일치, 큰 diff 미독(agent `f415b06` 2964줄, front #203 400KB 절단)이 남았고, 의도 근거가 없는 교체를 막는 규칙은 범위 안 전사와 맞지 않음
- **누가**: 위키 운영자가 `/agent-wiki:update`를 실행하고 PR을 리뷰하며, 정합 보정은 이후 audit 스킬이 맡음
- **완료**: update가 범위 안 diff 값을 근거 없이 교체하고, 120KB를 넘는 diff를 조각으로 나눠 끝까지 읽히게 하며, 위 절차 결함 4건이 문장 단위로 고쳐진 agent-wiki 0.7.0이 개인판에 커밋되고 사내판에 미러링된 상태

### 배경

- **드라이런 산출물**: 위키 clone `/var/folders/xk/xzrxhwr93z5gg36cm50kl2v00000gn/T/tmp.DIrf5H7FTA`, 추출·판정 `/var/folders/xk/xzrxhwr93z5gg36cm50kl2v00000gn/T/tmp.zqwbzHDCu0`(work.json, facts.json, applied/, review/, graph/, pr.md) — 재부팅 시 사라질 수 있음
- **판정 파일 누락**: 반영 에이전트 2개가 출력 경로의 `tmp.zqwbzHDCu0` 단계를 빠뜨리고 `$TMPDIR/applied/`에 썼고, `apply.md` 2·3·6장에는 출력 파일 존재 확인 규칙이 없음(update `SKILL.md` 3장 추출에만 있음)
- **원복 커서**: 검토가 `onestore-cmsapp-api/binary-signing-fingerprint.md`의 유일한 불릿(F60)을 위치 사유로 옮겨 문서를 reject했고, F60은 4장 재배정으로 `google-developer-verification.md`에 반영됨 — `apply.md` 5장은 원복 문서 사실 전부를 `검토 기각`으로 넘기고, `SKILL.md` 6장 원복 규칙과 `wiki-pr.md` 판정 표(`검토 기각`이 최우선)가 그 사실을 따라 커서를 150727c 앞으로 물림
- **치환 충돌**: `SKILL.md` 3장 추출 프롬프트 graph 줄의 `` 간선 to는 등록 레포 `{domain}/{slug}`만 쓴다 ``는 형식 표기인데 `{slug}`가 같은 프롬프트의 치환 변수라 "`{domain}/onestore-cmsapp-client`만"으로 바뀜, add `SKILL.md` 3장 graph 줄도 같은 표기
- **같은 머지 불일치**: 추출 병합 규칙 "값이 다른 두 사실은 둘 다 남긴다" 때문에 api `150727c`의 재조회 API 경로가 코드(`POST /googlePackageRegistration/save/v1`)와 커밋 메시지(`.../check/v1`) 두 사실로 나왔고 정리 규칙이 없어 메인이 기각함
- **diff 크기**: `collect_update_merges.py`는 diff 한 건을 파일 하나로 쓰고 `DIFF_MAX_BYTES` 400KB에서 자르며, `batches()`가 커밋 행 단위로 `BATCH_BYTES` 200KB까지 묶음 — `{sha7}.diff` 하나가 177KB면 에이전트가 앞 410줄 남짓만 읽음
- **quote 사용처**: update `SKILL.md` 3장 추출 출력의 `quote`, `apply.md` 0장 quote 설명과 2장 판정(빈 quote면 건너뜀), 규약 7장 `**다른 값**`, `wiki-pr.md` 판정 표 `교체 · 기존 {old} · 인용 "{quote}"`와 예시 F2 행 — add는 `quote`를 `사용자 확인 YYYY-MM-DD 새 값 선택`으로 채워 계속 씀

### 확정 결정 (사용자 확인 2026-10-02)

- 폐기: `## 확정 결정`의 `**다른 값(A)**` 중 "값이 다른 수정은 … 의도를 확인할 때만 교체하고 없으면 건너뜀" — update는 범위 안 머지 diff 값으로 근거 없이 교체함, 사용자 문장 "그냥 근거없는 교체도 허용하자 나중에 감사 스킬에서 수정하면 되니까"
- 폐기: `## 확정 결정`의 `**기각 항목**` 중 "10의 … diff 분할" — 120KB를 넘는 diff를 파일 경계 조각으로 나눔
- **quote**: update 추출 출력에서 `quote`를 빼고 정리 단계가 `source`(근거 머지 `{slug}@{sha7}` 목록)로 채움 — update에서는 건너뜀이 생기지 않으며 PR 교체 사유는 근거 sha로 표시함
- **diff 분할**: 수집 스크립트가 120KB 넘는 diff를 `diff --git` 경계 조각으로 나누고, 조각마다 묶음 단위가 되며 400KB 절단을 없앰
- **결함 4건**: 출력 파일 확인, 재배정 사실을 원복에서 제외, 치환 변수 충돌 제거, 같은 머지 안 커밋 메시지·작업 기록과 변경 줄이 다르면 변경 줄 값만 남김
- **버전**: 아직 머지 전이므로 agent-wiki 0.7.0·개인판 마켓플레이스 4.1.0을 유지하고, 사내판 미러링(앞 절 커밋 9)은 이 절의 마지막 커밋으로 옮김

### 작업

| 파일 | 변경 | 사다리 |
|---|---|---|
| `agent-wiki/scripts/collect_update_merges.py` | diff 조각 분할, 절단 상한 제거, 묶음을 조각 단위로 | 기존 파일 수정 |
| `agent-wiki/skills/update/SKILL.md` | 3장 `{diff 목록}` 출처·quote 삭제·병합 문장·graph 줄, 4장 quote 출처, 6장 원복 | 기존 파일 수정 |
| `agent-wiki/references/apply.md` | 서두 출력 확인, 0장 quote, 5장 재배정 사실 제외 | 기존 파일 수정 |
| `agent-wiki/references/doc-contract.md` | 7장 `**다른 값**` update 근거 | 기존 파일 수정 |
| `agent-wiki/templates/wiki-pr.md` | 교체 사유 `근거`, 검토 기각 원천 | 기존 파일 수정 |
| `agent-wiki/skills/add/SKILL.md` | 3장 graph 줄 치환 충돌 | 기존 파일 수정 |
| 사내판 `plugins/agent-wiki/**`, `.claude-plugin/marketplace.json` | 앞 절 `### 사내판 미러링`과 같은 방식 | 기존 파일 수정 |

#### agent-wiki/scripts/collect_update_merges.py

- **상수**: `DIFF_MAX_BYTES = 400_000` 삭제, `BATCH_BYTES = 200_000` → `120_000`이며 조각 상한과 묶음 상한을 같은 값으로 씀 — 주석 `# 추출 에이전트 1회가 끝까지 읽는 분량 — 건수는 사실 병합 품질, 바이트는 Read 반복 횟수.`
- **분할**: `extract_diff()`가 본문을 `\ndiff --git ` 경계로 파일 단위로 자르고 `BATCH_BYTES`를 넘지 않게 이어 붙여 조각을 만듦 — 파일 하나가 상한을 넘으면 그 파일만 줄 경계로 상한마다 자름
- **파일명·머리말**: 첫 조각은 `{sha7}.diff`에 지금 머리말 전체를, 둘째부터는 `{sha7}.{k}.diff`에 `# {slug} {sha} ({date})`, `# 제목: {subject}`, `# 조각 {k}/{n} — 커밋 메시지·변경 파일 목록은 {sha7}.diff` 세 줄만 둠, 첫 조각 머리말의 절단 문구 줄은 `# 변경 파일 {N}건 — diff 조각 {n}개` 로 바꿈
- **행 필드**: `row["truncated"]`·`row["diff_path"]`·`row["bytes"]`를 `row["parts"] = [{"path", "bytes"}]`로 바꿈
- **묶음**: `batches()`가 커밋 행 대신 조각을 순서대로 묶어 `{"id", "shas", "diffs", "bytes"}`를 냄 — `shas`는 묶음에 든 조각의 sha7 중복 제거, `diffs`는 조각 경로, 건수 상한 `BATCH_MERGES`는 조각 수에 적용
- **머리 주석**: 첫 줄의 "diff를 파일로 꺼내 묶음으로 자른다"를 "diff를 조각 파일로 꺼내 묶음으로 자른다"로

#### agent-wiki/skills/update/SKILL.md

- **3장 서두**: `` `{diff 목록}`은 그 묶음 `shas`의 `commits[].diff_path` `` → `` `{diff 목록}`은 그 묶음 `diffs` ``, `(다시 나누지 않음)` 유지
- **3장 프롬프트 입력 줄**: `머리말에 PR 제목·커밋 메시지·변경 파일 목록·절단 여부가 있다` → `머리말에 PR 제목·커밋 메시지·변경 파일 목록이 있고, 조각 파일은 첫 조각의 머리말을 가리킨다`
- **3장 graph 줄**: `` 간선 to는 등록 레포 `{domain}/{slug}`만 쓴다 `` → `간선 to는 {지도}의 등록 레포 키만 쓴다`
- **3장 병합 줄**: `병합: 묶음 안 같은 주장은 하나로 합쳐 shas에 모두 적고, 값이 다른 두 사실은 둘 다 남긴다.` → `병합: 묶음 안 같은 주장은 하나로 합쳐 shas에 모두 적는다. 값이 다른 두 사실은 둘 다 남기되, 같은 머지의 커밋 메시지·작업 기록이 변경 줄과 다르면 변경 줄 값만 남긴다.`
- **3장 출력 형식**: `"quote": …` 줄 삭제
- **4장 facts.json 문장**: `` `input`은 빈 배열이고 나머지 키는 추출 값 그대로 `` → `` `quote`는 `source`를 쉼표로 이은 값, `input`은 빈 배열이고 나머지 키는 추출 값 그대로 ``
- **6장 원복 있음**: `원복한 문서 사실의 그 레포 근거 머지(`source`) 중` → `` `검토 기각`으로 넘긴 사실의 그 레포 근거 머지(`source`) 중 ``

#### agent-wiki/references/apply.md

- **서두**: `어느 서브에이전트도 커밋하지 않습니다.` 뒤에 `서브에이전트의 출력 파일이 정해진 경로에 없으면 다음 장 전에 그 에이전트를 다시 실행합니다.` 추가
- **0장 quote**: `규약 7장 다른 값의 변경 근거 원문 — add는 …` → `규약 7장 다른 값의 변경 근거 — update는 근거 머지 목록, add는 `사용자 확인 YYYY-MM-DD 새 값 선택`, 없으면 빈 문자열`
- **5장**: `그 사실을 `검토 기각`으로 넘깁니다` → `` 그 사실을 `검토 기각`으로 넘깁니다 — 4장에서 다른 문서로 재배정한 사실은 그 문서의 판정을 따름 ``

#### agent-wiki/references/doc-contract.md

- **7장 다른 값**: `변경 의도를 밝힌 근거(커밋 메시지·PR 본문·작업 기록 또는 사용자 확인)가 있을 때만 고치고` → `변경 의도를 밝힌 근거(커밋 메시지·PR 본문·작업 기록 또는 사용자 확인, update는 반영 범위 안 머지 diff 자체)가 있을 때만 고치고`

#### agent-wiki/templates/wiki-pr.md

- **판정 표**: `` `교체 · 기존 {old} · 인용 "{quote}"` `` → `` `교체 · 기존 {old} · 근거 {quote}` ``, `` `검토 기각 · {reject_reason}` `` 원천 `5장에서 원복한 문서의 사실 전부` → `5장 `검토 기각` 사실`
- **예시 F2 행**: `교체 · 기존 \`모든 삭제\` · 인용 "…"` → `교체 · 기존 \`모든 삭제\` · 근거 shop-api@c61a8ab`

#### agent-wiki/skills/add/SKILL.md

- **3장 graph 줄**: `` slug와 간선 to는 등록 레포의 `{domain}/{slug}` 기준으로 쓰고, `` → `slug와 간선 to는 {지도}의 등록 레포 키로 쓰고,`

### 커밋 분해

개인판 `feat/agent-wiki-update-improvements` 브랜치에서 이어 작업함. `{fx}`는 검증용 임시 폴더, `{ws}`는 `~/.agent-wiki-workspace`, `{T}`는 드라이런 위키 clone `/var/folders/xk/xzrxhwr93z5gg36cm50kl2v00000gn/T/tmp.DIrf5H7FTA`.

| # | 범위 | 검증 |
|---|---|---|
| 1 | `collect_update_merges.py` 분할 | `python3 -m py_compile agent-wiki/scripts/collect_update_merges.py` 통과. `{T}`(registry·state만 읽음)를 `--wiki`로 `python3 agent-wiki/scripts/collect_update_merges.py --wiki {T} --workspace {ws} --domain onestore-cmsapp --out {fx}/out --max-merges 40` 실행 시 종료 코드 0, `{fx}/out/onestore-cmsapp-agent/f415b06.2.diff` 존재, `find {fx}/out -name '*.diff' -size +125k` 0행, `{fx}/out/onestore-cmsapp-front/934d282*.diff` 조각 합이 400KB 초과, `work.json`의 모든 `batches[]`에 `diffs` 키가 있고 `grep -c '"diff_path"\|"truncated"' {fx}/out/work.json` 0 |
| 2 | update `SKILL.md`·`apply.md`·`doc-contract.md`·`wiki-pr.md`·add `SKILL.md` 문장 | `grep -c '"quote"' agent-wiki/skills/update/SKILL.md` 0, `grep -rn '{domain}/{slug}\`만\|{domain}/{slug}\` 기준' agent-wiki/skills` 0행, `grep -c 'diff_path' agent-wiki/skills/update/SKILL.md` 0, `grep -n '다시 실행합니다' agent-wiki/references/apply.md` 1행(서두), `grep -n '재배정한 사실은' agent-wiki/references/apply.md` 1행, `grep -n 'update는 반영 범위 안 머지 diff' agent-wiki/references/doc-contract.md` 1행, `grep -c '인용 "' agent-wiki/templates/wiki-pr.md` 0, `grep -n '검토 기각.*사실' agent-wiki/skills/update/SKILL.md` 1행(6장) |
| 3 | 사내판 미러링 | 앞 절 커밋 9 검증과 같음 — 사내판에서 `diff -rq plugins/agent-wiki {개인판}/agent-wiki` 결과가 `config.json`·`references/publish.md`·`README.md` 3행뿐, `grep -rn '건너뜀·위치 재배정 행\|`건너뜀`·`위치 재배정` 행' plugins/agent-wiki` 0행, `python3 -m json.tool .claude-plugin/marketplace.json` 통과 |

### 특이 사항

- **전체 드라이런 생략**: 이 절은 스크립트 실행과 문장 grep으로만 검증하며, 근거 없는 교체·조각 묶음의 실제 추출 품질 확인은 다음 실제 update 실행 결과로 봄
- **교체 오판 한계**: 근거 없는 교체는 추출이 값을 잘못 읽으면 맞는 문장을 덮어씀 — 검토의 근거 머지 시점 코드 확인과 PR `교체` 행의 기존·새 값, 이후 audit이 보정 경로임
- **조각과 병합**: 한 머지가 여러 묶음으로 나뉘면 묶음 안 병합이 아니라 4장 정리 병합에 기대며, 둘째 조각부터는 커밋 메시지가 없어 작업 기록 근거 사실은 첫 조각에서만 나옴
- **긴 경로 오기**: 판정 파일 누락의 원인인 긴 `mktemp` 경로 오기는 출력 확인으로 재실행할 뿐 막지는 않음 — 반복되면 `{work}`를 짧은 고정 접두 경로로 바꿈
- **범위 밖**: 재검토가 첫 반영 줄을 `ids` 없이 지우는 경우(adhub-product-meta-sync 4건)와 같은 이름 집합 충돌(`AdhubResultCode`)은 그대로 둠

## Re-plan 2026-10-02 — 변경 검증 드라이런: 조각은 Read 크기로만, 묶음은 머지 단위, 거짓이 된 기존 문장 정리

### 의도

- **왜**: 변경 검증 드라이런에서 diff 조각마다 묶음을 만들자 추출 에이전트가 같은 머지의 다른 조각까지 모두 읽어 한 머지(front 934d282)에서 사실 171건이 중복으로 나왔고, 반영 에이전트는 표현이 다른 사실을 `추가`로 판정해 그 사실 때문에 거짓이 된 기존 문장을 남김
- **누가**: 위키 운영자가 `/agent-wiki:update`를 실행하고 PR을 리뷰하며, 등록 레포 에이전트가 그 문서를 읽음
- **완료**: 같은 머지의 조각이 한 묶음에 함께 들어가 에이전트 1개가 목록 순서대로 끝까지 읽고, 반영이 추가·교체한 사실과 어긋나는 기존 문장을 같은 편집에서 고치는 agent-wiki 0.7.0이 개인판에 커밋되고 사내판 미러링이 갱신된 상태

### 배경

- **읽기 한계의 실체**: front 묶음 3개가 묶음 상한 120KB를 넘어 934d282 조각 4개(444KB, 6287줄)를 모두 마지막 줄까지 읽었음 — 0.7.0 드라이런의 미독은 총량이 아니라 Read 1회에 담기지 않는 파일 하나(f415b06 177KB·2964줄)가 원인이었음
- **중복 원인**: 둘째 이후 조각 머리말 `# 조각 {k}/{n} — 커밋 메시지·변경 파일 목록은 {sha7}.diff`와 추출 프롬프트 입력 줄 "조각 파일은 첫 조각의 머리말을 가리킨다"를 따라 에이전트가 다른 조각을 열었고, 금지 "diff 밖 파일 열기"는 같은 머지의 조각을 막지 못함 — front b04만 첫 조각 머리말만 읽고 나머지 조각은 열지 않음
- **현재 수집 코드**: `agent-wiki/scripts/collect_update_merges.py`의 `split()`이 `BATCH_BYTES`(120KB)로 조각을 자르고, `batches()`가 조각 단위로 `BATCH_MERGES`(5)·`BATCH_BYTES`까지 묶어 `{"id", "shas", "diffs", "bytes"}`를 냄 — `extract_diff()`는 `row["parts"] = [{"path", "bytes"}]`를 채움
- **거짓이 된 기존 문장**: director-cut F39(CMS_APP_5180 = DC Y 게임을 앱 카테고리로 바꾼 검증요청)·F42(api에 directorCutYn 변경 거부 서버 검증 없음)가 `추가`로 반영되며 "검증요청 시 5180 검증은 두지 않음"(결정 절)과 "N에서 Y 설정은 화면·서버 검증 양쪽에서 막힘"(규칙 절)이 남음 — 규약 7장 `**현재 값만**`이 같은 편집에서 지우라고 하지만 반영 프롬프트 판정 줄에 없고, 검토는 이번 변경 줄만 고침
- **확인된 동작**: 같은 검증에서 변경 줄 우선(api 150727c 경로 1건), 치환 충돌 제거, 재배정 사실 원복 제외(api 커서 2145cd9), `quote` 삭제, 근거 없는 교체(instant-game-deploy F97 `교체`)는 의도대로 동작함
- **사내판 상태**: 사내판 `feat/agent-wiki-update-improvements` 브랜치에 0.7.0 미러링 커밋 `3c87f4f`가 있음

### 확정 결정 (사용자 확인 2026-10-02)

- 폐기: 앞 Re-plan 절 `**diff 분할**`의 "조각마다 묶음 단위가 되며" — 조각은 Read 크기를 맞추는 파일 분할일 뿐이고 묶음은 머지 단위로 둠, 사용자 문장 "diff 파일목록 전달하고 하나 씩 읽으라고 하면 문제없는거같긴하네"
- **묶음**: 같은 머지의 조각은 항상 한 묶음에 들어가고, 묶음은 머지 단위로 `BATCH_MERGES` 5건·`BATCH_BYTES` 200KB까지 합치며, 머지 하나가 상한을 넘으면 그 머지만으로 묶음 하나
- **조각 크기**: 조각 상한은 `PART_BYTES` 120KB로 따로 둠
- **읽기 지시**: 추출 프롬프트가 diff 목록을 한 파일씩 순서대로 끝까지 읽게 하고 목록 밖 파일 열기를 금지함
- **거짓이 된 문장**: 반영 판정 줄에 "추가·교체한 사실 때문에 거짓이 되는 기존 문장은 같은 편집에서 고치거나 지우고 교체로 적는다"를 둠
- **버전**: 머지 전이므로 0.7.0 유지, 사내판은 같은 브랜치에 미러링 커밋을 하나 더 남김

### 작업

| 파일 | 변경 | 사다리 |
|---|---|---|
| `agent-wiki/scripts/collect_update_merges.py` | `PART_BYTES` 분리, `batches()` 머지 단위 복귀, 둘째 조각 머리말 문구 | 기존 파일 수정 |
| `agent-wiki/skills/update/SKILL.md` | 3장 입력 줄·금지 줄 | 기존 파일 수정 |
| `agent-wiki/references/apply.md` | 2장 판정 줄 | 기존 파일 수정 |
| 사내판 `plugins/agent-wiki/scripts/collect_update_merges.py`·`skills/update/SKILL.md`·`references/apply.md` | 개인판 복사 | 기존 파일 수정 |

#### agent-wiki/scripts/collect_update_merges.py

- **상수**: 주석과 함께 `PART_BYTES = 120_000`(`# diff 조각 상한 — Read 1회가 끝까지 담는 크기.`)을 두고, `BATCH_BYTES = 120_000` → `200_000`, 묶음 주석은 `# 추출 에이전트 1회가 읽는 묶음 상한 — 건수는 사실 병합 품질, 바이트는 컨텍스트 예산.`으로 되돌림
- **분할**: `split()`과 그 안의 `cut()` 호출 조건·`extract_diff()`의 `split(body, ...)` 인자에서 `BATCH_BYTES`를 `PART_BYTES`로 바꿈
- **둘째 조각 머리말**: `# 조각 {k}/{n} — 커밋 메시지·변경 파일 목록은 {sha7}.diff` → `# 조각 {k}/{n} — 같은 머지 앞 조각에 이어짐`
- **묶음**: `batches()`를 머지 행 단위로 되돌림 — 행 바이트는 `sum(p["bytes"] for p in row["parts"])`, 건수 상한에 닿았거나 바이트 합계가 상한을 넘게 되면 새 묶음, 출력은 `{"id", "shas": 행 sha7 목록, "diffs": 행마다 parts 경로를 순서대로 이은 목록, "bytes"}`

#### agent-wiki/skills/update/SKILL.md

- **3장 입력 줄**: `입력: {diff 목록}을 순서대로 끝까지 Read(길면 offset으로 나눔) — 머리말에 PR 제목·커밋 메시지·변경 파일 목록이 있고, 조각 파일은 첫 조각의 머리말을 가리킨다.` → `입력: {diff 목록}을 목록 순서대로 한 파일씩 끝까지 Read(길면 offset으로 나눔) — 머지마다 첫 파일 머리말에 PR 제목·커밋 메시지·변경 파일 목록이 있고, {sha7}.{k}.diff는 같은 머지의 이어지는 조각이다.`
- **3장 금지 줄**: `금지: diff 밖 파일 열기, 사전 지식으로 채우기.` → `금지: 입력 목록 밖 파일 열기, 사전 지식으로 채우기.`

#### agent-wiki/references/apply.md

- **2장 판정 줄**: `동일·추가·교체는 본문에 반영하고,` → `동일·추가·교체는 본문에 반영하되 추가·교체한 사실 때문에 거짓이 되는 기존 문장은 같은 편집에서 고치거나 지우고 교체로 적으며(old에 기존 문장),`

### 커밋 분해

개인판 `feat/agent-wiki-update-improvements` 브랜치에서 이어 작업함. `{fx}`는 검증용 임시 폴더, `{ws}`는 `~/.agent-wiki-workspace`, `{T2}`는 변경 검증 위키 clone `/var/folders/xk/xzrxhwr93z5gg36cm50kl2v00000gn/T/tmp.jhm0TXsSzc`(registry·state만 읽음).

| # | 범위 | 검증 |
|---|---|---|
| 1 | `collect_update_merges.py` 묶음 머지 단위 | `python3 -m py_compile agent-wiki/scripts/collect_update_merges.py` 통과. `python3 agent-wiki/scripts/collect_update_merges.py --wiki {T2} --workspace {ws} --domain onestore-cmsapp --out {fx}/out --max-merges 40` 종료 코드 0, `find {fx}/out -name '*.diff' -size +125k` 0행, `work.json`에서 front 묶음 하나의 `diffs`가 `934d282.diff`·`934d282.2.diff`·`934d282.3.diff`·`934d282.4.diff`를 모두 담고 agent 묶음 하나가 `f415b06.diff`·`f415b06.2.diff`를 모두 담음, 같은 sha7이 두 묶음의 `shas`에 동시에 나오지 않음(python으로 확인), `grep -c '앞 조각에 이어짐' {fx}/out/onestore-cmsapp-front/934d282.2.diff` 1 |
| 2 | update `SKILL.md`·`apply.md` 문장 | `grep -c '첫 조각의 머리말을 가리킨다' agent-wiki/skills/update/SKILL.md` 0, `grep -n '입력 목록 밖 파일 열기' agent-wiki/skills/update/SKILL.md` 1행, `grep -n '거짓이 되는 기존 문장' agent-wiki/references/apply.md` 1행(2장) |
| 3 | 반영 동작 확인(커밋 없음) | `{T2}`에서 `git -C {T2} checkout -- knowledge` 후, 0.6.1 실행 산출물 `/var/folders/xk/xzrxhwr93z5gg36cm50kl2v00000gn/T/tmp.xzR2WSp1IH/facts.json`의 F39·F42를 `quote`=`source`로 둔 배정으로 새 `apply.md` 2장 프롬프트를 sonnet 에이전트 1개로 director-cut.md에 실행 — 통과 조건: F39·F42 중 하나 이상이 `교체`이고 `grep -c '5180)은 두지 않음\|N에서 Y로 설정은 화면·서버 검증 양쪽에서 막힘' {T2}/knowledge/onestore-cmsapp/director-cut.md` 0 |
| 4 | 추출 동작 확인(커밋 없음) | 커밋 1 산출물의 front 934d282 묶음 하나를 새 `SKILL.md` 3장 프롬프트로 sonnet 에이전트 1개에 실행 — 통과 조건: 에이전트가 조각 4개를 마지막 줄까지 읽었다고 보고하고 출력 JSON이 파싱되며 묶음 밖 파일을 열지 않음 |
| 5 | 사내판 미러링 | 사내판 `feat/agent-wiki-update-improvements` 브랜치에 개인판 세 파일을 복사해 커밋 `fix(agent-wiki): update 조각 묶음 머지 단위·거짓이 된 기존 문장 정리 미러링, 0.7.0` — `diff -rq plugins/agent-wiki {개인판}/agent-wiki` 결과가 `config.json`·`references/publish.md`·`README.md` 3행뿐 |

### 특이 사항

- **대형 머지 한계**: 머지 하나의 diff가 아주 크면(조각 수 증가) 에이전트 1개가 모두 읽어야 함 — 이번 검증의 444KB·6287줄은 끝까지 읽혔으며, 더 큰 머지에서 미독이 다시 보이면 그 머지만 조각 단위 묶음으로 나누는 예외를 검토함
- **기존 문장 정리 범위**: 반영 에이전트가 거짓이 된 기존 문장을 판단하는 것은 같은 문서 안에 한하며, 다른 문서에 남은 거짓 문장은 audit 몫
- **검증 비용**: 커밋 3·4는 서브에이전트 2회만 씀

## Re-plan 2026-10-02 — 반영 확인 실패: 거짓이 된 기존 문장을 식별자로 찾게 함

- **계기**: 앞 절 커밋 3 검증에서 F42는 `교체`로 "화면·서버 검증 양쪽에서 막힘"을 고쳤으나, F39(CMS_APP_5180)를 `## 코드값`에 추가하면서 `## 결정`의 "Director's Cut 필수값 검증(CMS_APP_5180)은 두지 않음"을 에이전트가 "조건이 달라" 남김(`grep -c` 1)
- **결정**: 사용자 선택 "식별자 기준 보강" — 대상 문장을 같은 식별자로 좁히고 절을 가리지 않으며, 판정 기준을 "함께 참일 수 없음"으로 둠
- **apply.md 2장 판정 줄**: `추가·교체한 사실 때문에 거짓이 되는 기존 문장은 같은 편집에서 고치거나 지우고 교체로 적으며(old에 기존 문장),` → `추가·교체한 사실과 같은 식별자(코드값·심볼·필드)를 말하는 기존 문장을 절을 가리지 않고 모두 찾아 그 사실과 함께 참일 수 없으면 같은 편집에서 고치거나 지우고 교체로 적으며(old에 기존 문장),`
- **커밋 분해**: 앞 절 커밋 3 앞에 `fix(agent-wiki)` 커밋 하나(검증 `grep -n '함께 참일 수 없으면' agent-wiki/references/apply.md` 1행, 2장)를 두고, 커밋 3을 같은 통과 조건으로 한 번 다시 실행함 — 다시 실패하면 멈춰 보고함

## Re-plan 2026-10-02 — 추출 확인 실패: 대형 머지만 조각 묶음, 발췌 대체 금지

- **계기**: 앞 절 커밋 4 검증에서 front 934d282(조각 4개 444KB) 단독 묶음의 sonnet 추출 에이전트가 목록 밖 파일은 열지 않았으나 누적 입력 약 19만 토큰에서 grep·sed 발췌로 전환해 `.3.diff` 1247행 이후와 `.4.diff` 대부분을 읽지 않음
- **진단**: Read 1회 상한은 25,000토큰(이 diff들에서 약 400줄)이고 offset으로 이어 읽혀 중단 원인이 아님 — 원인은 에이전트 1개가 읽는 총량이며, 묶음 상한 200KB는 약 11만 토큰(바이트당 약 0.55토큰)이지만 머지 단위 묶음은 단독으로 상한을 넘는 머지에 상한을 적용하지 않음
- **결정**: 사용자 선택 "대형 머지 조각 묶음+발췌 금지" — 앞 절 특이 사항 `**대형 머지 한계**`의 예외를 채택함
- **collect_update_merges.py `batches()`**: 머지마다 조각을 `BATCH_BYTES`까지 이어 붙인 단위로 나누고(상한 이하 머지는 단위 하나) 단위를 지금 규칙(건수 `BATCH_MERGES`·바이트 `BATCH_BYTES`)으로 묶음, `shas`는 중복 제거 — 같은 머지 조각은 상한 이하 머지면 한 묶음, 상한 초과 머지만 여러 묶음
- **PART_BYTES 주석**: `# diff 조각 상한 — Read 1회가 끝까지 담는 크기.`는 진단으로 틀렸으므로 `# diff 조각 상한 — 묶음 상한을 넘는 머지를 여러 묶음에 나누는 단위.`로 바꿈, 값 120KB는 유지
- **update SKILL.md 3장 금지 줄**: `금지: 입력 목록 밖 파일 열기, 사전 지식으로 채우기.` → `금지: 입력 목록 밖 파일 열기, grep·sed 발췌로 대신 읽기, 사전 지식으로 채우기.`
- **커밋 분해**: `fix(agent-wiki)` 커밋 하나(검증: py_compile, 앞 절 커밋 1 명령 재실행 종료 코드 0, 934d282 조각 4개가 묶음 `diffs`에 정확히 한 번씩 나오고 둘 이상 묶음에 걸친 sha는 조각 합이 `BATCH_BYTES` 초과인 머지뿐, 모든 묶음 `bytes`가 `BATCH_BYTES` 이하이거나 조각 하나뿐, `grep -n 'grep·sed 발췌로 대신 읽기' agent-wiki/skills/update/SKILL.md` 1행) 뒤 앞 절 커밋 4를 934d282 조각이 든 묶음마다 sonnet 에이전트 1개로 다시 실행함 — 통과 조건: 각 에이전트가 목록 파일을 Read 호출로 마지막 줄까지 읽고(호출 기록으로 확인) 발췌 대체·목록 밖 파일 열기가 없으며 출력 JSON이 파싱됨, 다시 실패하면 멈춰 보고함
