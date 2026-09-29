# agent-wiki add 스킬 이관과 쓰기 스킬 공통 반영·레포 지도 갱신

## 의도

- **왜**: agent-wiki에는 코드 밖 자료(명세, 공통코드 목록, 작업 기록)와 대화에서 확정한 결정을 위키 사실로 남기는 경로가 없고, update PR의 `건너뜀`·`위치 재배정` 행은 수동 처리로 남아 있음
- **누가**: 위키 운영자나 개발자가 세션에서 자료를 건네며 `/agent-wiki:add`를 실행하고, 등록 레포에서 계획·구현·리뷰하는 에이전트가 그 문서를 읽음
- **완료**: `/agent-wiki:add`가 자료·대화 문장·update PR 행에서 사실을 뽑아 규약 1~8장대로 문서를 쓰고, 문서마다 검토 에이전트를 거친 뒤 질문 1회로 PR을 게시함. 자료가 전체를 보여 준 코드값 표만 `전 N종`이고, update PR 템플릿의 수동 문구가 add 안내로 바뀐 상태. 더해 register·update·add가 같은 규약으로 `registry.json`·`deps.json`의 책임·간선·호스트를 갱신하는 상태

## 배경

- **이관 원본**: `llm-wiki/skills/add/SKILL.md`(입력 확정 → 사실 추출 → 위치·대조 → 질문 1회 → 초안 승인 1회 → 커밋·게시 → 보고)와 `llm-wiki/references/publish.md` — 원본의 `type` 판정, `catalog.py --check`, `graph.py`, 원본 노드·간선 스키마(`kind`·`contracts`)는 가져오지 않음
- **쓰기 방식**: agent-wiki 쓰기 스킬은 `mktemp -d` 임시 clone `{tmp}`에서만 쓰며 `wiki.baseRoot`는 세션마다 원격으로 강제 정리되는 읽기 전용 사본임. config는 `${CLAUDE_PLUGIN_ROOT}/config.json`의 `wiki.remote`·`wiki.baseBranch`·`workspace.root`, git 명령은 모두 `GIT_TERMINAL_PROMPT=0`
- **update 현행**: `agent-wiki/skills/update/SKILL.md` 1~8절(준비, 범위, 추출, 배정, 반영, 검토, 커밋·커서, 게시·보고). 4~6절 프롬프트와 판정 규칙은 실제 레포 검증(onestore-cmsapp 머지 12건, 시나리오 7개)을 2회차에 통과한 상태이며 이번 공유 참조로 옮길 때 문구를 바꾸지 않는 것이 원칙
- **update 추출 제외**: 현재 update 3절 프롬프트는 "레포 지도(소관·의존)는 사실이 아니다"로 지도 관련 문장을 버림 — 이번에 지도 후보로 돌림
- **registry 형식**: 노드는 `domains.{domain}.repos.{slug}`의 7키(`remote`·`defaultBranch`·`status`·`stack`·`summary`·`responsibilities`·`hosts`), 간선은 `deps.{domain}/{slug}` 배열의 `{to, desc}` — `agent-wiki/scripts/verify_register_file.py`가 노드 하나와 그 간선 블록을 검증함(종료 1이면 오류 줄 출력)
- **지도 값 규칙 위치**: 현재 `responsibilities`(기능 단위, 헬스체크·공통 설정·빈 스텁 제외), `hosts`(자기 서빙 호스트만), `stack`(언어·주 프레임워크만), 간선의 '보고 있다' 정의(호출·구독·조회·의존, 역방향 흔적·문서 언급 제외, 대상 코드에서 실재 확인)는 `agent-wiki/skills/register/SKILL.md` 4절 에이전트 프롬프트 안에만 있음
- **세션 소비**: `agent-wiki/scripts/generate_repository_map.py`가 `responsibilities`(없으면 `summary`)와 `deps`의 그룹 키·`to`만 읽어 레포 지도를 주입함
- **세션 규칙 문구**: `agent-wiki/scripts/generate_wiki_rules.py`의 마지막 불릿이 "위키 폴더는 세션 시작마다 원격 기준으로 초기화되므로 직접 고치지 말고, 고쳐야 할 내용이 있으면 사용자에게 알리세요."임
- **실제 작업 기록**: `~/Desktop/Projects/onestorecorp/onestore-cmsapp-{api,front,external,openapi}/.devcenter/workspace/progress/{브랜치}/`에 plan·feedback 작업 기록이 있음
- **공개 저장소**: my-claude-plugin-market은 PUBLIC이므로 회사 레포 산출물·판정표 원문은 스크래치에만 두고 커밋하지 않음
- **선행 기록**: `.ai-docs/workspace/agent-wiki-update-review/plan.md`·`feedback.md`에 update 이관의 결정·재계획·검증 하네스(스크래치 bare 위키 `wiki.git`, `ws/`, `results/`, 시나리오 S1~S7)가 있음

## 확정 결정 (사용자 확인 2026-09-29)

- **구조**: "내가 넘긴 사실(문서 등 자유양식) 에 대해서 사실을 추출하여 리스트업 하고 그것을 위키에 반영했으면 함 사실 추출 까지가 update와 다른점이고 이후 문서반영은 구조 동일해도 무방할 것 같음"
- **지도 갱신 의무**: "update, add 전부 registry.json·deps.json 도 최신화를 해야하는 의무를 가져야함 항상 register 를 할 수 없기 때문 물론 책임, 의존성 등 diff 으로 인해 변경되는 사항만 대상임"
- **지도 범위**: update·add는 `responsibilities` 추가·삭제·교체, `deps` 간선(`to`·`desc`) 추가·삭제·`desc` 교체, `hosts` 환경별 추가·교체만 하고, `stack`·`summary`·`remote`·`defaultBranch`·`status`는 register 소관으로 남김
- **규칙 단일화**: "update, add 전부 그래프 갱신, register 갱신 포함임 서로 다를 이유는 없어보임" — 지도 값 규칙을 규약 한 곳에 두고 register·update·add가 모두 인용함
- **게시**: add는 사실 목록 제시·질문 1회 뒤 배정·반영·검토를 update와 같이 돌리고 `wiki-add/{YYYYMMDD-HHMM}` 브랜치 PR로 올리며 PR 머지가 초안 승인을 대신함 — `wiki-update/` 접두가 아니므로 update의 열린 PR 중단 규칙과 겹치지 않음
- **공유 절차**: 배정·반영·검토·지도 갱신·커밋 절차는 `agent-wiki/references/apply.md` 하나에 두고 update·add가 인용함
- **큰 자료**: 파일·페이지 자료는 장 단위로 나눠 장마다 추출 에이전트를 병렬 실행하고 한 실행의 목록·PR 하나로 묶으며, 붙여 넣은 텍스트와 대화 문장은 메인이 직접 추출함
- **근거 형식**: "너무 빡쎄게 제한하지말고 역추적할 수 있는 값 정도로만 가이드" — 커밋 근거는 원문을 다시 찾을 수 있는 값(파일 경로·sha, 페이지 URL, PR 링크·F번호, 자료 제목, `사용자 확인 YYYY-MM-DD`)을 예시로만 둠
- **호출 방식**: add는 모델 호출을 허용하고(`disable-model-invocation` 없음), 세션 규칙 문구에 `/agent-wiki:add` 안내를 덧붙임
- **검증**: update는 지도 갱신이 있는 실제 머지와 기존 S1·S3로 재검증하고, register·add도 실제 레포·실제 작업 기록으로 검증함
- **이관 제외 유지**: 문서 `type`, 형식 검사 스크립트, `graph.py` 없음 — 검토 에이전트가 규약 1~7장을 의미와 형식 모두 판정함("템플릿만 지켰다고 그게 통과되었다고 생각할 수 있기때문"), 스크립트는 재현성이 필요한 곳에만 둠("불필요한 스크립트는 최소화 하고싶음")

## 선행 읽기

- `agent-wiki/references/doc-contract.md` — 모든 쓰기 스킬의 판정 기준이며 스킬 프롬프트가 장 번호로 인용함, 이번에 4·8장을 고치고 9장을 신설함
- `agent-wiki/skills/update/SKILL.md` — 4~7절을 `apply.md`로 옮기는 원본이며 문구를 보존해야 함
- `agent-wiki/skills/register/SKILL.md` 4절 — 규약 9장으로 옮길 지도 값 규칙의 원본
- `.ai-docs/workspace/agent-wiki-update-review/feedback.md` — 추출 식별자 오기, 대체 규칙, 검토 판정 편차 같은 이전 검증의 교훈

## 작업

| 파일 | 변경 | 사다리 |
|---|---|---|
| `agent-wiki/references/doc-contract.md` | 4장 원본 줄 예시에 자료 추가, 8장 근거를 역추적 값 가이드로, 9장 레포 지도 신설 | 기존 파일 수정 |
| `agent-wiki/scripts/verify_register_file.py` | 머리 주석을 "register·update·add가 기록한 노드"로 고침 — 검증 로직 불변 | ② 노드·간선 검증이 이미 있음 |
| `agent-wiki/skills/register/SKILL.md` | 4절 프롬프트의 지도 값 규칙 문장을 규약 9장 인용으로 대체 | 기존 파일 수정 |
| `agent-wiki/references/apply.md` | 신설 — 배정·반영·검토·재배정·지도 갱신·커밋 공통 절차 | ② update 4~7절 문구 이동, 지도 갱신만 ⑦ — 두 스킬이 같은 규칙을 따라야 하는 사용자 결정 |
| `agent-wiki/skills/update/SKILL.md` | 3절 지도 후보 출력 추가, 4절을 정리(병합·대체·번호)로 줄이고 반영 이후를 `apply.md` 인용으로 대체 | 기존 파일 수정 |
| `agent-wiki/skills/add/SKILL.md` | 신설 — 입력 확정·추출·목록과 질문·반영 인용·게시 | ⑦ 새 스킬 |
| `agent-wiki/templates/update-pr.md` → `agent-wiki/templates/wiki-pr.md` | `git mv` 후 add 공용화, `레포 지도` 절 추가, 건너뜀·위치 재배정을 add 안내로 | 기존 파일 수정 |
| `agent-wiki/references/publish.md` | 머리말 update·add, 2장 브랜치·제목을 스킬별로, 3장 update PR 읽기 신설, 인증 실패는 4장 | 기존 파일 수정 |
| `agent-wiki/scripts/generate_wiki_rules.py` | 마지막 불릿에 `/agent-wiki:add` 제안 문구 | 기존 파일 수정 |
| `agent-wiki/README.md` | 스킬 표 add 행, update 행에 지도 갱신, 로컬 사본 표에 add·update의 clone·fetch, `gh` 요구에 add | 기존 파일 수정 |
| `agent-wiki/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | agent-wiki 0.6.0, 마켓플레이스 `metadata.version` 3.7.0 | 기존 파일 수정 |

스크립트 신설 없음 — 레포 clone·fetch는 명령 두 줄이고, 지도 파일 편집은 에이전트가 Edit으로 하며 검증은 기존 `verify_register_file.py`를 씀.

### agent-wiki/references/doc-contract.md

- **4장 원본 줄**: 괄호 예시를 "새 enum 파일, 정의 전체가 보이는 diff, 공통코드 전체 목록을 담은 자료 등"으로 넓힘 — add 자료가 전체를 보여 주는 경로
- **8장 근거**: `**근거**` 불릿을 "원문을 다시 찾을 수 있는 값 — diff 반영은 `{slug}@{sha7}`, 자료는 파일 경로(등록 레포 파일은 `{slug}@{sha7} {경로}`)·페이지 URL·PR 링크와 F번호·자료 제목처럼, 대화는 `사용자 확인 YYYY-MM-DD`"로 고치고, 사실마다 한 줄로 두되 형식은 예시일 뿐이라는 문장을 붙임
- **9장 레포 지도 신설**: 아래 불릿을 규약 문체(`**라벨**: 내용 — 이유`)로 둠
  - **편집 주체**: register는 노드 7키 전체와 자기 간선 블록, update·add는 `responsibilities`·`hosts`·자기 레포 간선만 — `stack`·`summary`·`remote`·`defaultBranch`·`status`는 register
  - **stack**: 언어·주 프레임워크만, 버전은 주 항목만, 빌드 도구·DB·개별 라이브러리 좌표 제외 (register 4절에서 이동)
  - **summary**: 이 레포가 맡는 일 한 줄 (register 4절에서 이동)
  - **responsibilities**: 이 레포를 참고해야 할 작업 단위를 기능 단위 짧은 문장으로, 헬스체크·공통 설정·빈 스텁 제외 (register 4절에서 이동)
  - **hosts**: `qa`·`stg`·`prod` 키에 이 레포 자신이 요청을 받는 호스트 리터럴만, 호출하는 API·DB·브로커·캐시 주소 제외, 못 찾은 환경은 키 생략 (register 4절에서 이동)
  - **간선**: 현재 레포의 코드·빌드·설정이 대상 레포의 API·메시지 토픽·테이블·라이브러리를 호출·구독·조회·의존하면 `{"to": "{domain}/{slug}", "desc": "대상의 무엇을 현재 레포 어디에서 쓰는지 한 줄"}` — 역방향 흔적(CORS 허용 origin 등)과 README·주석·문서의 이름 언급은 해당하지 않고, 대상 레포 코드에서 실재를 확인함 (register 4절에서 이동)
  - **변경 근거**: 추가·교체는 diff·자료·대화가 계기가 되고 코드에서 실재를 확인한 값만, 삭제는 기준 시점 코드에 사용처·기능이 남아 있지 않음을 확인한 경우만 — 자료만으로는 지도를 바꾸지 않음, 확인하지 못하면 바꾸지 않고 보고함
  - **교체**: 기존 책임 문장·`desc`는 새 코드에서 거짓일 때만 그 문장을 고치고, 표현만 다르면 두지 않음
  - **커밋**: register는 `chore(register): {slug} → {domain}`, update·add는 실행마다 한 커밋 `docs(graph): {domain} 책임 N건 · 간선 M건 · 호스트 K건`, 본문은 8장 근거 줄

### agent-wiki/skills/register/SKILL.md

- **4절 노드 프롬프트**: `stack에는 ...`, `hosts에는 ...`, `responsibilities는 ...` 세 줄을 `기준: \`sed -n '/^## 9\./,$p' {doc_contract_path}\` — stack·summary·responsibilities·hosts 규칙` 한 줄로 대체하고 JSON 스키마 줄은 유지
- **4절 간선 프롬프트**: `'보고 있다'는 ...` 두 줄을 같은 9장 인용으로 대체하고 흔적 탐색·응답 형식 줄은 유지
- **서두**: `{doc_contract_path}`는 `${CLAUDE_PLUGIN_ROOT}/references/doc-contract.md`를 전개한 절대 경로로 넘긴다는 문장 추가 — update 서두와 같은 문체

### agent-wiki/references/apply.md

머리말: update·add가 추출 뒤 공통으로 따르는 절차이며, 스킬이 `{work}/facts.json`·`{work}/graph-candidates.json`을 넘기면 1장부터 실행한다는 문장. 서브에이전트에게 규약 경로는 절대 경로로 넘김.

- **0. 입력 형식**
  - `facts.json`: `{"facts": [{"id", "fact", "topic", "code", "set", "set_total", "quote", "slug", "source", "check", "input"}]}` — `id`는 스킬이 매긴 순서 번호(update `F1`~, add `A1`~), `slug`는 사실이 다루는 레포(없으면 빈 문자열), `source`는 8장 근거 줄 목록, `check`는 코드 확인 대상 `[{"repo_path", "rev"}]`(update는 머지 sha, add는 `origin/{defaultBranch}`), `input`은 자료 원문 파일 경로 목록(update는 빈 배열), `quote`는 7장 다른 값의 변경 근거(update는 커밋 메시지·plan·feedback 원문, add는 `사용자 확인 YYYY-MM-DD 새 값 선택`)
  - `graph-candidates.json`: `{"candidates": [{"id": "G1~", "slug", "key": "responsibilities|hosts|deps", "op": "add|remove|replace", "value", "old", "code", "source", "check"}]}` — `value`는 책임 문장, `{"env", "host"}`, `{"to", "desc"}` 중 하나
  - **레포 읽기**: 코드 확인 대상 레포가 `{workspace.root}/{slug}`에 없으면 `git clone {remote} {workspace.root}/{slug}`, 있으면 `git -C {workspace.root}/{slug} fetch origin {defaultBranch}` — 작업 트리는 건드리지 않고 `rev`만 `git grep`·`git show`로 읽음, 실패한 레포는 코드 확인 없이 진행하고 보고에 남김
- **1. 배정**: update 4절의 위치·대조·신규 문서 3불릿과 `assign.json` 형식을 옮기고 사실 행 키를 0장 키로 바꿈. 병합·대체·번호 불릿은 update 정리 절에 남김
- **2. 반영**: update 5절 프롬프트를 그대로 옮기되 입력을 `{work}/assign.json`으로 둠 — 도메인 루트 신규 문서의 `## 적용 대상` 필수 문장과 코드값 원본 줄 문장 보존
- **3. 검토**: update 6절 프롬프트를 옮기고 `{근거}`를 사실 행의 `check`와 `input`으로 바꿈, 한 줄 추가 — "자료 대조: `input`이 있는 사실은 원문 파일과 대조해 원문에 없는 값·식별자를 지우고 `removed`에 `자료에 없음`으로 적는다" — 출력의 `removed`·`fixed_sets`·`edited`·`reject` 보존
- **4. 재배정**: 검토가 `위치 — {올바른 위치}`로 삭제한 사실은 그 위치로 1장 배정을 한 번 더 해 2·3장을 그 문서에만 다시 돌림, 두 번째 검토도 위치로 삭제하면 `위치 재배정` 행으로 넘김
- **5. 원복**: update 7절 첫 문단(`reject` 문서와 빈 신규 문서 원복, `검토 기각`)을 옮김
- **6. 지도 갱신**: 후보가 있는 `slug`마다 Agent 1회를 `model: sonnet`으로 한 메시지에 병렬 실행, 에이전트는 파일을 고치지 않음

  ```
  레포 {slug}의 지도 변경 후보를 코드로 확인해 적용할 변경만 남겨라.
  입력: {work}/graph-candidates.json 중 slug가 "{slug}"인 행, 현재 노드 {registry 노드 JSON}, 현재 간선 {deps 블록 JSON}, 등록 레포 {domain/slug·remote·defaultBranch·hosts 목록}.
  기준: `sed -n '/^## 9\./,$p' {doc_contract_path}`
  코드 확인: 현재 레포는 후보 check의 rev를 `git -C {repo_path} grep|show {rev}`로, 간선 대상은 0장 레포 읽기로 준비한 `{workspace.root}/{target}`의 `origin/{defaultBranch}`를 읽는다.
  판정: 후보마다 동일·추가·삭제·교체·기각 — 9장 변경 근거·교체를 적용하고 확인하지 못하면 기각 `코드 미확인`, 대상이 등록 레포가 아니면 기각 `상대 미등록`.
  금지: 파일 편집, 9장 편집 주체 밖 키 변경.
  출력: {work}/graph/{slug}.json에 Write — {"slug", "ops": [{"id", "key", "op", "value", "old", "reason"}], "rejected": [{"id", "reason"}]}
  응답은 판정별 건수만.
  ```

  메인이 `ops`를 `{tmp}/registry.json`·`{tmp}/deps.json`에 Edit으로 반영하고(해당 노드·블록 줄만, 서식 유지, 간선이 비면 키 삭제) 바꾼 slug마다 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify_register_file.py {tmp} {domain}/{slug}`가 `ok`일 때까지 고침
- **7. 커밋**: `--dry-run`이면 커밋 없이 `git -C {tmp} diff`와 집계를 보고함. 그 밖에는 update 7절의 문서별 커밋 블록(규약 8장, 근거 줄은 사실 행 `source`, 교체면 `기존 {old} / 새 {값}`)을 옮기고, 지도 변경이 있으면 이어서 `git -C {tmp} add registry.json deps.json` 후 규약 9장 `docs(graph)` 커밋 한 개

### agent-wiki/skills/update/SKILL.md

- **서두**: "이 스킬은 `registry.json`·`deps.json`을 고치지 않습니다" 문장을 "지도는 규약 9장 범위만 고칩니다"로 바꾸고 `apply.md` 경로를 더함
- **3절 추출**: 프롬프트의 `레포 지도(소관·의존)는 사실이 아니다.`를 "레포 소관·책임·서빙 호스트·레포 사이 의존을 바꾸는 diff는 사실이 아니라 `graph`에 담는다"로 바꾸고, 출력 JSON에 `"graph": [{"key", "op", "value", "old", "code", "shas"}]`를 더함 — 기준은 규약 9장 `sed` 인용
- **4절 정리**: 기존 병합·대체·번호 3불릿만 남기고, 사실마다 0장 키(`source`는 `shas`의 `{slug}@{sha7}`, `check`는 `repos[slug].path`와 가장 늦은 근거 머지, `input`은 빈 배열)로 `{work}/facts.json`을 쓰며, `graph`는 `G1`부터 번호를 매겨 `{work}/graph-candidates.json`에 씀
- **5절 반영**: `apply.md` 1~5장
- **6절 커서**: 기존 7절 커서 규칙 그대로 — 커서를 정한 뒤 커서 밖 머지에서 나온 지도 후보는 `graph-candidates.json`에서 뺌(다음 실행이 다시 추출함)
- **7절 지도·커밋**: `apply.md` 6·7장, 이어서 기존 커서 커밋
- **8절 게시·보고**: 템플릿 경로를 `templates/wiki-pr.md`로 바꿈, 그 밖은 그대로

### agent-wiki/skills/add/SKILL.md

frontmatter `name: add`, `disable-model-invocation` 없음, 영문 description은 원본 add description에서 audit 언급을 빼고 "opens a wiki PR" 취지로 씀(트리거 문구 "위키에 정리해줘", "위키에 추가", "이거 문서로 남겨줘", "정책으로 기록해줘", "건너뜀 처리" 유지, NOT for merged code). 서두는 update와 같은 문체(config, `GIT_TERMINAL_PROMPT=0`, 규약·`apply.md`·`publish.md` 경로, 서브에이전트에 절대 경로). 인자 `--domain {domain}`, `--dry-run`(`apply.md` 7장까지, 커밋·PR 없음).

- **1. 준비**: update 1절과 같이 `mktemp -d` 두 번으로 `{tmp}`·`{work}`, clone, `registry.json` 부재면 `/agent-wiki:init` 안내 후 중단. 도메인은 `--domain`, 없으면 현재 레포 `origin`이 registry 노드 `remote`와 같을 때 그 도메인, 둘 다 아니면 update 1절 질문
- **2. 입력 확정**
  - **입력 집합**: 붙여 넣은 텍스트, 읽은 파일, 가져온 페이지, 대화에서 사용자가 정한 문장, update PR(링크 또는 붙여 넣은 본문)의 `건너뜀`·`위치 재배정` 행, 작업 기록(커밋 메시지, plan, feedback — 등록 레포의 `.devcenter/workspace/progress/*/feedback.md` 같은 파일) — 이 밖의 사실 기록 금지, 에이전트의 추론은 대화 문장이 아님
  - **부재 시 질문**: 건넨 것이 없으면 무엇을 기록할지 묻고 추측하지 않음
  - **원문 보관**: 자료마다 `{work}/input/{n}.md`에 원문을 두고(붙여 넣은 텍스트·대화 문장·가져온 페이지는 Write, 파일은 경로만 기록) 8장 근거 줄 값을 정함, update PR 링크는 `publish.md` 3장으로 읽음
- **3. 추출**
  - **분담**: 붙여 넣은 텍스트·대화 문장·update PR 행은 메인이 직접, 파일·페이지 자료가 여러 장이고 합쳐 500줄을 넘으면 장마다 Agent 1회를 `model: sonnet`으로 한 메시지에 병렬 실행, 출력 파일이 없는 장은 4절 전에 다시 실행
  - **프롬프트**: 아래 블록을 SKILL.md에 둠

  ```
  자료 한 장에서 위키에 남길 사실을 추출하라.
  입력: {input 파일} {장 범위} — 근거 줄 {source}.
  기준: `sed -n '/^## 1\./,/^## 2\./p' {doc_contract_path}` — 후보 문장마다 적용한다. 화면 시안, UI 문구 원문, 일정·담당자, "검토 중"·미확정 항목도 담지 않는다.
  작업 기록: plan·feedback의 이유·버린 대안·제약·바로잡은 사실은 후보이고, 의도·범위·후속 작업·작업 현황은 1장 변경 서사로 담지 않는다.
  금지: 입력 밖 파일 열기, 사전 지식으로 채우기, 원문 절 구조 옮기기.
  set: 원소의 뜻을 말하는 사실이면 정의 식별자(심볼 또는 공통코드 그룹 이름), 규칙 문장이 코드를 인용할 뿐이면 빈 문자열.
  set_total: 자료가 그 집합의 전체 목록(공통코드 전체 표, enum 전체 정의)을 보여 주면 전 원소 수이고 원소마다 사실을 남긴다, 아니면 0.
  충돌: 같은 대상의 값이 둘이면 개정 일자·판본으로 가려 뒤의 값만 남기고 가린 근거를 conflict에 적는다. 가려지지 않으면 둘 다 남기고 conflict에 상대 사실 번호를 적는다 — 뒤쪽이 최신이라 가정하지 않는다. 복합 사실이면 충돌하는 주장만 떼어 낸다.
  graph: 레포 소관·책임·서빙 호스트·레포 사이 의존을 말하는 문장은 사실이 아니라 graph에 담는다 — 기준 `sed -n '/^## 9\./,$p' {doc_contract_path}`.
  출력: {work}/facts/{n}-{장}.json에 Write —
  {"facts": [{"fact", "topic", "code": "식별자, 없으면 빈 문자열", "slug": "사실이 다루는 등록 레포, 없으면 빈 문자열", "set", "set_total", "loc": "원문 장·절·페이지", "conflict": ""}],
   "graph": [{"slug", "key", "op", "value", "old", "loc"}]}
  응답은 사실·후보 건수만.
  ```

  - **update PR 행**: `건너뜀` 행은 사실·기존 값·출처(`{slug}@{sha7}`)를 그대로 옮기고 `check`를 그 레포와 sha로, `위치 재배정` 행은 사실과 올바른 위치를 옮김
- **4. 목록과 질문 — 정지점 하나**
  - **정리**: 같은 주장 병합, `A1`부터 번호, 사실·후보의 `slug`마다 `apply.md` 0장 레포 읽기, 이어서 `apply.md` 1장 배정을 먼저 돌려 대상 문서의 기존 값과 다른 사실을 교체 후보로 표시
  - **목록**: 메시지 본문에 `| # | 사실 | 문서 | 판정 후보 | 원문 |` 표와 지도 후보 `| # | 레포 | 변경 | 원문 |` 표를 출력
  - **질문**: 교체 후보(기존 값과 새 값, 코드로 확인되면 현재 값 병기, 옵션 `새 값`·`기존 유지`), 자료 내부 미결 충돌, update PR `건너뜀` 행(교체 후보와 같음), 위치가 갈리지 않는 사실을 AskUserQuestion으로 묻고 마지막에 `진행`·`수정`(수정 내용은 기타 입력) 한 질문 — 한 라운드 4질문까지이며 넘치면 같은 정지점에서 라운드를 잇고, 교체 외 행에는 권장안을 첫 옵션으로 둠
  - **답 반영**: `새 값`은 `quote`를 `사용자 확인 YYYY-MM-DD 새 값 선택`으로, `기존 유지`와 `모름`은 사실을 빼고 보고의 미기록 표로, 그 밖의 `모름`은 권장안 채택
  - **기록**: `apply.md` 0장 형식으로 `{work}/facts.json`·`{work}/graph-candidates.json`(`check`는 준비한 `{workspace.root}/{slug}`와 `origin/{defaultBranch}`, 등록 레포 파일 근거면 그 sha) — `--dry-run`이 아니면 `git -C {tmp} switch -c wiki-add/{YYYYMMDD-HHMM}`
- **5. 반영**: `apply.md` 1~7장 — 1장 배정은 4절 답을 반영해 다시 씀
- **6. 게시·보고**: `templates/wiki-pr.md`대로 `{work}/pr.md`, 새 커밋이 없으면 게시 없이 집계만 보고, 있으면 `publish.md` 2장으로 push·PR, PR 링크·집계 한 줄·미기록 표(`| 사실 | 위치 | 기존 값 | 새 값·사유 |` — 기존 유지 행, 자료에 없어 기록하지 못한 항목, 지도 `rejected`)·"머지 후 다음 세션에 반영"을 보고한 뒤 `rm -rf {tmp} {work}`, 실패하면 지우지 않고 경로와 원인 보고

### agent-wiki/templates/wiki-pr.md

- **공용화**: 제목을 "위키 PR 본문"으로, `레포` 절은 update만, `추출 사실` 절의 `#`은 update `F`·add `A` 번호, `출처`는 사실 행 `source`
- **레포 지도 절 신설**: `문서` 절 뒤 `## 레포 지도` — `apply.md` 6장 `ops`마다 `- **{추가|삭제|교체}**: {slug} {key} {value} (G번호)`, `rejected`마다 `- **기각**: {slug} {key} {value} — {reason} (G번호)`, 요약 집계 줄에 `지도 {g}건` 추가
- **판정 표**: `건너뜀` 사유 칸 뒤에 "머지 후 `/agent-wiki:add {PR 링크}`로 교체 여부 결정", `위치 재배정` 원천 문구의 "(agent-wiki `add` 이관 전까지 수동)"을 "`apply.md` 4장 두 번째 검토도 위치로 삭제 — 머지 후 `/agent-wiki:add {PR 링크}`로 반영"으로 바꿈, add의 `기존 유지` 행은 PR에 싣지 않고 스킬 보고로만 남김
- **검토 방법**: `**남은 행**: 건너뜀·위치 재배정 행은 머지 후 이 PR 링크를 `/agent-wiki:add`에 건네 처리` 불릿 추가

### agent-wiki/references/publish.md

- **머리말**: "update·add 스킬이 위키 원격 호스트와 주고받는 절차"
- **1장**: update 전용임을 명시, 내용 불변
- **2장**: 브랜치는 스킬이 만든 `wiki-update/`·`wiki-add/`, 제목은 update `update({domain}): {YYYY-MM-DD} 머지 {N}건 · 문서 {M}장`, add `add({domain}): {자료 대표 이름} · 문서 {M}장`
- **3장 update PR 읽기 신설**: `gh pr view {url} --json body,comments` — 본문에 "사실 원장은 첫 코멘트"가 있으면 첫 코멘트의 `추출 사실` 표를 읽음
- **4장**: 기존 3장 인증 실패

### agent-wiki/scripts/generate_wiki_rules.py

- **마지막 불릿**: "…직접 고치지 말고, 고쳐야 할 내용이 있으면 사용자에게 알리고 `/agent-wiki:add`로 반영을 제안하세요."

## 커밋 분해

| # | 범위 | 검증 |
|---|---|---|
| 1 | `doc-contract.md` 4·8·9장, `verify_register_file.py` 머리 주석 | `grep -n '^## 9\. 레포 지도' agent-wiki/references/doc-contract.md` 1줄, `grep -c '공통코드 전체 목록\|역추적\|다시 찾을 수 있는' agent-wiki/references/doc-contract.md` 2 이상, `python3 -c 'import ast;ast.parse(open("agent-wiki/scripts/verify_register_file.py").read())'` 무출력 |
| 2 | `register/SKILL.md` 9장 인용 | `grep -c "stack에는\|hosts에는\|responsibilities는\|'보고 있다'는" agent-wiki/skills/register/SKILL.md`가 0, `grep -c '## 9' agent-wiki/skills/register/SKILL.md` 2 이상 |
| 3 | `apply.md` 신설, `update/SKILL.md` 재구성, `update-pr.md` → `wiki-pr.md`, `publish.md` | `grep -rn 'update-pr.md' agent-wiki`가 0건, `apply.md`에 update 5·6절 프롬프트 본문 줄(`## 적용 대상`을 사실 행의 레포·모듈로 반드시 둔다, `위치: 2장 위치에 맞지 않는 불릿은 삭제`)이 문자 그대로 존재, 스크래치 fixture(bare 위키, 레포 2개 — A가 B의 `GET /orders` 호출을 새로 추가하는 머지와 enum 머지)로 update를 `--dry-run` 수동 실행해 `graph/{A}.json`에 간선 추가 1건, `registry.json`·`deps.json` diff에 A 간선 블록, `verify_register_file.py`가 `ok`, 문서 결과는 enum 표와 원본 줄 |
| 4 | `add/SKILL.md` 신설 | 커밋 3 fixture에서 붙여 넣은 공통코드 전체 목록(5종)과 대화 문장 1건으로 add를 `--dry-run` 수동 실행해 문서의 `## 코드값` 표가 5행이고 바로 위가 `` 원본: `{그룹}` 전 5종 ``, 대화 문장 사실의 `source`가 `사용자 확인 YYYY-MM-DD` |
| 5 | `generate_wiki_rules.py`, README, 버전 | `python3 agent-wiki/scripts/generate_wiki_rules.py d/s`의 마지막 줄에 `/agent-wiki:add`, `python3 -c 'import json;print(json.load(open("agent-wiki/.claude-plugin/plugin.json"))["version"], json.load(open(".claude-plugin/marketplace.json"))["metadata"]["version"])'`가 `0.6.0 3.7.0`, README 스킬 표에 add 행 |
| 6 | 실제 레포 검증과 불일치 수정 | 아래 검증 절 판정표의 모든 행이 규약 부합·예상 일치이거나, 불일치마다 원인 파일 수정 커밋과 해당 시나리오 재실행 결과 또는 사용자 확인된 `constraint` 항목이 있음 |
| 7 | `feedback.md` 검증 결과 기록 | `git diff --cached`에 회사 코드값·문구 원문 없음, 레포@sha와 일반화한 사실만 |

### 실제 레포 검증 (커밋 6)

- **하네스**: `.ai-docs/workspace/agent-wiki-update-review/plan.md` `추가 계획` 절의 하네스를 스크래치에 다시 만듦 — bare `wiki.git`(도메인 `onestore-cmsapp`, 레포 4개 register 7키 노드, `deps.json` `{"deps": {}}`), `--workspace` 스크래치 `ws/`, 산출물 `results/`, 시나리오마다 초기 상태에서 새로 clone
- **U1·U2 update 지도**: onestore-cmsapp-api·agent의 `git log --first-parent` 머지에서 다른 등록 레포 호출(Feign·HTTP 클라이언트·공유 테이블·client 라이브러리 새 사용)을 추가한 머지 1건과 기능(책임)을 새로 연 머지 1건을 골라 `--dry-run` — 예상: 코드로 확인된 간선 추가·책임 추가만 `ops`, 역방향 흔적·문서 언급은 기각, `verify_register_file.py` `ok`
- **U3 update 회귀**: 이전 S1(api@87c08cf44)·S3(api@e81fbcdd4~f9275fd40) 재실행 — 예상: 이전 2회차 판정과 같은 문서 결과, 지도 후보 0건 또는 기각
- **R1 register**: fixture 위키에서 onestore-cmsapp-api를 간선 대상 client·agent로 register 수동 실행(push 대신 커밋까지) — 예상: 노드 값이 9장 규칙(stack 주 항목만, hosts 서빙 호스트만, 책임 기능 단위)에 부합하고 간선이 코드로 확인된 것만
- **A1 add 전체 목록**: 공통코드 전체 표(개정일 포함)를 담은 합성 자료 — 예상: `전 N종`과 N행
- **A2 add 부분·충돌**: 일부 코드만 담고 같은 코드의 뜻이 개정일로 가려지는 두 값과 가려지지 않는 두 값을 담은 합성 자료 — 예상: `— 일부`, 개정일로 가린 값만 남음, 미결 충돌은 질문에 나옴
- **A3 add 교체**: A1 결과를 커밋한 위키에 뜻이 다른 코드 1건을 건넴 — 예상: 질문에 기존·새 값, `새 값`이면 교체와 커밋 `기존 / 새` 줄
- **A4 add 작업 기록**: onestore-cmsapp-api `.devcenter/workspace/progress/` 아래 feedback.md 2건 — 예상: 의도·범위·작업 현황 제외, 이유·제약은 규약 1·2장대로 도메인 루트 또는 레포 폴더, 식별자는 검토가 코드로 확인
- **A5 add update PR 행**: U1 산출 `pr.md`에 `건너뜀`·`위치 재배정` 행을 한 건씩 넣은 붙여 넣은 본문 — 예상: 건너뜀은 질문, 위치 재배정은 올바른 위치 문서에 반영
- **A6 add 지도 후보**: "api가 agent의 X를 호출함" 같은 문장 1건(코드 실재)과 1건(코드에 없음) — 예상: 앞 건 간선 추가, 뒤 건 기각 `코드 미확인`
- **A7 add 큰 자료**: 3장 600줄 이상 합성 자료 파일 — 예상: 장별 추출 에이전트 3개, 목록 하나
- **판정**: 산출 문서·지도 diff를 직접 끝까지 읽고 규약 1~9장 부합과 예상 일치를 `results/report.md`의 `| # | 규약 부합 | 예상 일치 | 불일치 내용 | 원인(추출·배정·반영·검토·지도·규약) | 조치 |`로 판정해 사용자에게 요약 보고함 — 스크립트 판정 없음
- **인증**: 회사 원격 clone이 인증으로 실패하면 중단하고 사용자에게 `! git ls-remote {원격}` 인증을 요청함

## 특이 사항

- **범위 밖**: audit 스킬 이관, 코드값 표 전 원소 완결(audit 몫), 실제 위키 원격 대상 실행과 PR 게시 검증(머지 후 사용자가 `/agent-wiki:add --dry-run`·`/agent-wiki:update --domain {domain} --dry-run`으로 확인), llm-wiki 플러그인 수정
- **의도적 단순화**: 지도 변경은 코드 확인이 필수라 레포가 clone되지 않거나 코드 밖 의존(외부 시스템)은 기각으로 남음 — 외부 시스템 소재는 문서 사실이 맡고, 필요해지면 9장에 외부 시스템 표기 규칙을 더함
- **의도적 단순화**: 파일·페이지 자료의 분할 기준을 500줄로 고정함 — 추출 누락이나 컨텍스트 초과가 반복되면 기준을 조정함
- **충돌 가능성**: 열린 update PR과 add PR이 같은 문서나 `deps.json` 인접 줄을 고치면 뒤에 머지하는 PR에 충돌이 남 — 스킬이 막지 않고 PR 머지 시 rebase로 해소함
- **재검증 비용**: update 4~7절 이동은 문구 보존이 원칙이나 U3 회귀로만 확인하며, 이전 7개 시나리오 전체는 다시 돌리지 않음
- **후속 작업**: 회사 위키(Bitbucket) 전환 시 `references/publish.md` 2·3장을 Bitbucket 절차로 교체
