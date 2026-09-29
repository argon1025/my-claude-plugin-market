# agent-wiki register 이관

## 의도

- **왜**: 기존 llm-wiki register는 `graph.py` schema 출력 주입, 4레인 JSON 초안 파일, 2.5장 상호 대조, `catalog.py --check`, `references/` 장 번호 참조가 얽혀 프롬프트가 길고 고치기 어려우며, 스크립트·정규식 기반 추출은 다양한 기술 스택에서 놓치면 전부 놓치는 구조임
- **누가**: 팀원이 새 레포를 위키에 처음 올릴 때, 플러그인 관리자가 등록 절차를 고칠 때 겪음
- **완료**: `/agent-wiki:register` 한 번으로 현재 레포가 서브에이전트 탐색을 거쳐 `registry.json` 노드 7키, `deps.json` 간선(`to`·`desc`), `knowledge/{domain}/{slug}/` 폴더로 기록되어 위키 `main`에 push되며, 스킬은 init과 같은 문체로 references 참조 없이 완결됨

## 배경

- **선행 결과물**: PR #25(`0463f9b`)로 `agent-wiki/`(plugin.json `0.1.0`, config.json `wiki` 3키, `skills/init/SKILL.md`, `scripts/write_skeleton.sh`, README.md)가 main에 머지됨 — init SKILL.md가 문체 기준 예시
- **현재 위키**: `~/.llm-wiki`는 `main...origin/main`, 도메인 `personal-stock-trading` 1개, 노드 `pigeon-trade`·`pigeon-trade-dashboard` 2개(7키, remote는 `github.com/argon1025/...`처럼 scheme 없는 구형 꼴), 구형 간선 1건(`to`·`kind`·`contracts`), `knowledge/personal-stock-trading/pigeon-trade/` 레포 폴더 존재
- **공유 트리**: llm-wiki와 agent-wiki가 같은 `~/.llm-wiki`를 쓰고 llm-wiki update는 그 트리에서 `wiki-update/` 브랜치 전환·stash를 수행함
- **마켓 항목**: `.claude-plugin/marketplace.json` metadata version `3.2.0`, agent-wiki 항목 description `에이전트 위키`, 루트 `README.md` 24행 표 요구 사항 `git`

### 원점 재검토 결과

| 기존 요소 | 판정 | 근거 |
|---|---|---|
| 정본 remote 판별(upstream 우선·포크 의심·질문) | 폐지 | 현재 레포의 `origin` URL을 그대로 기록하고 워크스페이스 clone에도 그 URL을 씀 |
| remote 정규화 꼴(`host/owner/repo`) | 폐지 | clone에 바로 쓰는 URL 원형을 저장하고, 재등록 판정은 slug로 함 |
| slug 규칙 | 채택(축소) | remote 마지막 경로에서 `.git`을 뺀 소문자, remote 없는 레포 대체 규칙은 폐지 |
| 도메인 예비 판정 | 폐지 | 스키마 주입용이었으며 도메인은 초안 승인 라운드에서 한 번 고름 |
| 4레인 병렬 조사(library·http·message·responsibilities) | 재설계 | 노드 에이전트 1개 + 등록 레포마다 간선 에이전트 1개, 모두 `model: sonnet` |
| `graph.py schema` 출력 주입 | 폐지 | 응답 JSON 형식을 프롬프트에 직접 적음 |
| 관용구 판별 선행 | 채택(한 줄) | "기술 스택을 가정하지 말고 빌드·설정 파일부터 확인" 한 문장으로 다양한 스택 대응 |
| 초안 JSON 파일 쓰기 | 폐지 | 에이전트가 응답으로 반환 |
| 2.5장 상호 대조·선언 위치 위반 | 폐지 | 간선이 kind 없이 "현재 레포가 대상 레포를 보고 있는가"만 판단 |
| 대상 판정(호스트 대조·상대 clone 확인) | 재설계 | 간선 에이전트가 대상 레포의 워크스페이스 clone을 직접 읽어 실재 확인 |
| 간선 `kind`·`contracts` | 폐지 | `to`·`desc` 2키로 대체 |
| 상대 미정 보고 | 폐지 | 등록 레포만 후보이므로 미등록 상대는 찾지 않음 |
| 호스트 확인 게이트(`hosts_missing`) | 폐지 | 못 찾은 환경 키는 생략하고 초안 표에서 수정 |
| 기본 브랜치 질문 | 폐지 | 워크스페이스 clone의 현재 브랜치(원격 기본 브랜치) |
| `status` 질문·`dormant`·`--dormant` | 폐지 | 현재 레포 등록이므로 `active` 고정 |
| `--status` 상태 표 | 폐지 | 등록과 무관한 조회 기능 |
| `--resurvey` | 폐지 | 재실행이 곧 재조사이며 노드와 자기 간선 블록을 교체 |
| 도메인 이동(`git mv`·끝점 치환) | 폐지 | 이번 범위 밖으로 사용자 확정 |
| 신규 도메인 생성 | 채택 | 노드가 도메인 아래 중첩되므로 필수 |
| 필드 상한(summary 80자·책임 40자·stack 5개·`/` 금지) | 폐지 | 목표만 프롬프트에 제시, 검증은 키·타입·hosts 환경 키만 |
| `catalog.py --check`·`graph.py check` | 대체 | `scripts/check_register.py`가 현재 노드와 자기 간선 블록만 검사 |
| `references/publish.md` | 폐지 | pull·commit·push를 git 명령으로 직접 수행 |
| 커밋 메시지 `chore(register): {slug} → {domain}` | 채택 | 위키 이력 일관성 |
| 초안 표 1회 승인 | 채택 | 공유 원격 push 전 안전선 |
| 레포 폴더 `knowledge/{domain}/{slug}/` 생성 | 신규 | 사용자 요구 |
| 공통 clone 워크스페이스 | 신규 | 사용자 요구, 간선 탐색과 이후 참조에 공용 |
| 등록 레포 일괄 clone·checkout·pull | 신규(스크립트) | 사용자 요구 "일괄 지정된 경로로 clone 후 설정된 베이스 브랜치로 체크아웃 처리, 일괄 pull 하는 유틸성 스크립트", 레포 수만큼 반복되는 단순 처리 |
| 구형 간선·구형 remote 데이터 전환 | 보류 | 별도 전환 예정으로 사용자 확정 |

## 확정 결정 (사용자 확인 2026-09-29)

- **범위**: "해당 스킬은 프로젝트 분석해서 deps, register, 위키 내 폴더 생성 까지만 담당 하위호완은 고려하지 않음" — 도메인 이동 제외, llm-wiki `graph.py check`·SessionStart 훅 호환은 목표 아님
- **노드**: 기존 7키(`remote`·`defaultBranch`·`status`·`stack`·`summary`·`responsibilities`·`hosts`) 유지
- **간선**: "registry에 등록된 레포 대상으로 세부적으로 어떻게 의존하고 있는지 리스트업이 아닌 그냥 애가 너를 보고있어 정도만 판단", "어떤 작업을 할 때 이 레포를 참고해야겠네 or 먼저 이 레포에 개발이 필요하다 판단이 가능하기만 하면 됨" — 키는 `to`·`desc`, 현재 레포가 `from`인 자기 블록만 기록하고 재실행 시 그 블록을 통째로 교체
- **탐색**: 스크립트로 레포 코드를 추출하지 않고 서브에이전트가 탐색함, 노드 1개 + 등록 레포마다 간선 1개, `model: sonnet` 고정
- **후보 범위**: "별도 지침이 없으면 전체 등록 레포 조사" — 스킬 인자로 범위 지시가 오면 그 범위만
- **워크스페이스**: 간선 탐색에 대상 레포 clone을 사용하고, 경로 기본값은 `~/.llm-wiki/.local/repos`이며 config.json에서 바꿀 수 있고, 폴더 이름은 `{slug}`
- **레포 준비**: "각 레포들 clone 한 뒤 메인 브랜치로 체크아웃 해두고 pull만 땡겨서 최신화 하면 안되나? 예외 케이스 만들지말고" — 현재 레포도 워크스페이스에 clone해서 분석하며 포크 판별은 두지 않음
- **일괄 동기화**: "registry에 등록된 레포에 대해서 일괄 지정된 경로로 clone 후 설정된 베이스 브랜치로 체크아웃 처리, 일괄 pull 하는 유틸성 스크립트 정도는 지원해도될듯" — `scripts/sync_repos.py` 하나가 이 책임만 맡음
- **승인**: push 전 도메인과 초안 표를 한 라운드로 승인받음
- **JSON 수정**: 에이전트가 Edit으로 직접 수정하고 검증만 스크립트(python3)로 제공
- **필드 규칙**: 목표만 프롬프트에 제시하고 검증 스크립트는 키 존재·타입·hosts 환경 키만 검사
- **재실행**: 재조사 후 노드와 자기 간선 블록을 교체하고 기존 도메인을 유지
- **구형 데이터**: "나중에 별도 전환 예정 하위호완 신경쓰지않고 개편에 집중" — 검증은 현재 레포 노드·블록만 대상
- **브랜치**: main에서 `feat/agent-wiki-register`를 새로 분기하고 기록은 `.ai-docs/workspace/agent-wiki-register/`

## 외부 계약

### registry.json 노드

```json
{
  "domains": {
    "{domain}": {
      "description": "도메인 한 줄 설명",
      "repos": {
        "{slug}": {
          "remote": "git clone에 쓰는 URL 원형",
          "defaultBranch": "main",
          "status": "active",
          "stack": ["Java 21", "Spring Boot 3.5"],
          "summary": "이 레포가 맡는 일 한 줄",
          "responsibilities": ["이 레포를 참고해야 할 작업 단위 짧은 문장"],
          "hosts": {"prod": "api.example.com"}
        }
      }
    }
  }
}
```

- **domain**: `^[a-z0-9]+-[a-z0-9-]+$`
- **hosts**: 키는 `qa`·`stg`·`prod` 중에서만, 못 찾으면 `{}`

### deps.json 간선

```json
{
  "deps": {
    "{domain}/{slug}": [
      {"to": "{domain}/{target}", "desc": "대상의 무엇을 현재 레포 어디에서 쓰는지 한 줄"}
    ]
  }
}
```

- **방향**: 그룹 키가 현재 레포(`from`)이며 `to`를 바꾸면 `from`이 영향을 받음
- **desc 예**: `대시보드 조회 화면에서 주문·잔고 API 호출`

## 작업

| 파일 | 변경 | 사다리 |
|---|---|---|
| `agent-wiki/scripts/check_register.py` | 신규 — 인자 `{baseRoot} {domain}/{slug}`로 현재 노드와 자기 간선 블록 검증, 표준 라이브러리만 | ⑦ 사용자가 검증을 스크립트로 지정했고, JSON 문법·키·대상 실재 확인은 에이전트 육안보다 기계 검사가 확실하며 git에 대응 명령이 없음 |
| `agent-wiki/scripts/sync_repos.py` | 신규 — registry 노드마다 `{workspace.root}/{slug}`에 clone(없을 때), `defaultBranch` checkout, `pull --ff-only`, 표준 라이브러리만 | ⑦ 사용자가 스크립트로 지정했고, registry JSON 순회와 레포 수만큼의 git 반복을 한 명령으로 묶어 스킬 본문이 줄어듦 |
| `agent-wiki/config.json` | `workspace` 최상위 객체 추가(`root`: `~/.llm-wiki/.local/repos`), `wiki` 객체 유지 | ② 기존 용도별 객체 방식 그대로 |
| `agent-wiki/skills/register/SKILL.md` | 신규 — 6절(위키 최신화·레포 준비·분석·초안 승인·기록·보고) | ⑦ 사용자 명시 호출 진입점이 필요하고 절차는 git 명령과 Agent만으로 성립 |
| `agent-wiki/.claude-plugin/plugin.json` | version `0.1.0`에서 `0.2.0` | ② |
| `agent-wiki/README.md` | 스킬 표에 register 행, 설정 표에 `workspace.root` 행, 요구 사항 `git`·`python3`, 위키 구조의 `deps.json` 설명을 `의존 간선(to·desc)`로, 등록 레포 일괄 동기화 명령(`sync_repos.py`) 코드 블록 하나 | ② 기존 형식 그대로, 진행 상황·예정 기능은 적지 않음 |
| `.claude-plugin/marketplace.json` | metadata version `3.2.0`에서 `3.3.0`, agent-wiki 항목 description은 `에이전트 위키` 유지 | ② |
| `README.md` | agent-wiki 행 요구 사항 `git`을 `` `git`, `python3` ``으로 | ② |

### scripts/check_register.py

- **책임**: 검증 하나만 수행하며 수정·커밋은 하지 않음
- **검사 항목**: ① `registry.json`·`deps.json` JSON 파싱 ② `domains.{domain}.description`이 빈 값 아닌 문자열 ③ `repos.{slug}` 존재, 키가 정확히 7키 ④ `remote`·`defaultBranch`·`summary`가 빈 값 아닌 문자열, `status == "active"` ⑤ `stack`·`responsibilities`가 빈 값 없는 비어 있지 않은 문자열 배열 ⑥ `hosts`가 객체이고 키가 `qa`·`stg`·`prod` 중 하나, 값이 빈 값 아닌 문자열 ⑦ `deps.{domain}/{slug}`가 없거나 배열이며 항목 키가 정확히 `to`·`desc`, 둘 다 빈 값 아닌 문자열 ⑧ `to`가 registry에 실재하는 `{domain}/{slug}`이고 자기 자신이 아니며 중복 없음
- **범위**: 다른 노드와 다른 간선 블록은 검사하지 않음 — 구형 데이터가 남아 있어도 통과
- **출력**: 에러마다 한 줄을 stderr로 출력하고 종료 코드 1, 에러가 없으면 `ok {domain}/{slug}`와 종료 코드 0
- **분량**: 60줄 이내, 파일 머리 주석은 `write_skeleton.sh`처럼 역할·책임 경계 3줄 이내

### scripts/sync_repos.py

- **책임**: 등록 레포 동기화 하나만 수행하며 위키 트리와 registry.json은 읽기만 함
- **인자**: `sync_repos.py {baseRoot}/registry.json {workspace.root} [slug ...]` — slug를 주면 그 레포만, 없으면 모든 도메인의 모든 노드
- **동작**: 노드마다 폴더가 없으면 `git clone {remote} {root}/{slug}`, 이어서 `git -C {root}/{slug} checkout {defaultBranch}`와 `git -C {root}/{slug} pull --ff-only origin {defaultBranch}`, git은 `GIT_TERMINAL_PROMPT=0` 환경으로 실행하고 `~`는 확장함
- **출력**: 레포마다 `ok {slug}` 또는 `fail {slug} {git 에러 마지막 줄}`을 stdout에 한 줄, 실패가 있어도 나머지를 계속 처리하고 하나라도 실패하면 종료 코드 1
- **분량**: 50줄 이내, 머리 주석은 역할·책임 경계 3줄 이내

### skills/register/SKILL.md

- **frontmatter**: `name: register`, `disable-model-invocation: true`, description `Survey the current repo with subagents and record it in the wiki as a node with dependency edges.`
- **도입 3문장**: `${CLAUDE_PLUGIN_ROOT}/config.json`의 `wiki`(`baseRoot`·`remote`·`baseBranch`)와 `workspace.root`를 사용함, git 명령은 모두 `GIT_TERMINAL_PROMPT=0`을 붙여 실행함, 인자로 범위 지시가 오면 그 범위의 등록 레포만 간선 탐색함
- **문체**: 절마다 제목, 한 줄 조건, 명령·프롬프트 코드 블록, 예외 한 줄 — 굵은 라벨 불릿·근거 서술 없음, 다른 스킬은 이름(`/agent-wiki:init`)으로만 안내, references·다른 스킬 파일 참조 없음, "컨텍스트" 용어 없음
- **1. 위키 최신화**: 조건 `{baseRoot}/registry.json`이 있을 때, 명령 `git -C {baseRoot} pull --ff-only origin {baseBranch}`, 예외 `registry.json`이 없으면 `/agent-wiki:init` 안내 후 중단하고 현재 브랜치가 `baseBranch`가 아니면 전환·stash 없이 중단 후 보고
- **2. 레포 준비**: 조건 등록 레포(범위 지시가 있으면 그 slug만)와 현재 레포를 워크스페이스에 둠, slug는 현재 레포 remote 마지막 경로에서 `.git`을 뺀 소문자, 명령은 아래와 같음

  ```
  python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sync_repos.py {baseRoot}/registry.json {workspace.root} [slug ...]
  git remote get-url origin
  git clone {remote} {workspace.root}/{slug}
  git -C {workspace.root}/{slug} branch --show-current
  ```

  아래 세 줄은 현재 레포용이며 clone은 `{workspace.root}/{slug}` 폴더가 없을 때만 실행하고 마지막 명령의 결과가 `defaultBranch`임, 예외 `fail` 줄의 등록 레포는 간선 탐색에서 빼고 보고하며(현재 레포의 `fail`은 `origin` clone이 성공하면 무시) 현재 레포 clone이 실패하면 중단

- **3. 분석**: 조건 노드 에이전트 1개와 등록 레포(현재 레포 제외)마다 간선 에이전트 1개를 `model: sonnet` Agent로 한 메시지에 병렬 실행, 프롬프트 코드 블록 2개는 아래 요지를 담음
  - 노드: `{workspace.root}/{slug}`를 읽기 전용으로 분석하고 파일을 고치지 않음, 기술 스택을 가정하지 말고 빌드·설정 파일부터 확인한 뒤 전수로 읽음, 스크립트로 코드를 추출하지 않음, 응답은 `stack`(주 언어·프레임워크, 버전은 주 항목만)·`summary`(맡는 일 한 줄)·`responsibilities`(이 레포를 참고해야 할 작업 단위 짧은 문장)·`hosts`(설정·코드의 서빙 호스트 리터럴, `qa`·`stg`·`prod`, 못 찾으면 키 생략) JSON과 필드별 근거 파일 경로
  - 간선: 현재 레포 `{workspace.root}/{slug}`가 대상 레포 `{workspace.root}/{target}`(`{domain}/{target}` — summary·responsibilities·hosts 동봉)를 보고 있는지 읽기 전용으로 확인, 기술 스택을 가정하지 말고 import·의존 좌표·URL·호스트·큐·테이블·이름 등 현재 레포의 흔적을 찾고 대상 레포 코드에서 실재를 확인, 보고 있으면 `{"to", "desc"}` JSON과 근거 파일 경로, 아니면 `없음`만 응답, desc는 대상의 무엇을 현재 레포 어디에서 쓰는지 한 줄
  - 예외: 등록 레포가 없으면 간선 에이전트 없이 노드 에이전트만 실행
- **4. 초안 승인**: 조건 AskUserQuestion 한 라운드로 도메인과 `| 항목 | 초안 | 근거 |` 표(remote·defaultBranch·stack·summary·responsibilities 문장마다 한 행·hosts 환경마다 한 행·간선마다 한 행)를 확인받음, 도메인은 registry의 기존 도메인 중 선택 또는 신규 `{조직}-{도메인}`과 description 한 줄, 수정은 자유 입력, `알아서`는 초안 채택, 예외 이미 등록된 slug면 기존 도메인을 유지하고 기존 값과 초안을 함께 보임
- **5. 기록**: 조건 승인된 값으로 `registry.json`의 `domains.{domain}.repos.{slug}`를 7키로 쓰고 `deps.json`의 `deps.{domain}/{slug}` 블록을 통째로 교체(간선이 없으면 키 삭제), 신규 도메인이면 `description`과 빈 `repos`를 함께 기록, 명령은 아래와 같음

  ```
  mkdir -p {baseRoot}/knowledge/{domain}/{slug}
  touch {baseRoot}/knowledge/{domain}/{slug}/.gitkeep
  python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_register.py {baseRoot} {domain}/{slug}
  git -C {baseRoot} add registry.json deps.json knowledge/{domain}/{slug}
  git -C {baseRoot} commit -m "chore(register): {slug} → {domain}"
  git -C {baseRoot} push origin {baseBranch}
  ```

  `.gitkeep`은 폴더가 비어 있을 때만 만듦, 예외 검증이 종료 코드 1이면 출력대로 고쳐 다시 검증하고, push가 거절되면 `git -C {baseRoot} pull --rebase origin {baseBranch}` 후 한 번 더 push하며 충돌이면 `git -C {baseRoot} rebase --abort` 후 보고

- **6. 보고**: 조건 항상, 노드 요약·간선 목록(`to`·`desc`)·탐색에서 뺀 레포·`git -C {baseRoot} log -1 --oneline`
- **분량**: 코드 블록 포함 90줄 이내

### config.json

```json
{
  "wiki": {
    "baseRoot": "~/.llm-wiki",
    "remote": "https://github.com/argon1025/argon1025-llm-wiki.git",
    "baseBranch": "main"
  },
  "workspace": {
    "root": "~/.llm-wiki/.local/repos"
  }
}
```

- **경로**: init 골격의 `.gitignore`(`.local/`)가 이미 제외하므로 위키 커밋에 섞이지 않음

## 커밋 분해

승인 직후 `git switch -c feat/agent-wiki-register`로 분기하고 `plan.md`·`feedback.md` 스냅샷 커밋을 먼저 남김.

| # | 범위 | 검증 |
|---|---|---|
| 1 | `agent-wiki/scripts/check_register.py` — `feat(agent-wiki): register 검증 스크립트` | 스크래치에 픽스처를 만들어 ① 유효 노드·`to`/`desc` 블록: 종료 코드 0, 출력 `ok {domain}/{slug}` ② 노드 키 누락: 종료 코드 1, 누락 키 이름 출력 ③ `to`가 registry에 없음: 종료 코드 1 ④ `kind` 키 포함 항목: 종료 코드 1 ⑤ 다른 블록에 구형 간선(`kind`·`contracts`)만 있음: 종료 코드 0 ⑥ 깨진 JSON: 종료 코드 1, `python3 -m py_compile agent-wiki/scripts/check_register.py` 종료 코드 0 |
| 2 | `agent-wiki/scripts/sync_repos.py` — `feat(agent-wiki): 등록 레포 일괄 동기화 스크립트` | 스크래치에 `git init --bare`로 원격 2개(각 `main` 커밋 1건)를 만들고 그 경로를 remote로 둔 registry 픽스처로 ① 첫 실행: 두 폴더 clone, `ok` 2줄, 종료 코드 0 ② 원격에 커밋 추가 후 재실행: 해당 clone `git log -1`이 새 커밋 ③ clone을 다른 브랜치로 바꾼 뒤 재실행: `git branch --show-current`가 `main` ④ remote가 없는 경로인 노드 추가: 그 노드만 `fail` 줄, 나머지 `ok`, 종료 코드 1 ⑤ slug 인자 1개: 그 레포만 출력, `python3 -m py_compile` 종료 코드 0 |
| 3 | `agent-wiki/config.json`·`agent-wiki/skills/register/SKILL.md` — `feat(agent-wiki): register 스킬` | `python3 -m json.tool agent-wiki/config.json` 종료 코드 0, `claude plugin validate ./agent-wiki` 에러 0, `grep -rnE 'references/\|llm-wiki:\|컨텍스트' agent-wiki` 출력 없음, `wc -l agent-wiki/skills/register/SKILL.md` 90 이하 |
| 4 | `agent-wiki/.claude-plugin/plugin.json`·`agent-wiki/README.md`·`.claude-plugin/marketplace.json`·`README.md` — `feat: agent-wiki register v0.2.0` | `python3 -m json.tool .claude-plugin/marketplace.json` 종료 코드 0, `claude plugin validate .` 에러 0, `grep -nE '예정\|이관\|진행' agent-wiki/README.md` 출력 없음 |
| 5 | 수동 E2E(커밋 없음) | 스크래치에 `git clone --bare https://github.com/argon1025/argon1025-llm-wiki.git {스크래치}/wiki.git`, config.json을 임시로 `wiki.baseRoot={스크래치}/wiki`·`wiki.remote={스크래치}/wiki.git`·`workspace.root={스크래치}/repos`로 바꾸고 `claude --plugin-dir ./agent-wiki`로 `/agent-wiki:init` 실행, `gh repo clone argon1025/pigeon-trade`·`gh repo clone argon1025/pigeon-trade-dashboard`로 스크래치에 받은 체크아웃에서 ① pigeon-trade `/agent-wiki:register`: 기존 slug로 인식해 도메인 `personal-stock-trading` 유지, 노드 remote가 `https://github.com/argon1025/pigeon-trade.git` 원형으로 교체 ② pigeon-trade-dashboard `/agent-wiki:register`: `deps.personal-stock-trading/pigeon-trade-dashboard`가 `to: personal-stock-trading/pigeon-trade`·`desc` 2키 항목 1건으로 교체 ③ ②를 재실행해 블록 항목 수가 늘지 않음 ④ 각 실행 뒤 `git -C {스크래치}/wiki.git log --oneline -1`에 `chore(register): {slug} → personal-stock-trading`, `{스크래치}/wiki/knowledge/personal-stock-trading/pigeon-trade-dashboard/` 존재, `check_register.py` 종료 코드 0 ⑤ 검증 후 `git checkout agent-wiki/config.json`으로 원복하고 `git diff --exit-code agent-wiki/config.json` 종료 코드 0 |

## 특이 사항

- **범위 밖**: 도메인 이동, SessionStart 주입·update·add·audit 이관, llm-wiki 제거, 구형 노드 remote(scheme 없음)·구형 간선(`kind`·`contracts`) 데이터 전환
- **구형 remote**: 기존 노드의 remote가 `github.com/...` 꼴이라 워크스페이스 clone이 실패하므로 그 레포는 간선 탐색에서 빠지고 보고됨 — 해당 레포에서 register를 재실행하거나 별도 전환 시 해소
- **llm-wiki 공존**: 새 노드의 remote가 URL 원형이고 간선에 `kind`가 없어 llm-wiki `graph.py check`는 에러를, llm-wiki 세션 훅은 의존 힌트 누락을 냄 — 사용자가 하위 호환을 목표에서 제외함
- **의도적 단순화 1**: remote는 `origin` URL 원형을 그대로 기록하므로 포크 체크아웃에서 실행하면 포크 URL이, ssh 체크아웃이면 ssh URL이 기록됨 — 초안 승인 표에서 사용자가 고치며, 팀원 간 clone 실패가 반복되면 URL 정규화를 도입함
- **의도적 단순화 2**: 간선은 현재 레포가 `from`인 자기 블록만 기록하므로 다른 레포가 현재 레포를 보는 간선은 그 레포를 등록할 때만 생김
- **의도적 단순화 3**: 간선 에이전트 수가 등록 레포 수에 비례하므로 레포가 많아지면 비용·시간이 늘어남 — 인자로 범위를 지시해 줄이며, 반복 부담이 확인되면 도메인 단위 묶음을 도입함
- **워크스페이스 브랜치**: `sync_repos.py`는 워크스페이스 clone을 각 노드의 `defaultBranch`로 checkout하므로 워크스페이스 안에서 직접 작업하던 브랜치는 전환됨 — 위키 트리(`baseRoot`)는 전환하지 않으며, 워크스페이스 clone에 로컬 변경이 있어 checkout이 실패하면 `fail`로 보고함
- **README 사용법**: agent-wiki README에 `sync_repos.py` 단독 실행 명령을 코드 블록 하나로 적어 등록 레포 일괄 최신화 용도로도 쓸 수 있게 함
- **승인 후 기록**: `.ai-docs/workspace/agent-wiki-register/plan.md`에 이 계획을, `feedback.md`에 사용자 의도 `context`, 간선 단순화 `why`, 공유 트리·구형 데이터 `constraint`, 의도적 단순화 한계 `context`를 남겨 한 커밋으로 기록

## Re-plan 2026-09-29 — 워크스페이스를 위키 트리 밖으로 독립

- **폐기**: `## 확정 결정`의 워크스페이스 경로 기본값 `~/.llm-wiki/.local/repos`, `### config.json`의 `workspace.root` 값과 그 아래 `경로` 불릿(`.gitignore`의 `.local/` 제외에 기대는 근거), `## 특이 사항`의 해당 경로 언급 — 사용자 지시 "그냥 위키에 한번에 등록하지 말고 위키 경로도 바꾸자 ~/.llm-wiki ~/.llm-wiki-workspac 로 독립"
- **경로**: 위키는 `~/.llm-wiki`(`wiki.baseRoot`) 그대로, 워크스페이스 기본값은 위키 트리 밖의 `~/.llm-wiki-workspace`(`workspace.root`)이며 clone 폴더는 `~/.llm-wiki-workspace/{slug}`
- **config.json**:

  ```json
  {
    "wiki": {
      "baseRoot": "~/.llm-wiki",
      "remote": "https://github.com/argon1025/argon1025-llm-wiki.git",
      "baseBranch": "main"
    },
    "workspace": {
      "root": "~/.llm-wiki-workspace"
    }
  }
  ```

- **영향**: `sync_repos.py`는 `workspace.root`가 없으면 만들고, 위키 트리의 `.gitignore`는 바꾸지 않음 — `write_skeleton.sh`의 `.local/` 항목은 그대로 둠
- **README**: `agent-wiki/README.md` 설정 표의 `workspace.root` 기본값을 `~/.llm-wiki-workspace`로 적음

| # | 범위 | 검증 |
|---|---|---|
| 2 보강 | `sync_repos.py` | 존재하지 않는 `workspace.root`로 첫 실행 시 폴더가 생성되고 `ok` 줄 출력 |
| 3 보강 | `agent-wiki/config.json` | `python3 -c "import json;assert json.load(open('agent-wiki/config.json'))['workspace']['root']=='~/.llm-wiki-workspace'"` 종료 코드 0, `grep -rn '.local/repos' agent-wiki` 출력 없음 |
| 5 보강 | 수동 E2E | 워크스페이스를 `{스크래치}/repos`로 둔 채 실행한 뒤 `git -C {스크래치}/wiki status --porcelain` 출력 없음(위키 트리에 clone 흔적 없음) |

## Re-plan 2026-09-29 — 스크립트 이름 명시화

- **이름 변경**: `scripts/check_register.py`는 `scripts/verify_register_file.py`로, `scripts/sync_repos.py`는 `scripts/sync_register_repositories.py`로 바꾸며 책임·인자·출력은 그대로 둠 — 사용자 지시 "스크립트 명을 좀 더 명시작으로 verify-register-file? sync_register_repository.."
- **표기**: 기존 `write_skeleton.sh`의 snake_case를 따르고, 등록 레포 여러 개를 처리하므로 복수형 `repositories`를 씀
- **영향**: `skills/register/SKILL.md`·`agent-wiki/README.md`의 명령과 두 스크립트의 usage 문자열만 갱신함
