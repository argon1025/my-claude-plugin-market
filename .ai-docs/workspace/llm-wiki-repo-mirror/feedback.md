# llm-wiki-repo-mirror 작업 기록

- `context` 레포 경로 파일에 문제가 있는 것이 아닌지, 워크트리를 많이 써서 계속 재발할 것 같으니 기존 레포 경로를 재활용하지 말고 위키용으로 별도 경로에 프로젝트를 받아 유지하면 paths.json도 유지할 필요가 없음 — llm-wiki update·audit은 `{WIKI_ROOT}/.local/mirrors/{slug}.git` bare 미러만 읽고 `.local/paths.json`은 제거함
  - source: 사용자 확인 2026-09-26
- `context` 개발 세션에서 에이전트가 다른 레포 코드를 읽을 때도 미러로 통일하며, 기본 브랜치에 병합된 코드만 보이고 작업 중인 로컬 변경은 보이지 않는 한계를 수용함 — 업그레이드 조건은 병합 전 브랜치를 타 레포 기준으로 대조해야 하는 요청이 반복될 때 `mirror --ref` 도입
  - source: 사용자 확인 2026-09-26
- `constraint` `git clone --bare`는 fetch refspec을 두지 않아 이후 `git fetch origin`이 FETCH_HEAD만 갱신하고 브랜치 ref는 낡으므로, llm-wiki 미러는 `remote.origin.fetch=+refs/heads/*:refs/heads/*`를 매번 설정한 뒤 fetch해야 함
- `why` llm-wiki 미러를 `git clone --mirror`가 아니라 `--bare`와 heads 전용 refspec으로 만드는 이유는 `--mirror`가 GitHub의 `refs/pull/*`까지 받아 무거워지기 때문이며, `--filter=blob:none` 부분 clone은 `git grep {rev}`가 blob을 지연 다운로드해 느려지므로 쓰지 않음
- `correction` `.local/paths.json`은 세션을 연 git toplevel로 덮어써지므로 워크트리(예: `/Users/rok/orca/workspaces/pigeon-trade/issue-5`)에서 세션을 연 뒤 워크트리를 지우면 로컬 사본이 있어도 update가 `로컬 경로 없음`으로 건너뜀 — 경로 기록 방식 자체가 재발 원인임
  - evidence: llm-wiki/hooks/session_start.sh, llm-wiki/scripts/update.py
- `constraint` llm-wiki `update.py`의 `extract_diff`가 쓰는 `-- .` pathspec과 `:(exclude)` 제외 규칙은 bare 미러에서도 그대로 동작하므로 `-- :/`로 바꿀 필요가 없음 — pigeon-trade 머지 b292dfa 추출에서 14개 파일 diff로 확인함
  - evidence: llm-wiki/scripts/update.py
