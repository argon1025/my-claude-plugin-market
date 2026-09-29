# agent-wiki 위키·워크스페이스 정책 단순화와 프롬프트 정리 v0.4.0

## 의도

- **왜**: 위키는 "읽기 전용, 세션 시작 때 초기화", 워크스페이스는 "사용 자유, 다른 에이전트가 건드리면 변경 사항이 사라질 수 있음"으로 정책이 단순해졌으나 register의 추가 위키 최신화, 워크스페이스 일괄 최신화 모드, "읽기 전용으로 분석하라"·"원격 기본 브랜치로 보라" 같은 옛 정책 문구가 스킬·주입 텍스트·README에 남아 있음
- **누가**: register를 실행하는 사용자, 세션 주입을 보고 다른 레포를 읽거나 고치는 작업 에이전트, register가 띄우는 분석 서브에이전트
- **완료**: 위키 사본은 세션 시작 때만 초기화되고, 워크스페이스에 대한 강제 규칙 대신 변경 유실 위험만 고지되며, 스킬·주입 텍스트·README에 새 정책과 무관하거나 중복된 지시 문장이 남지 않은 상태

## 배경

- **작업 트리 선반영**: 계획 수립 전 `main` 작업 트리에 미커밋 변경 6종(`plugin.json`, `README.md`, `hooks/session_start.py`, `scripts/generate_repository_map.py`, `scripts/sync_register_repositories.py`, `skills/register/SKILL.md`, 모두 `agent-wiki/` 아래)이 적용되어 있으며, 실행은 이를 기준선으로 아래 `## 작업`의 최종 문구로 맞춤
- **위키 사본**: `wiki.baseRoot` 기본값 `~/.agent-wiki`, 초기화 스크립트는 `agent-wiki/scripts/sync_wiki.py`이며 호출자는 세션 훅과 init 3절임
- **워크스페이스**: `workspace.root` 기본값 `~/.agent-wiki-workspace/{slug}`, 강제 정리 스크립트는 `agent-wiki/scripts/sync_register_repositories.py`이며 호출자는 register 3절뿐임
- **버전 관행**: 플러그인 변경 때마다 `agent-wiki/.claude-plugin/plugin.json` 버전과 `.claude-plugin/marketplace.json`의 `metadata.version`을 함께 올림 (직전 3.3.0에서 3.4.0)

## 확정 결정 (사용자 확인 2026-09-29)

- **위키**: "위키는 무조건 읽기 기준, 세션 시작시 초기화됨"이며, 세션 주입의 "위키는 직접 고치지 말고 사용자에게 알림"을 유지하고 위키 수정은 이후 도입할 위키 수정 스킬이 별도 임시 폴더 clone에서 수행함
- **위키 최신화 시점**: 세션 훅의 대상 `source`는 `startup`·`resume`·`clear`이고 `compact`는 제외하며, init 3절 동기화는 최초 clone을 만드는 설치 단계라 유지함
- **워크스페이스**: "워크스페이스는 뭐 쓰는건 자유 알아서 쓰세요 다른 에이전트가 건들면 변경사항 다 날라갈 수 있음 정도로 정리", 일괄 최신화는 도입하지 않음
- **금지 문구**: "무조건 베이스 브랜치로 하세요 이런 무의미한 프롬프트들은 없었으면함"
- **검증 방식**: "검증은 스크립트로 진행하지말고 직접 읽고 불필요한 프롬프트 있는지 검토하고 수정, 삭제, 재작성할것"
- **선반영 처리**: 작업 트리의 미커밋 변경을 계획 기준선으로 포함함

## 작업

| 파일 | 변경 | 사다리 |
| --- | --- | --- |
| `agent-wiki/skills/register/SKILL.md` | 임시 clone 하나로 전 과정 처리(선반영), 서두·서브에이전트 프롬프트의 중복·옛 정책 문구 삭제 | ① 삭제, ② 기존 임시 clone 절차 재배치 |
| `agent-wiki/skills/init/SKILL.md` | 서두의 중복 문장 삭제 | ① 삭제 |
| `agent-wiki/scripts/generate_wiki_rules.py` | 위키 수정 규칙에 초기화 사실 결합 | ⑥ 문자열 교체 |
| `agent-wiki/scripts/generate_repository_map.py` | 워크스페이스 안내를 유실 위험 고지로 재작성(선반영 문구 교체) | ⑥ 문자열 교체 |
| `agent-wiki/hooks/session_start.py` | 최신화 대상 `source`에 `clear` 추가(선반영) | ⑥ 한 줄 |
| `agent-wiki/scripts/sync_register_repositories.py` | 전체 레포 일괄 모드 제거(선반영), 머리 주석 교체 | ① 삭제 |
| `agent-wiki/README.md` | 정책 절 재작성, 설정 표 행 원복, 일괄 최신화 절 삭제(선반영) | ⑥ 문서 |
| `agent-wiki/.claude-plugin/plugin.json` | `0.4.0`(선반영) | ⑥ |
| `.claude-plugin/marketplace.json` | `metadata.version` `3.4.0`에서 `3.5.0` | ⑥ |

### skills/register/SKILL.md

- **서두**: 선반영 문장 "`baseRoot`는 읽기 전용 사본이므로 읽지도 고치지도 않고, registry·deps는 1절의 임시 clone `{tmp}` 파일을 뜻합니다. 6절 push 실패 외의 이유로 중단하면 `{tmp}`를 지웁니다."를 "registry·deps는 1절 임시 clone `{tmp}`의 파일입니다." 한 문장으로 교체함 — 1절이 `{tmp}`만 쓰므로 `baseRoot` 금지 문장은 불필요하고, 중단 시 임시 폴더 삭제는 남아도 해가 없음
- **1절**: `mktemp -d` 결과를 `{tmp}`로 쓰고 `git clone -b {baseBranch} {remote} {tmp}`, clone 실패나 `{tmp}/registry.json` 부재면 `/agent-wiki:init` 안내 후 중단 (선반영 유지)
- **3절**: 본문 "워크스페이스에 clone하고 원격 기본 브랜치로 강제 정리합니다"를 "워크스페이스에 원격 기본 브랜치 최신으로 준비합니다"로 교체하고, 명령은 `sync_register_repositories.py {tmp}/registry.json ...` 유지
- **4절 노드 프롬프트**: 첫 줄 "`{workspace.root}/{slug}`를 읽기 전용으로 분석하라. 파일을 고치지 말고, 스크립트로 코드를 추출하지 말라."를 "`{workspace.root}/{slug}`를 분석하라. 스크립트로 코드를 추출하지 말라."로 교체함 — 분석 에이전트에게 쓰기 금지는 불필요하며, 스크립트 추출 금지는 사용자 요구라 유지함
- **4절 간선 프롬프트**: 첫 줄 "...보고 있는지 읽기 전용으로 확인하라."에서 "읽기 전용으로 "를 삭제하고, 둘째 줄 "파일을 고치지 말고, 스크립트로 코드를 추출하지 말라. 기술 스택을 가정하지 말라."를 "스크립트로 코드를 추출하지 말라. 기술 스택을 가정하지 말라."로 교체함
- **6절**: clone 줄·`rm -rf {tmp}`·`sync_wiki.py` 줄 제거와 "1절의 `{tmp}`에 기록합니다" (선반영 유지)
- **7절**: `git -C {tmp} log -1 --oneline` 보고 뒤 `rm -rf {tmp}`, "로컬 위키 사본에는 다음 세션 시작 때 반영됩니다." (선반영 유지, 사용자 보고용 사실)
- **근거**: 위키 사본 초기화 시점을 세션 시작 하나로 두면서 최신 registry로 판단하기 위함이며, 대가는 중단되는 실행에서도 위키 전체 clone 비용이 든다는 점임

### skills/init/SKILL.md

- **서두**: 마지막 문장 "`baseRoot`는 읽기 전용 사본이며 쓰기는 임시 clone에서 합니다."를 삭제함 — 2절 명령이 임시 clone을 직접 지시하므로 중복임
- **유지**: description, 1~5절은 변경 없음

### scripts/generate_wiki_rules.py

- **규칙 3행**: "위키는 직접 고치지 말고, 고쳐야 할 내용이 있으면 사용자에게 알리세요."를 "위키 폴더는 세션 시작마다 원격 기준으로 초기화되므로 직접 고치지 말고, 고쳐야 할 내용이 있으면 사용자에게 알리세요."로 교체함

### scripts/generate_repository_map.py

`HEAD`의 셋째 문장부터 끝까지(선반영 문구 "위 경로는 읽기 전용이므로 파일을 고치거나 브랜치를 바꾸지 말고 ..."로 시작하는 두 문장)를 아래로 교체함.

```
위 경로는 자유롭게 써도 되지만 다른 에이전트가 덮어쓸 수 있어 변경 사항이 사라질 수 있습니다. 폴더가 없으면 사용자의 로컬 체크아웃을 찾거나 `{base}/registry.json`의 remote를 clone해 쓰세요.
```

### hooks/session_start.py

- **조건**: `source() in ("startup", "resume", "clear")`, 2행 주석 "새 세션(startup·resume·clear)" (선반영 유지)

### scripts/sync_register_repositories.py

- **처리 대상**: `targets = {s: nodes.get(s) for s in a.slugs}`에 `--current`가 추가되며, argparse description "나열한 slug와 --current 레포만 처리" (선반영 유지)
- **머리 주석 3행**: "# 워크스페이스는 읽기 전용 사본이므로 로컬 변경·커밋·다른 브랜치는 버린다."를 "# register 분석 기준을 맞추기 위해 로컬 변경·커밋·다른 브랜치는 버린다."로 교체함

### README.md

- **설정 표**: `workspace.root` 행 의미를 선반영 "등록 레포 읽기 전용 clone 경로(`{slug}` 폴더)"에서 원래 문구 "등록 레포 clone 경로(`{slug}` 폴더)"로 되돌림
- **정책 절**: 선반영 `## 읽기 전용 정책` 절(도입 문장, 표, 표 아래 문단)을 통째로 아래로 교체함

```
## 로컬 사본

| 대상 | 정책 |
| --- | --- |
| 위키 사본(`wiki.baseRoot`) | 읽기 전용이며 세션 시작(`startup`·`resume`·`clear`)과 `/agent-wiki:init` 때 원격 `baseBranch`로 초기화, 위키 기록은 스킬이 임시 clone에서 커밋·push |
| 워크스페이스(`workspace.root`) | 사용 자유, register가 분석 대상 레포를 원격 기본 브랜치로 강제 정리하므로 변경 사항은 사라질 수 있음 |
```

- **유지**: `## 세션 주입`의 "세션 시작·재개·`/clear` 때는" 문장과 `## 등록 레포 일괄 최신화` 절 삭제는 선반영 유지

## 커밋 분해

실행 전 `git switch -c feat/agent-wiki-readonly-policy`로 브랜치를 만들며, 계획 스냅샷 커밋이 이 브랜치의 첫 커밋임. 파일 단위 `git add {파일}`만 씀. 검증은 스크립트 실행 없이 대상 파일을 Read 도구로 끝까지 열어 읽고, 통과 조건에 맞지 않거나 새 정책과 무관·중복인 지시 문장을 발견하면 그 커밋 안에서 수정·삭제·재작성한 뒤 `feedback.md`에 근거를 남김.

| # | 범위 | 검증 |
| --- | --- | --- |
| 1 | `skills/register/SKILL.md`·`skills/init/SKILL.md` — 스킬 프롬프트 정리 | 두 파일 전문을 읽어 `baseRoot`가 register에는 없고 init에는 서두 값 목록·3절·5절에만 있음, register 두 서브에이전트 프롬프트에 `읽기 전용`·`파일을 고치지 말고`가 없고 `스크립트로 코드를 추출하지 말라`는 남음, register 1절에서 만든 `{tmp}`가 3·6·7절에서 쓰이고 7절에서만 지워짐, `sync_wiki.py`가 register에 없음 |
| 2 | `scripts/generate_wiki_rules.py`·`scripts/generate_repository_map.py`·`hooks/session_start.py` — 세션 주입 문구 | 세 파일 전문을 읽어 주입 문장 중 워크스페이스에 대해 `읽기 전용`·`기본 브랜치 기준`·`버리고`·`최신화 없이` 같은 강제 지시가 없고 유실 위험 고지 한 문장만 있음, 위키 규칙에 초기화 사실이 결합됨, 훅 조건이 `startup`·`resume`·`clear` |
| 3 | `scripts/sync_register_repositories.py`·`README.md`·`plugin.json`·`marketplace.json` — 스크립트·문서·버전 | 네 파일 전문을 읽어 스크립트에 slug 생략 시 전체 처리 경로가 없음, README에 `읽기 전용 정책`·`일괄 최신화`·`읽기 전용 clone` 문구가 없고 `## 로컬 사본` 표가 위 문구와 같음, `version` `0.4.0`·`metadata.version` `3.5.0` |
| 4 | 전체 재독 — 누락 보정 | `agent-wiki/` 아래 SKILL.md 2종·README·`scripts/generate_*.py` 3종·`hooks/session_start.py`를 다시 전문으로 읽어 1~3 이후 남은 불필요 지시 문장이 없음을 확인하고, 발견하면 고친 뒤 이 커밋에 담으며 없으면 `feedback.md` 보충만 커밋함 |

## 특이 사항

- **범위 밖**: `sync_wiki.py`·`verify_register_file.py`·`write_skeleton.sh`·`generate_document_list.py`의 동작, 레포 slug 충돌, 플러그인 설치 폴더의 `config.json` 교체 문제
- **알려진 한계**: 워크스페이스는 최신화하지 않으므로 작업 에이전트가 오래된 코드를 읽을 수 있고, register 실행 중 강제 정리가 같은 폴더를 쓰는 다른 세션의 변경을 지울 수 있음 — 사용자가 유실 위험 고지로 감수함
- **검증 한계**: 스크립트·헤드리스 실행 검증을 하지 않으므로 register 전 과정과 훅 동작은 문서·코드 정독으로만 확인됨
- **후속 작업**: 위키 수정 스킬(임시 clone에서 위키 문서 수정·push) 도입
