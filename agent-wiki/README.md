# agent-wiki

에이전트 위키 플러그인입니다. 위키 저장소는 `config.json`에 고정합니다.

| 스킬 | 실행 | 역할 |
| --- | --- | --- |
| `/agent-wiki:init` | 명시 호출만 | 위키 저장소를 clone 또는 최신화, 빈 저장소면 골격 생성 |
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
| `wiki.baseRoot` | `~/.llm-wiki` | 로컬 위키 경로 |
| `wiki.remote` | `https://github.com/argon1025/argon1025-llm-wiki.git` | 위키 원격 저장소 |
| `wiki.baseBranch` | `main` | 기준 브랜치 |
| `workspace.root` | `~/.llm-wiki-workspace` | 등록 레포 clone 경로(`{slug}` 폴더) |

다른 위키를 쓰려면 `config.json`만 교체합니다.

## 위키 구조

```
~/.llm-wiki/
├── registry.json    # 레포 노드
├── deps.json        # 의존 간선(to·desc)
├── knowledge/       # 문서, 레포마다 {domain}/{slug}/
└── .gitignore       # .local/
```

## 등록 레포 일괄 최신화

등록 레포 전체를 `workspace.root`에 clone하고 각 `defaultBranch`로 checkout·pull합니다. 플러그인 폴더에서 실행하며, slug를 붙이면 그 레포만 처리합니다.

```
python3 scripts/sync_repos.py ~/.llm-wiki/registry.json ~/.llm-wiki-workspace [slug ...]
```
