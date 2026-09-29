# share-context-init 작업 기록

- `context` "기존 플러그인은 불필요한 스크립트 사용으로 안내 프롬프트가 많아지고 프롬프트 복잡한 구조 순환의존성으로 수정하기 어려움 / 초기 구성, 세션주입, 문서 업데이트 각각의 use case 에서 간단한 구조와 간결한 프롬프트로 플러그인을 새로 만들고자 함 / 위키 문서 구조는 (registry.json, deps.json, knowledge) 그대로 유지하고 나머지에 대해서 진행 / 기존 위키 구현은 요구사항의 결과로써만 취급하고 재활용 인용 금지 필요성에 대해서 원점부터 재검토 / 목표는 간결한 구조, 간결한 프롬프트 에이전트가 이미 익숙한 cli 활용하도록 하고 엣지 케이스만 간단히 가이드 하는 구조로 스크립트로 단순 처리가 더 이득이 높으면 채용 가능"
  - source: 사용자 확인 2026-09-29
- `context` share-context 첫 이관 범위는 플러그인 골격과 init(위키 준비)까지이며, register·SessionStart 주입·update·add·audit 이관과 llm-wiki 제거는 이후 단계로 둠
  - source: 사용자 확인 2026-09-29
- `why` share-context는 위키 저장소를 사용자가 고르지 않고 `config.json`의 `wiki.remote`·`wiki.baseBranch`로 고정해, 기존 llm-wiki init의 clone·새로 만들기 선택 질문, 원격 없는 로컬 전용 모드, 추적 브랜치 부재로 인한 pull 실패 분기, `references/publish.md` 변형 배포 계약을 모두 없앰 — 대가는 다른 위키를 쓰려면 플러그인 변형이 `config.json`을 교체해야 한다는 점임
  - source: 사용자 확인 2026-09-29
- `constraint` my-claude-plugin-market은 PUBLIC 저장소이므로 share-context `config.json`에는 공개 위키 `https://github.com/argon1025/argon1025-llm-wiki.git`(`main`)만 두고, 사내 Bitbucket 위키 URL은 사내 플러그인이 별도로 선언함
  - source: 사용자 확인 2026-09-29
- `constraint` share-context와 llm-wiki는 같은 `~/.llm-wiki` 작업 트리를 공유하고 llm-wiki update는 그 트리에서 `wiki-update/` 브랜치 전환과 `stash`를 수행하므로, share-context 스킬은 위키 트리의 브랜치를 전환하거나 stash하지 않고 기준 브랜치가 아니면 보고만 함
  - evidence: llm-wiki/references/publish.md
- `context` share-context `config.json`은 `{"wiki": {"baseRoot", "remote", "baseBranch"}}`처럼 용도별 최상위 객체로 구성하며, 이후 단계의 설정도 같은 방식으로 객체를 추가함
  - source: 사용자 확인 2026-09-29
- `context` `feat/share-context-init` 브랜치의 계획·작업 기록은 브랜치 slug(`feat-share-context-init`)가 아닌 `.ai-docs/workspace/share-context-init/`에 있으며, 이 브랜치의 추가 기록도 같은 폴더에 덧붙임
