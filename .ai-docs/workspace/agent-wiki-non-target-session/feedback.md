# agent-wiki-non-target-session 작업 기록

- `context` agent-wiki 세션 시작 훅을 위키 대상이 아닌 세션에서도 상태를 알리고 도메인 개요를 주입하도록 개선함 — 사용자 문장 "플러그인을 user 스코프로 전역 설치하여 사용하는 사용자가 많아지면서 위키 범위가 아닌 세션에서는 세션 스타트 훅도 보이지 않거나 로드가 되지 않는 문제가 있음", "완전 주입 안하기 보다 먼저 해당 세션에서 시작된 프로젝트는 지원 대상이 아님을 전달하고 이러이러한 도메인이 있으니 혹시 사용자가 질문하면 문서 참고할 수 있다는 형태로 제공", "개발자가 아니라 기획자도 해당 플러그인을 사용함", 구현 전에 "각 케이스별로 어떻게 뜰것인지 예상 결과물을 나에게 공유해서 확인받고 진행"
  - source: 사용자 확인 2026-10-14
- `context` agent-wiki 세션 시작 훅은 git 밖 폴더·origin 없는 레포·미등록 레포를 하나의 비대상 템플릿으로 합쳐 알림과 도메인 개요(도메인 이름·description과 도메인 색인 경로)를 주고, `/agent-wiki:register` 안내는 origin이 있는 미등록 레포 알림에 한 줄로만 붙이며, 비대상 세션에서도 위키 최신화(최대 3초 대기)를 수행함 — 사용자 문장 "권장안대로 진행하고 케이스별 예상 결과물 보여줘"
  - source: 사용자 확인 2026-10-14
- `context` agent-wiki 로드 알림의 첫 줄은 등록 레포 로드·비대상 개요 로드·실패 세 가지만 두고, 실패(위키 미구성·등록 도메인 0개·주입 생성 전체 실패·훅 예외)는 모두 "위키 로드에 실패했습니다" 한 줄 아래 원인·조치 불릿을 붙이며 주입은 하지 않고, 최신화 실패·한도 초과·일부 생성 실패처럼 주입이 남는 경우는 로드 문구에 경고 불릿을 붙임 — 사용자 문장 "그냥 위키 로드에 실패했습니다 를 메인 문구로 두고 각 케이스별로 불릿을 추가하는 형태면 코드도 간단해지지 않을지?"
  - source: 사용자 확인 2026-10-14
- `why` agent-wiki 비대상 세션(git 밖·origin 없음·미등록)의 문서 탐색은 도메인 색인 파일을 만들지 않고 에이전트가 도메인 문서 폴더를 `^description:`으로 grep하게 함 — 문서 frontmatter가 곧 색인이라 색인 파일 쓰기·생성 실패 경고·도메인 수에 비례한 훅 시간이 없고, 에이전트 도구 호출 수는 색인 파일 한 번 읽기와 같음, 레포 책임은 `registry.json`에서 읽음
- `why` agent-wiki 비대상 세션 주입은 신규 생성기 `generate_domain_overview.py` 하나가 전부 출력하고 기존 생성기 3종(`generate_wiki_rules.py`·`generate_repository_map.py`·`generate_document_list.py`)에 모드를 더하지 않음 — 위키 수정 금지 등 규칙 문장 2줄과 도메인 행 형식이 중복되지만 등록·비대상 경로가 파일 단위로 갈려 각 생성기에 인자별 분기가 생기지 않음
- `context` 비대상 세션 문서 탐색을 grep에 맡기는 것은 의도적 단순화임 — 도메인 description 한 줄만으로 질문에 맞는 도메인을 고르기 어려운 사례가 쌓이면 도메인 행에 레포 이름을 더하거나 도메인 색인 파일(`{baseRoot}/.local/index/{domain}.md`) 생성으로 올림
- `context` agent-wiki 비대상 세션 개선의 사내판 미러링은 이 작업 범위에서 빼고 별도 이슈로 진행함 — 사용자 문장 "일단 사내판 미러링은 별도 이슈로 진행할 예정"
  - source: 사용자 확인 2026-10-14
- `constraint` agent-wiki add 스킬은 현재 레포 origin이 registry에 없으면 반영할 도메인을 AskUserQuestion으로 고르므로, 비대상 세션 주입에서 `/agent-wiki:add` 반영 제안이 유효함
  - evidence: agent-wiki/skills/add/SKILL.md
- `constraint` agent-wiki 세션 시작 훅을 생성기가 실패하도록 바꾼 플러그인 복사본으로 등록 레포에서 검증할 때 `config.json`의 `wiki.baseRoot`가 실제 위키(`~/.agent-wiki`)를 가리키면 훅이 제목 한 줄뿐인 색인을 실제 `{baseRoot}/.local/index/{domain}/{slug}.md`에 덮어써 그 레포의 다른 세션이 다음 세션 시작 전까지 빈 색인을 읽으므로, `baseRoot`를 위키 복사본으로 바꿔 돌려야 함
  - evidence: agent-wiki/hooks/session_start.py
