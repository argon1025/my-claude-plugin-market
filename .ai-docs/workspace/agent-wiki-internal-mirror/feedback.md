# agent-wiki-internal-mirror 작업 기록

- `context` 개인판 agent-wiki 0.11.0(#45) 변경을 사내판 마켓플레이스 `plugins/agent-wiki`로 미러링함 — 사용자 문장 "agent-wiki 가 업데이트된 상태 사내판 미러링 반영 검토", 검토 결과 계획(사내 고유 3파일 제외 rsync, 사내 README 세션 주입 문단 교체, 루트 README 세 문장 교체, 0.11.0·마켓플레이스 5.5.0, master 단일 커밋 후 push) 승인
  - source: 사용자 확인 2026-10-14
- `constraint` 사내판 마켓플레이스 루트 `README.md`의 플러그인 표 활성 조건 칸과 agent-wiki 소개 문장은 agent-wiki 세션 주입 동작을 서술하므로, 주입 동작을 바꾸는 개인판 agent-wiki 변경을 미러링할 때 사내 고유 3파일(`config.json`·`references/publish.md`·`README.md`) 밖이어도 함께 맞춰야 함
  - evidence: onestore-devcenter-claude-plugin-marketplace/README.md
- `constraint` agent-wiki 세션 시작 훅(`hooks/session_start.py`)을 수동 실행해 검증할 때 stdin에 `{"source":"compact"}`를 주면 위키 강제 동기화(`sync_wiki.py`)를 건너뜀 — stdin이 비면 `startup`으로 간주해 위키 사본을 원격 기준으로 강제 checkout함
  - evidence: agent-wiki/hooks/session_start.py
