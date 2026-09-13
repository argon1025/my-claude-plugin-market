# feat-llm-wiki 작업 기록

- `context` 사내 devcenter-wiki는 팀 위키·Bitbucket PR 게이트·무인 파이프라인에 묶여 개인 레포에서 못 쓰고 규약 690줄과 스킬 9종의 프롬프트 과부하가 크며, 사용자 본인이 서로 무관한 여러 사이드 프로젝트를 오가며 개발할 때 세션마다 코드에 없는 지식을 다시 설명하는 비용을 겪고, 개인 마켓에 최소 기능(위키 초기화·세션 주입·무인 갱신·정리)만 가진 플러그인이 설치되어 동작하고 프롬프트가 better-communication 문체로 재작성되며 제외 기능이 기록되면 끝난다.
  - source: 사용자 확인 2026-09-14
- `context` 사용자 원문 "주로 harvest 스킬보다는, 무인 업데이트 스킬인 auto-* 스킬들을 주로 이용하는편임 이후 문서정리 스킬 사용" — llm-wiki의 주 사용 경로는 update(무인 갱신) → audit(정리)이고 add(대화형 반영)는 부차 경로다.
  - source: 사용자 확인 2026-09-14
- `context` 사용자 원문 "훅이 자동 관리, 여러 사용자(팀원) 가 공유해도 가능하도록.. 그리고 기존과 달리 지식 베이스는 플러그인 레포 내가 아니라 별도 레포지토리에서 관리되도록 구성" — llm-wiki의 위키는 플러그인 레포 밖 별도 git 저장소(원격 필수)이고 SessionStart 훅이 60분 게이트로 pull하며, 팀원 공유를 전제로 레포별 커서 파일(state/{slug}.json)을 사람 편집 파일(registry.json)과 분리한다.
  - source: 사용자 확인 2026-09-14
- `context` 사용자 확인으로 확정된 범위 — 스킬은 init·update·add·audit 4종, 기존 사내 위키 문서(그룹 172건·레포 128건) 이관은 범위 밖, 폴더는 knowledge/common + knowledge/projects/{p} 2층, 플러그인명 llm-wiki·기본 경로 ~/.ai-docs/wiki·환경변수 LLM_WIKI_ROOT, UserPromptSubmit 리마인더 훅은 제외.
  - source: 사용자 확인 2026-09-14
- `context` llm-wiki v1의 의도적 단순화 — 낡음 신호는 레포 커서 지연과 verified 180일만 쓰고 문서별 anchor·watch는 두지 않음(업그레이드 조건: 커서가 최신인데 낡은 문서가 관측될 때), 무인 갱신은 .local/paths.json에 로컬 경로가 있는 레포만 처리하고 클론·미러를 하지 않음(업그레이드 조건: 다른 머신에서 갱신이 필요할 때), 프로젝트 폴더는 평면이며 repos/{slug}/ 하위 층을 두지 않음(업그레이드 조건: 한 프로젝트의 레포 종속 문서 30건 초과), 테스트 파일을 두지 않고 픽스처 수동 검증으로 대체함(업그레이드 조건: catalog.py 두 번째 수정 시 원본 BuildContract 7개 이식).
- `why` 원본의 auto-collect→auto-publish 2단계(facts/ 원자재 대장·원장·샤드·PR 본문)를 update 한 스킬로 접은 이유는 그 분리가 팀 PR 게이트와 재소비를 위한 구조였고 개인·소규모 공유 위키에서는 게이트가 git 커밋 하나이기 때문이며, 대안이던 원자재 층 유지는 저장소 크기가 머지 수에 비례하고 스크립트 3벌을 유지해야 해 기각했다.
- `why` 모양 폴더 5종(policy/process/domain/external/adr)을 adr/만 남기고 폐지한 이유는 원본 실측 분포가 policy에 71~73% 몰려 폴더가 검색 신호 구실을 못 했고 기존 문서 이관이 범위 밖이라 호환 부담이 없기 때문이다.
- `constraint` 로컬 위키 검증(onestore-devcenter-front .devcenter/knowledge 128문서 2,971주장)에서 주장의 67%는 코드 grep 1~2회로 복원 가능했으나 ADR 기각 대안 58불릿·코드에 흔적 없는 외부 계약·자기 불확실성 표기·비강제 컨벤션·반파리티 경고 33%는 코드로 대체 불가하므로, llm-wiki 규약은 레포 종속 사실의 자리를 없애지 않고 description에 레포명을 넣어 프로젝트 폴더에 둔다.
- `constraint` 같은 검증에서 최근 17커밋 미수확으로 문서 6건이 코드와 불일치하고 그중 1건은 verified 날짜가 최신인데 문서 전체가 낡아 있었으므로, llm-wiki의 낡음 신호는 verified 날짜만으로는 부족하고 레포 커서와 HEAD 거리를 세션 헤더에 표시해야 한다.
- `why` llm-wiki의 머지 diff 머리말이 머지 커밋 메시지가 아니라 `git log {sha}^1..{sha}`로 딸린 커밋 메시지 전부(상한 20건)를 싣는 이유는 PR 머지 커밋의 메시지가 "Merged in {branch} (pull request #N)" 한 줄이라 결정 근거가 어디에도 남지 않기 때문이며, 원본 collect.py는 subject만 실어 이 손실이 있었다.
  - evidence: llm-wiki/scripts/update.py extract_diff
- `context` llm-wiki 실측 규모는 catalog.py 403줄·update.py 311줄·session_start.sh 180줄로 계획의 목표치(180·140·60)를 넘지만 사양은 그대로 충족했으며, 차이는 주석과 독스트링이고 원본 대비 감축(catalog 1,002줄, 스크립트 4,569줄)은 유지된다.
