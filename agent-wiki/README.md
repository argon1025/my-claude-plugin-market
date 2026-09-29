# agent-wiki

에이전트 위키 플러그인입니다. 위키 저장소는 `config.json`에 고정합니다.

| 스킬 | 실행 | 역할 |
| --- | --- | --- |
| `/agent-wiki:init` | 명시 호출만 | 빈 위키 저장소면 골격 생성, 로컬 위키를 clone 또는 최신화 |
| `/agent-wiki:register` | 명시 호출만 | 현재 레포를 서브에이전트로 분석해 노드·의존 간선·레포 폴더를 위키에 기록 |

## 설치

```
/plugin marketplace add argon1025/my-claude-plugin-market
/plugin install agent-wiki@my-claude-plugin-market
```

설치 후 `/agent-wiki:init`을 한 번 실행합니다. 요구 사항은 `git`, `python3`이며, `wiki.remote`에 clone·push 권한이 필요합니다.

## 설정

| 키 | 기본값 | 의미 |
| --- | --- | --- |
| `wiki.baseRoot` | `~/.agent-wiki` | 로컬 위키 경로 |
| `wiki.remote` | `https://github.com/argon1025/argon1025-llm-wiki.git` | 위키 원격 저장소 |
| `wiki.baseBranch` | `main` | 기준 브랜치 |
| `workspace.root` | `~/.agent-wiki-workspace` | 등록 레포 clone 경로(`{slug}` 폴더) |

다른 위키를 쓰려면 `config.json`만 교체합니다. `wiki.baseRoot`·`workspace.root`는 읽기 전용 사본이며 실행 때마다 원격 기준 브랜치로 덮어씁니다. 위키 기록은 스킬이 임시 clone에서 커밋·push합니다.

## 세션 주입

등록 레포에서 세션을 열면 위키 규칙, 같은 도메인 레포 지도(책임과 의존 표식), 도메인 공유·레포 전용 문서 목록, 다른 도메인 목록이 주입됩니다. 세션 시작·재개 때는 로컬 위키를 먼저 최신화하며 최대 3초 기다립니다. 위키가 없거나 미등록 레포면 안내 한 줄만 주입하고, git 원격이 없는 폴더에는 주입하지 않습니다.

## 위키 구조

```
~/.agent-wiki/
├── registry.json    # 레포 노드
├── deps.json        # 의존 간선(to·desc)
├── knowledge/       # 문서, 레포마다 {domain}/{slug}/
└── .gitignore       # .local/
```

## 등록 레포 일괄 최신화

등록 레포 전체를 `workspace.root`에 clone하고 각 원격 `defaultBranch`로 강제 정리합니다. 플러그인 폴더에서 실행하며, slug를 붙이면 그 레포만 처리합니다.

```
python3 scripts/sync_register_repositories.py ~/.agent-wiki/registry.json ~/.agent-wiki-workspace [slug ...]
```
