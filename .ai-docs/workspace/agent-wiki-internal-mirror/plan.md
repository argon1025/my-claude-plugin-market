# 사내판 agent-wiki 0.11.0 미러링

## 의도

- **왜**: 개인판 agent-wiki 0.11.0(#45, `0a9a0ed` — 비대상 세션 도메인 개요 주입, 위치 무관 위키 최신화, 로드 실패 알림 첫 줄 `위키 로드에 실패했습니다.` 통일)이 머지됐으나 사내판 `plugins/agent-wiki`는 0.10.0이라 비대상 세션에서 위키를 쓰지 못함
- **누가**: 사내판 마켓플레이스 agent-wiki 사용자, 특히 루트 README "그 밖의 레포와 `claude -p`·클라우드 세션" 경로로 user 스코프 설치한 사용자(기획자 포함)
- **완료**: 사내판 `plugins/agent-wiki`가 사내 고유 3파일(`config.json`·`references/publish.md`·`README.md`)을 뺀 전 파일에서 개인판 0.11.0과 내용이 같고, 사내판 문서·버전이 0.11.0 동작과 맞으며, 단일 커밋이 사내판 origin/master에 push된 상태

## 배경

- **저장소 위치**: 개인판 원본은 `/Users/a1000377/Desktop/Projects/onestorecorp/my-claude-plugin-market/agent-wiki`, 사내판은 `/Users/a1000377/Desktop/Projects/onestorecorp/onestore-devcenter-claude-plugin-marketplace`(master, 계획 시점 origin/master와 동기, 작업 트리 깨끗함)
- **실행 위치**: 이 계획 기록은 개인판 저장소에 있고 변경·커밋·push는 모두 사내판 저장소에서 하며, 개인판 저장소에는 구현 커밋을 만들지 않음
- **공통 본문**: 계획 시점 사내판 `hooks/session_start.py`는 개인판 0.10.0(`9ad5886`)과 바이트 단위로 같아 덮어써도 사내 수정분 손실 없음
- **내용 차이**: 계획 시점 `rsync -c` dry-run 기준 사내 고유 3파일 외 차이는 `hooks/session_start.py`, `scripts/generate_domain_overview.py`(신규), `.claude-plugin/plugin.json`(version)이며 `skills/add`·`skills/update`는 수정 시각만 다르고 사내판에만 있는 파일은 없음
- **환경 값**: `generate_domain_overview.py`는 경로를 `baseRoot` 인자로 만들고 안내 명령(`/agent-wiki:add`·`register`·`init`)이 사내판 플러그인 이름과 같아 사내판 수정 없이 동작하며, 사내 위키(`~/.onestore-llm-wiki`)로 실행하면 도메인 4개(onestore-ai, onestore-cmsapp, onestore-cmsmm, onestore-devcenter), 1,503자를 출력함
- **README 문단**: 사내판 `plugins/agent-wiki/README.md` 43행 세션 주입 문단은 개인판 변경 전 문단과 글자 단위로 같고 사내 값이 없음
- **이전 미러링**: 사내판 `e8838aa`가 같은 유형(개인판 0.10.0 미러링)으로 master에 직접 커밋됨 — `.claude-plugin/marketplace.json`, `plugins/agent-wiki/.claude-plugin/plugin.json`, `plugins/agent-wiki/README.md`, `plugins/agent-wiki/hooks/session_start.py` 4파일

## 확정 결정 (사용자 확인 2026-10-14)

- **복사 방식**: 사내 고유 3파일을 `--exclude`로 빼고 개인판 `agent-wiki/`를 rsync로 덮어씀(`--delete` 쓰지 않음)
- **고유 파일 수정**: 사내 고유 3파일 중 `README.md` 세션 주입 문단만 개인판 새 문단으로 교체하고 `config.json`·`references/publish.md`는 그대로 둠
- **버전**: agent-wiki 0.11.0(`plugin.json`은 복사로 반영, `marketplace.json` agent-wiki 항목 `version`도 0.11.0), 마켓플레이스 최상위 `version` 5.4.0 → 5.5.0
- **루트 README**: 사내판 루트 `README.md`의 22행·42행·77행 세 문장을 `## 작업`에 적은 문구로 교체
- **배포**: 사내판 master에 단일 커밋 후 `git fetch origin`으로 origin/master 이동 여부를 확인하고 `git push origin master` — 마켓플레이스 autoUpdate 사용자에게 바로 배포됨

## 선행 읽기

- `/Users/a1000377/.agent-wiki/knowledge/personal-claude-tooling/internal-plugin-mirror.md` — 사내 고유 3파일 규칙과 rsync `-c` 함정
- `/Users/a1000377/Desktop/Projects/onestorecorp/onestore-devcenter-claude-plugin-marketplace/plugins/agent-wiki/README.md` — `## 미러링` 절의 사내 고유·원본 사본 구분과 version 맞춤 규칙

## 작업

경로는 사내판 저장소 루트 기준입니다.

| 파일 | 변경 | 사다리 |
| --- | --- | --- |
| `plugins/agent-wiki/hooks/session_start.py` | 개인판 0.11.0으로 덮어씀 | 재사용 — 개인판 원본 복사 |
| `plugins/agent-wiki/scripts/generate_domain_overview.py` | 개인판 파일 신규 복사 | 재사용 — 개인판 원본 복사 |
| `plugins/agent-wiki/.claude-plugin/plugin.json` | `version` 0.11.0(복사로 반영) | 재사용 — 개인판 원본 복사 |
| `plugins/agent-wiki/README.md` | 43행 세션 주입 문단을 개인판 `agent-wiki/README.md` 41행 문단으로 교체 | 한 줄 |
| `.claude-plugin/marketplace.json` | 최상위 `version` 5.5.0, agent-wiki 항목 `version` 0.11.0 | 한 줄 |
| `README.md` | 22행·42행·77행 문장 교체 | 한 줄 |

### 공통 본문 복사

```bash
rsync -a -c --exclude config.json --exclude references/publish.md --exclude README.md \
  /Users/a1000377/Desktop/Projects/onestorecorp/my-claude-plugin-market/agent-wiki/ \
  /Users/a1000377/Desktop/Projects/onestorecorp/onestore-devcenter-claude-plugin-marketplace/plugins/agent-wiki/
```

### `README.md` (루트)

- **22행**: `네 플러그인이 각자 활성 조건을 확인해서, 관계없는 프로젝트에서는 아무것도 주입하지 않습니다.`를 `네 플러그인이 각자 활성 조건을 확인해 주입 여부와 범위를 정하며, 조건은 아래 플러그인 표에 있습니다.`로 교체
- **42행 표 활성 조건 칸**: `git 원격이 있는 레포. 등록 레포면 전체, 미등록이면 안내 한 줄`을 `세션 위치와 무관. 등록 레포면 전체, 미등록 레포·git 원격이 없는 레포·git 밖 폴더면 도메인 개요`로 교체
- **77행 끝 문장**: `미등록 레포에는 안내 한 줄만 주입됩니다.`를 `등록되지 않은 레포·git 원격이 없는 레포·git 밖 폴더에서는 위키 대상이 아님을 알리고 도메인 목록과 문서 폴더 경로만 주입합니다.`로 교체

### 커밋 메시지

```
feat(agent-wiki): 비대상 세션 도메인 개요 주입과 로드 실패 알림 통일 미러링, 0.11.0, 마켓플레이스 5.5.0

- 개인판 agent-wiki 0.11.0 session_start.py 복사와 generate_domain_overview.py 신설
- 사내 고유 README 세션 주입 문단을 개인판과 같은 문구로 교체
- 루트 README agent-wiki 활성 조건·소개 문장을 비대상 세션 도메인 개요 주입에 맞춤

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

## 커밋 분해

| # | 범위 | 검증 |
| --- | --- | --- |
| 1 | 사내판 저장소 master에 `## 작업` 표 전 파일을 한 커밋으로 남긴 뒤 `git fetch origin`에서 origin/master가 `e8838aa`에 머물러 있을 때만 `git push origin master`, 이동했으면 push하지 않고 정지 후 보고 | ① 아래 잔여 차이 명령의 `>fc` 줄이 `README.md`·`config.json`·`references/publish.md` 3건뿐임 ② 아래 훅 실행 3건이 각 기대 출력과 맞음 ③ `python3 -m json.tool .claude-plugin/marketplace.json`과 `python3 -m json.tool plugins/agent-wiki/.claude-plugin/plugin.json`이 오류 없이 끝남 ④ push 후 `git status`가 `up to date with 'origin/master'` |

잔여 차이 명령:

```bash
rsync -a -n -i -c /Users/a1000377/Desktop/Projects/onestorecorp/my-claude-plugin-market/agent-wiki/ \
  /Users/a1000377/Desktop/Projects/onestorecorp/onestore-devcenter-claude-plugin-marketplace/plugins/agent-wiki/
```

훅 실행 명령(stdin `source`를 `compact`로 주어 위키 강제 동기화를 건너뜀, 세 번째 경로는 세션 scratchpad 같은 git 밖 빈 폴더):

```bash
H=/Users/a1000377/Desktop/Projects/onestorecorp/onestore-devcenter-claude-plugin-marketplace/plugins/agent-wiki/hooks/session_start.py
echo '{"source":"compact"}' | CLAUDE_PROJECT_DIR=/Users/a1000377/Desktop/Projects/onestorecorp/onestore-devcenter-api python3 $H
echo '{"source":"compact"}' | CLAUDE_PROJECT_DIR=/Users/a1000377/Desktop/Projects/onestorecorp/my-claude-plugin-market python3 $H
echo '{"source":"compact"}' | CLAUDE_PROJECT_DIR={git 밖 폴더} python3 $H
```

- **등록 레포**: `onestore-devcenter-api`는 onestore-devcenter 도메인 등록 레포이며 `additionalContext`에 위키 규칙·레포 지도·문서 목록이 들어가고 `systemMessage` 첫 줄이 `onestore-devcenter/onestore-devcenter-api 프로젝트 위키가 로드되었습니다.`로 시작함
- **미등록 레포**: `additionalContext`가 `# 위키 — 대상 외 프로젝트(my-claude-plugin-market)`로 시작하고 `systemMessage`에 `위키 대상이 아닙니다. 도메인 개요만 로드되었습니다.`와 `/agent-wiki:register` 안내 불릿이 있음
- **git 밖 폴더**: `additionalContext`가 도메인 개요이고 `systemMessage`에 `/agent-wiki:register` 안내 불릿이 없음

## 특이 사항

- **범위 밖**: `.claude-plugin/marketplace.json`의 agent-wiki 항목 `description`은 등록 레포 기준 서술로 여전히 참이라 고치지 않음
- **권한 확인**: 사내 위키 사본(`~/.onestore-llm-wiki`)도 세션 프로젝트 밖이라 비대상 세션의 문서 grep·Read가 기본 권한 모드에서 권한 확인을 거침
- **세션 시간**: 비대상 세션도 위키 최신화로 최대 3초를 기다리므로 user 스코프 설치 사용자는 모든 세션 시작에 이 대기가 생김
- **후속 작업**: 위키 `internal-plugin-mirror` 문서에 "agent-wiki 세션 주입 동작을 바꾸는 미러링은 사내판 루트 README 활성 조건·소개 문장도 맞춤" 규칙을 `/agent-wiki:add`로 반영하도록 완료 보고에서 제안함
