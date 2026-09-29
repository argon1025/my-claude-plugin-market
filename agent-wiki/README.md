# agent-wiki

에이전트 위키 플러그인입니다. 위키 저장소는 `config.json`에 고정합니다.

| 스킬 | 실행 | 역할 |
| --- | --- | --- |
| `/agent-wiki:init` | 명시 호출만 | 빈 위키 저장소면 골격 생성, 로컬 위키를 clone 또는 최신화 |
| `/agent-wiki:register` | 명시 호출만 | 현재 레포를 서브에이전트로 분석해 노드·의존 간선·레포 폴더를 위키에 기록 |
| `/agent-wiki:update` | 명시 호출만 | 지정 도메인 레포의 미처리 머지를 시간 순 묶음으로 문서에 반영해 위키 PR로 올림, 커서 없는 레포는 시작 지점을 물음 |

## 설치

```
/plugin marketplace add argon1025/my-claude-plugin-market
/plugin install agent-wiki@my-claude-plugin-market
```

설치 후 `/agent-wiki:init`을 한 번 실행합니다. 요구 사항은 `git`, `python3`, `gh`(update의 PR 확인·생성, `gh auth login` 인증)이며, `wiki.remote`에 clone·push 권한이 필요합니다.

## 설정

| 키 | 기본값 | 의미 |
| --- | --- | --- |
| `wiki.baseRoot` | `~/.agent-wiki` | 로컬 위키 경로 |
| `wiki.remote` | `https://github.com/argon1025/argon1025-llm-wiki.git` | 위키 원격 저장소 |
| `wiki.baseBranch` | `main` | 기준 브랜치 |
| `workspace.root` | `~/.agent-wiki-workspace` | 등록 레포 clone 경로(`{slug}` 폴더) |

다른 위키를 쓰려면 `config.json`만 교체합니다.

## 로컬 사본

| 대상 | 정책 |
| --- | --- |
| 위키 사본(`wiki.baseRoot`) | 읽기 전용이며 세션 시작(`startup`·`resume`·`clear`)과 `/agent-wiki:init` 때 원격 `baseBranch`로 초기화, 위키 기록은 스킬이 임시 clone에서 커밋·push |
| 워크스페이스(`workspace.root`) | 사용 자유, register가 분석 대상 레포를 원격 기본 브랜치로 강제 정리하므로 변경 사항은 사라질 수 있음, update는 clone·fetch만 하고 작업 트리는 건드리지 않음 |

## 세션 주입

등록 레포에서 세션을 열면 위키 규칙, 같은 도메인 레포 지도(책임과 의존 표식), 도메인 공유·레포 전용 문서 목록, 다른 도메인 목록이 주입됩니다. 세션 시작·재개·`/clear` 때는 로컬 위키를 먼저 최신화하며 최대 3초 기다립니다. 위키가 없거나 미등록 레포면 안내 한 줄만 주입하고, git 원격이 없는 폴더에는 주입하지 않습니다.

## 위키 구조

```
~/.agent-wiki/
├── registry.json    # 레포 노드
├── deps.json        # 의존 간선(to·desc)
├── knowledge/       # 문서, 레포마다 {domain}/{slug}/
├── state/           # update 커서, 레포마다 {slug}.json(cursor·at)
└── .gitignore       # .local/
```
