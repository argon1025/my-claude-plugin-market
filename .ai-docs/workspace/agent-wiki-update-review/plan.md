# agent-wiki update 스킬 신설과 코드값 표 완결성 보장

## 의도

- **왜**: agent-wiki에는 머지된 코드를 위키에 반영하는 경로가 없고, diff에서 뽑은 사실만으로는 코드값·상태 표가 일부만 담긴 채 전체 목록처럼 읽힘
- **누가**: 위키 운영자가 `/agent-wiki:update`를 실행하고, 등록 레포에서 계획·구현·리뷰하는 에이전트가 그 문서를 읽음
- **완료**: `/agent-wiki:update`가 지정한 도메인 레포의 머지를 시간 순 묶음으로 처리해 `doc-contract.md`를 따르는 문서를 PR로 올리고, 그 PR 안의 코드값 표가 전 원소를 담거나 일부임을 밝힌 상태

## 배경

- **원본 스킬**: `llm-wiki/skills/update/SKILL.md`(범위, 추출, 배정, 반영, 검토, 검증·커밋·커서, 게시 7장)와 `llm-wiki/scripts/update.py`(`pending`·`advance`), `llm-wiki/references/publish.md`, `llm-wiki/templates/update-pr.md`가 이관 원본임
- **이관 제외**: llm-wiki의 문서 `type`, `catalog.py --check`, `graph.py`(간선 `kind`·`contracts`·책임·호스트 배정), `--range`·`--repo`, `update.py advance`는 가져오지 않음
- **registry 형식**: `registry.json`은 `domains.{domain}.repos.{slug}`에 `remote`(`git remote get-url origin` 전체 URL)·`defaultBranch`·`status`·`stack`·`summary`·`responsibilities`·`hosts`를 둠 (`agent-wiki/scripts/verify_register_file.py`)
- **쓰기 방식**: agent-wiki 쓰기 스킬은 `mktemp -d` 임시 clone `{tmp}`에서 커밋·push하며 `baseRoot`는 세션 시작마다 원격으로 강제 정리되는 읽기 전용 사본임 (`agent-wiki/skills/register/SKILL.md`, `agent-wiki/scripts/sync_wiki.py`)
- **워크스페이스**: `workspace.root/{slug}`는 register가 원격 기본 브랜치로 강제 정리하는 전체 clone이며 README가 "사용 자유, 변경 사항 유실 가능"으로 고지함
- **세션 주입**: 문서 목록은 `knowledge/{domain}/*.md`·`knowledge/{domain}/{slug}/*.md`를 한 단계만 읽고 frontmatter `description`만 씀 — `state/`는 주입에 영향 없음 (`agent-wiki/scripts/generate_document_list.py`)
- **스크립트 관례**: agent-wiki 스크립트는 파일마다 머리 주석 2~3줄과 자체 `git()` 헬퍼를 두는 단일 목적 스크립트이며 다른 플러그인 모듈을 import하지 않음

## 확정 결정 (사용자 확인 2026-09-29)

- **게시**: 반영 결과는 위키 원격에 `wiki-update/{YYYYMMDD-HHMM}` 브랜치 PR로 올리고 PR 머지를 승인 지점으로 둠
- **PR 절차 분리**: PR 확인·생성 절차는 `agent-wiki/references/publish.md` 별도 파일로 관리해 회사 위키에서는 그 파일만 고침 — 이번 구현은 `gh`
- **커서**: 레포별 커서는 위키 `state/{slug}.json`(`cursor`·`at` 2키)에 둠
- **첫 실행**: 커서 없는 레포는 스킬이 사용자에게 어느 지점을 커서로 등록할지 물음
- **도메인 한정**: 추출 대상은 도메인 하나로 한정함 — 전 도메인을 한 번에 돌리면 머지가 너무 많아짐
- **스크립트 최소화**: 스크립트는 재현성이 필요한 머지 수집(범위 계산·diff 추출·묶음)만 두고, 위키 파일 수정(문서·커서)은 에이전트가 직접 함
- **기계 검사 게이트 없음**: 문서 규약의 형식 검사 스크립트를 두지 않고 검토 에이전트가 규약 1~7장을 의미와 형식 모두 읽어 판정함 — 형식 통과가 품질 통과로 오인되는 것을 막음
- **완결성 원칙**: 닫힌 집합은 전 원소를 담거나 일부임을 밝힘 — 추출 사실의 `set` 표시, 반영 단계의 머지 시점 정의 전 원소 보충, 표 위 `원본:` 줄, 검토 단계의 원소 수 대조
- **그래프 불변**: update는 `registry.json`·`deps.json`을 고치지 않음 — register 소관

## 선행 읽기

- `agent-wiki/references/doc-contract.md` — 스킬 프롬프트가 장 번호로 인용하는 판정 기준이며 이번에 4·7장을 고침
- `llm-wiki/skills/update/SKILL.md`, `llm-wiki/scripts/update.py` — 이관 원본, 묶음·정렬·diff 절단 로직을 그대로 가져옴

## 작업

| 파일 | 변경 | 사다리 |
|---|---|---|
| `agent-wiki/references/doc-contract.md` | 4장 `원본:` 줄·코드값 표 규칙, 7장 집합 완결 조항, 4장 예시 갱신 | 기존 파일 수정 |
| `agent-wiki/scripts/collect_update_merges.py` | 신설 — 도메인 레포의 미처리 머지 수집·diff 추출·묶음 | ⑦ `llm-wiki/scripts/update.py` `pending` 이식, 레포 N개 순회·force-push 판정·시각 정렬·diff 절단·묶음 경계를 에이전트가 bash로 하면 실행마다 결과가 달라짐 |
| `agent-wiki/skills/update/SKILL.md` | 신설 — update 스킬 | ⑦ 새 스킬 |
| `agent-wiki/references/publish.md` | 신설 — 열린 PR 확인·PR 게시 절차(`gh`) | ⑦ 사용자 결정(호스트 교체 지점 분리) |
| `agent-wiki/templates/update-pr.md` | 신설 — PR 본문 형식 | ⑦ llm-wiki 템플릿에서 그래프 절 제거, 보충 행 추가 |
| `agent-wiki/README.md` | 스킬 표·위키 구조(`state/`)·로컬 사본·요구 사항(`gh`) 갱신 | 기존 파일 수정 |
| `agent-wiki/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | agent-wiki 0.5.0, 마켓플레이스 `metadata.version` 3.6.0 | 기존 파일 수정 |

커서 기록은 스크립트 없이 에이전트가 JSON 한 개를 씀(①) — 커서 sha는 `work.json` `commits`에서 오므로 `origin/{branch}`의 first-parent 조상임이 보장되어 별도 조상 검증이 필요 없음.

### agent-wiki/references/doc-contract.md

- **4장 절 표**: `## 코드값` 칸을 "코드와 뜻의 표 — 상태 코드 포함", `## 상태와 전이` 칸을 "전이 조건과 전이를 일으키는 주체 — 상태 코드 자체는 `## 코드값` 표"로 고침 — `원본:` 줄 적용 대상을 코드값 표 하나로 모음
- **4장 불릿 추가**: 아래 3개를 `**표**` 불릿 뒤에 둠
  - `**원본 줄**`: `## 코드값` 표마다 바로 위에 `` 원본: `{정의 식별자}` 전 N종 `` 또는 `` 원본: {원본 이름} — 일부 ``를 두고, 전 N종이면 표 행 수가 N — 에이전트가 표에 없는 값을 없는 값으로 판단해도 되는지 가름
  - `**집합 표기**`: 닫힌 집합(enum·공통코드·상태·허용 채널처럼 원소가 정의된 값)의 원소는 개수와 무관하게 `## 코드값` 표로 씀 — 문장 속 나열은 원본 줄을 붙일 자리가 없음
  - `**뜻 미확인**`: 원본 정의·주석·사용처에서 뜻을 확인하지 못한 원소는 뜻 칸을 `뜻 미확인`으로 둠 — 행을 빼면 표가 일부가 됨
- **4장 예시**: 도메인 루트 예시의 코드값 표 위에 `` 원본: 공통코드 `CR` — 일부 `` 줄 추가
- **7장 불릿 추가**: `**근거 범위**` 뒤에 `**집합 완결**`: 코드값 표의 원소를 더하거나 고치면 diff 밖이어도 머지 시점 원본 정의를 읽어 표 전체를 원본과 맞추고, 원본이 코드 밖(DB 적재 공통코드 등)이면 diff가 보여 준 원소만 담고 `— 일부`로 밝힘

### agent-wiki/scripts/collect_update_merges.py

- **사용법**: `collect_update_merges.py --wiki {tmp} --workspace {workspace.root} --domain {domain} --out {dir} [--start SLUG=REV]... [--max-merges N]` (기본 40)
- **대상**: `registry.json` `domains.{domain}.repos`의 레포만 — 도메인이 없으면 종료 1
- **clone**: `{workspace}/{slug}`가 없으면 `git clone {remote}`, 있으면 `remote set-url origin {remote}` 후 `fetch origin {defaultBranch}` — 작업 트리는 건드리지 않고 `origin/{defaultBranch}` ref만 읽음, 실패는 `skipped` 사유
- **커서**: `{tmp}/state/{slug}.json` `cursor`, 없으면 `--start` 값(`HEAD` 또는 sha, `origin/{branch}` 조상이어야 함), 둘 다 없으면 `unset[slug]`에 `head`(sha7)와 `candidates[{label, sha}]`(`HEAD`, `최근 10건 앞`, `최근 30건 앞` — first-parent 이력이 모자라면 해당 후보 생략)를 기록
- **이식 로직**: `update.py`의 `first_parent`, `extract_diff`(머리말·딸린 커밋 메시지·400KB 절단·`EXCLUDE_PATHSPECS`), `batches`(5건·500KB), 누적 최대 시각 정렬, 전역 예산 선택, force-push 판정(`merge-base --is-ancestor`)을 그대로 가져옴
- **work.json**: `order[{slug, sha7, date}]`, `repos[slug]{path, branch, head, cursor, commits, batches, remaining}`, `skipped{slug: 사유}`, `unset{slug: {head, candidates}}`
- **종료 코드**: `unset`이 있으면 20(diff 추출 없이 work.json만 씀), 처리할 머지나 부트스트랩이 있으면 0, 없으면 10, 오류 1 — 마지막 줄에 work.json 경로
- **부트스트랩**: `--start`로 받은 레포는 머지 0건이어도 `repos`에 넣어 스킬이 커서를 기록하게 함

### agent-wiki/skills/update/SKILL.md

frontmatter `name: update`, `disable-model-invocation: true`, 영문 description 한 줄. 서두에 config 값 사용, `GIT_TERMINAL_PROMPT=0`, 규약·스크립트 경로는 `${CLAUDE_PLUGIN_ROOT}` 전개 절대 경로로 서브에이전트에 넘긴다는 문장을 register와 같은 문체로 둠. 인자는 `--domain {domain}`, `--max-merges N`, `--dry-run`.

- **1. 준비**: `mktemp -d`로 `{tmp}`(위키 clone, `-b {baseBranch}`)와 `{work}`(스크래치) 생성, clone 실패나 `registry.json` 부재면 `/agent-wiki:init` 안내 후 중단. `--domain`이 없거나 registry에 없으면 AskUserQuestion으로 도메인을 고름(현재 레포가 등록돼 있으면 그 도메인을 첫 옵션, 도메인마다 레포 수 병기). `--dry-run`이 아니면 `publish.md` 1장(열린 update PR 확인)
- **2. 범위**: `collect_update_merges.py` 실행 — 20이면 `unset` 레포마다 AskUserQuestion(한 라운드 4개까지, 옵션은 `candidates`, 기타 입력으로 sha) 후 `--start`를 붙여 재실행, 10이면 한 줄 보고 후 종료, 1이면 stderr 전달 후 중단, 0이면 `--dry-run`이 아닐 때 `git -C {tmp} switch -c wiki-update/{YYYYMMDD-HHMM}`
- **3. 추출**: 묶음마다 Agent 1회 병렬(`model: sonnet`, 출력은 `{work}/facts/{slug}/{batch}.json`, 응답은 건수만), 묶음 1개·머지 3건 이하면 메인 직접 처리 — 프롬프트는 llm-wiki 2장에서 `type`·그래프 스키마를 빼고 사실 키를 `fact, topic, code, set, quote, shas`로 둠. `set`은 닫힌 집합의 원소를 다루는 사실이면 정의 위치 `경로#심볼` 또는 코드 밖 원본 이름, 아니면 빈 문자열. 기준은 규약 1장, 금지는 diff 밖 파일 열기
- **4. 배정(메인)**: 사실 병합(같은 주장은 `shas` 합집합), `order` 기준 시각 순 `F1`부터 번호, 규약 2장으로 위치, 7장 대조(`{tmp}/knowledge/{domain}`·`{domain}/{slug}` 한 단계 `*.md`의 description과 `grep -ril`), 대상 없는 사실은 같은 위치끼리 주제로 묶어 규약 3장 한 주제가 서면 신규 문서, 아니면 `기각 — 한 주제 아님`. 문서별 `set_sha`는 `set` 사실이 있으면 그 레포의 이번 실행 마지막 처리 머지 sha. `{work}/assign.json`에 기록
- **5. 반영**: 문서 1장에 Agent 1회 병렬(`model: sonnet`, 커밋 금지) — 기준 규약 2~7장, 판정 동일·추가·교체·건너뜀. `set` 사실이 있는 문서만 `git -C {workspace}/{slug} show {set_sha}:{경로}`·`git -C {workspace}/{slug} grep -n {심볼} {set_sha}`로 원본 정의와 뜻을 읽어 규약 7장 집합 완결 적용, 그 밖의 레포 조회 금지. 출력 `{work}/applied/{doc_slug}.json` — `{doc, created, verdicts[{id, verdict, summary, old}], completed[{set, source, total, added, unresolved}]}`
- **6. 검토(유일한 품질 게이트)**: 문서 1장에 Agent 1회 병렬(모델 상속, 커밋 금지) — 문서를 끝까지 읽고 규약 1~7장을 의미(1장 판정, 5장 문장, 6장 겹침)와 형식(2장 위치·파일명, 3장 description, 4장 절 이름·순서·`원본:` 줄) 모두 판정. 범위는 이번 변경 줄·description·이번에 손댄 코드값 표, 1장 코드 확인과 원소 수 대조는 `git -C {repo_path} show|grep {sha}`로 머지 시점 레포를 읽음. 위반은 고치되 새 사실 추가는 금지하고, `전 N종` 표의 원소가 원본 정의와 다를 때만 원본에 맞춤(예외). 고칠 수 없는 문서는 `reject: true`와 사유. 출력 `{work}/review/{doc_slug}.json` — `{doc, removed[{bullet, reason, ids}], fixed_sets[{set, before, after}], reject, reject_reason}`
- **7. 커밋·커서**: `reject: true` 문서와 검토로 본문이 빈 신규 문서는 `git -C {tmp} checkout -- {경로}`(신규는 삭제)로 원복해 `검토 기각`으로 넘김. `--dry-run`이면 `git -C {tmp} diff`·신규 문서 경로·집계를 보고하고 커밋 없이 `{tmp}`·`{work}` 경로를 남긴 채 종료. 아니면 문서마다 규약 8장 커밋, 레포마다 처리한 마지막 머지 전체 sha로 `{tmp}/state/{slug}.json`에 `{"cursor": sha, "at": "YYYY-MM-DD"}`를 Write(원복 문서가 있으면 그 사실의 첫 머지 직전까지, 사실 0건 머지와 부트스트랩 레포도 전진, 부트스트랩 머지 0건이면 `--start` sha) 후 `chore(update): {slug} 커서 {sha7} · 머지 N건` 커밋
- **8. 게시·보고**: `templates/update-pr.md`대로 `{work}/pr.md` 작성, 커밋 0건이면 게시 없이 보고, 아니면 `publish.md` 2장으로 push·PR 생성, PR 링크·요약 집계 한 줄·"머지 후 다음 세션에 반영" 보고 뒤 `rm -rf {tmp} {work}` — 실패 시에는 지우지 않고 경로와 원인 보고

### agent-wiki/references/publish.md

- **머리말**: update 스킬이 위키 원격 호스트와 주고받는 절차만 담으며, 호스트를 바꾸면 이 파일만 고친다는 문장
- **1. 열린 update PR**: `{tmp}`에서 `gh pr list --state open --json url,headRefName` — `wiki-update/` 브랜치 PR이 있으면 링크 보고 후 중단(커서가 PR 머지 전까지 기준 브랜치에 없어 같은 머지를 두 번 추출함), 명령 실패도 오류 한 줄 보고 후 중단
- **2. 게시**: `git -C {tmp} push -u origin {branch}` 후 `gh pr create --base {baseBranch} --head {branch} --title "update({domain}): {YYYY-MM-DD} 머지 {N}건 · 문서 {M}장" --body-file {work}/pr.md`, 본문이 60,000바이트를 넘으면 `추출 사실` 절을 떼어 PR 생성 후 `gh pr comment {url} --body-file`로 게시, 실패는 단계·브랜치·오류 한 줄 보고
- **3. 인증 실패**: 사용자가 `! gh auth login`을 마친 뒤 다시 실행하도록 안내

### agent-wiki/templates/update-pr.md

- **구성**: llm-wiki 템플릿의 요약·레포·추출 사실·문서·검토 방법 절 유지, 그래프 절과 커밋 링크 제거(레포 칸은 sha7과 subject — 원격 호스트마다 커밋 URL 형식이 다름)
- **보충 행**: 문서 절에 `**보충**: \`{set}\` 원소 {added}종 추가, 뜻 미확인 {unresolved}종 (F번호)`, 검토의 `fixed_sets`는 `**원본 맞춤**` 행
- **판정 표**: llm-wiki의 `기각`(검사 실패) 원천을 `검토 기각`(6장 `reject_reason`)으로 바꿈
- **검토 방법**: squash 금지(문서별 커밋 근거 유지), 전체 거절은 PR close로 커서 미반영

### agent-wiki/README.md

- **스킬 표**: `/agent-wiki:update` 행 — 명시 호출만, 지정 도메인 레포의 미처리 머지를 시간 순 묶음으로 문서에 반영해 PR로 올림, 커서 없는 레포는 시작 지점을 물음
- **요구 사항**: `gh` 인증 추가
- **로컬 사본 표**: 워크스페이스 행에 update가 clone·fetch만 하고 작업 트리는 건드리지 않는다는 사실
- **위키 구조**: `state/{slug}.json`(update 커서) 행 추가

## 커밋 분해

| # | 범위 | 검증 |
|---|---|---|
| 1 | `doc-contract.md` 4·7장 개정 | `grep -c '원본 줄\|집합 완결\|뜻 미확인\|집합 표기' agent-wiki/references/doc-contract.md`가 4 이상, 4장 예시 코드값 표 바로 위 줄이 `` 원본: 공통코드 `CR` — 일부 `` |
| 2 | `collect_update_merges.py` 신설 | 스크래치에 bare 원격과 레포 fixture 2개(도메인 A의 레포는 `OrderStatus` enum에 CANCEL·ALLOW·DELETE, `--no-ff` 머지 3건 중 마지막이 DELETE 한 줄만 수정, 도메인 B의 레포는 머지 1건)와 위키 fixture를 만들고: `--domain A` 커서 없이 실행하면 종료 20·`unset`에 A 레포만·후보 존재, 머지 3건 앞 sha를 `--start`로 재실행하면 종료 0·`commits` 3건·`batches` 1개·diff 파일 3개·B 레포 없음, fixture `state/{slug}.json`에 마지막 머지를 쓰고 재실행하면 종료 10, 커서를 HEAD 조상이 아닌 sha로 바꾸면 `skipped`에 force-push 사유, 없는 도메인은 종료 1 |
| 3 | `skills/update/SKILL.md`·`references/publish.md`·`templates/update-pr.md` 신설 | 커밋 2 fixture로 SKILL.md 1~7장을 `--domain A --dry-run`으로 따라 실행(위키 clone 원격은 fixture bare 경로로 대체): DELETE 한 줄 diff에서 나온 문서를 직접 읽어 `## 코드값` 표가 CANCEL·ALLOW·DELETE 3행이고 바로 위에 `` 원본: `OrderStatus` 전 3종 ``이며 규약 1·5장 위반 불릿이 없음, 커밋·push·PR 없음 |
| 4 | README·버전 | `python3 -c 'import json;print(json.load(open("agent-wiki/.claude-plugin/plugin.json"))["version"], json.load(open(".claude-plugin/marketplace.json"))["metadata"]["version"])'`가 `0.5.0 3.6.0`, README 스킬 표에 update 행 존재 |

## 특이 사항

- **범위 밖**: `registry.json`·`deps.json` 갱신, `add`·`audit` 스킬 이관, 공유 라이브러리 enum이 레포 밖으로 넘어가는지 판정(diff만으로 알 수 없는 문제, cmsapp-client dffa94a 사례), 전이 목록의 완결성(`## 상태와 전이`는 원본 줄 대상이 아님), 여러 도메인 일괄 실행
- **의도적 단순화**: 원본이 코드 밖인 집합은 `— 일부` 표시로 끝나며 완결되지 않음 — DB 공통코드 조회 경로가 생기면 7장 집합 완결에 그 경로를 더함
- **의도적 단순화**: 한 번도 머지로 건드려지지 않은 집합은 문서가 없음 — 부분 표가 아니라 부재이므로 오판을 만들지 않으며, 초기 적재가 필요해지면 첫 실행 시작 지점을 과거로 잡아 해소함
- **의도적 단순화**: 형식 검사 스크립트가 없어 파일명·절 순서 같은 형식 위반도 검토 에이전트 판정에 기댐 — PR 리뷰에서 형식 위반이 반복되면 그 항목만 검사하는 스크립트를 도입함
- **실행 전제**: 커밋 3의 스킬 검증은 설치된 플러그인 캐시가 아니라 작업 트리 파일을 따라 수동 실행함 — 실제 위키 원격 대상 실행은 머지 후 사용자가 `/agent-wiki:update --domain {domain} --dry-run`으로 확인
- **후속 작업**: 회사 위키(Bitbucket) 전환 시 `references/publish.md`만 Bitbucket 절차로 교체
