# agent-wiki

여러 레포와 팀원이 공유할 사실을 별도 git 위키 저장소에 두고 로컬에 준비하는 플러그인입니다. 위키 저장소는 사용자가 고르지 않고 `config.json`에 고정하며, 위키 문서 구조(`registry.json`·`deps.json`·`knowledge/`)는 llm-wiki와 같습니다.

| 스킬 | 실행 | 역할 |
| --- | --- | --- |
| `/agent-wiki:init` | 명시 호출만 | 위키 경로가 없으면 clone, 있으면 `pull --ff-only`, clone한 저장소가 비어 있으면 골격 작성·커밋·push |

## 설치

```
/plugin marketplace add argon1025/my-claude-plugin-market
/plugin install agent-wiki@my-claude-plugin-market
```

설치 후 새 세션에서 `/agent-wiki:init`을 한 번 실행합니다.

## 전제 조건

- **git**: 스킬은 git 명령으로 동작하며, 빈 저장소 골격 작성만 bash 스크립트 `scripts/write_skeleton.sh`가 맡음
- **원격 접근**: `wiki.remote`에 clone·push 권한이 필요하며, 인증은 비대화식으로 시도하고 실패하면 직접 실행할 명령을 안내함

## 설정

`config.json`의 `wiki` 객체가 위키 위치의 단일 정본이며, 다른 위키를 쓰는 변형 배포는 이 파일만 교체합니다.

| 키 | 기본값 | 의미 |
| --- | --- | --- |
| `wiki.baseRoot` | `~/.llm-wiki` | 로컬 위키 경로 |
| `wiki.remote` | `https://github.com/argon1025/argon1025-llm-wiki.git` | 위키 원격 저장소 |
| `wiki.baseBranch` | `main` | 동기화 기준 브랜치 |

## 특이 사항

- **공존**: llm-wiki와 같은 `~/.llm-wiki`를 공유하며, 위키 트리가 `baseBranch`가 아닌 브랜치에 있거나 `origin`이 다르면 init은 브랜치 전환·stash 없이 보고만 함
- **골격 범위**: 빈 저장소 골격은 `registry.json`·`deps.json`·`knowledge/.gitkeep`·`.gitignore`(`.local/`) 4종이며 `state/`는 두지 않고, 스크립트는 대상 파일이 하나라도 있으면 아무것도 쓰지 않음

## 이관 현황

| 기능 | 상태 |
| --- | --- |
| init(위키 준비) | 완료 |
| register(레포 등록) | 예정 |
| 세션 주입 | 예정 |
| update(문서 갱신) | 예정 |
