# agent-wiki

에이전트 위키 플러그인입니다. 위키 저장소는 `config.json`에 고정합니다.

| 스킬 | 실행 | 역할 |
| --- | --- | --- |
| `/agent-wiki:init` | 명시 호출만 | 위키 저장소를 clone 또는 최신화, 빈 저장소면 골격 생성 |

## 설치

```
/plugin marketplace add argon1025/my-claude-plugin-market
/plugin install agent-wiki@my-claude-plugin-market
```

설치 후 `/agent-wiki:init`을 한 번 실행합니다. 요구 사항은 `git`이며, `wiki.remote`에 clone·push 권한이 필요합니다.

## 설정

| 키 | 기본값 | 의미 |
| --- | --- | --- |
| `wiki.baseRoot` | `~/.llm-wiki` | 로컬 위키 경로 |
| `wiki.remote` | `https://github.com/argon1025/argon1025-llm-wiki.git` | 위키 원격 저장소 |
| `wiki.baseBranch` | `main` | 기준 브랜치 |

다른 위키를 쓰려면 `config.json`만 교체합니다.

## 위키 구조

```
~/.llm-wiki/
├── registry.json    # 레포 노드
├── deps.json        # 의존 간선
├── knowledge/       # 문서
└── .gitignore       # .local/
```
