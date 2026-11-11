# codex-plugin-support 작업 기록

- `context` 사용자는 개인 원본에서 구현·테스트·전체 적용 후 대상 마켓플레이스까지 이식하는 계획을 승인하고 진행을 요청했다.
  - source: 사용자 확인 2026-11-05
- `constraint` 기존 로컬 main에는 원격에 없는 계획 커밋이 있어 원격 최신에서 별도 작업 공간을 만들고 기존 로컬 브랜치를 보존한다.
- `context` 작성 규칙의 기존 평가 입력은 재사용하되 기존 Claude 실행 결과를 Codex 검증 결과로 취급하지 않는다.

- `why` Codex CLI 0.166.0에서 루트 portable manifest가 있을 때 번들 훅 목록이 비고, 루트 파일 없이 .codex-plugin/plugin.json을 쓸 때 4개 훅이 등록됨을 실제 설치와 hooks/list로 재현했다. 이번 배포는 Claude/Codex 이중 manifest를 사용한다.
- `constraint` 기본 quick_validate.py는 기존 Claude disable-model-invocation 필드를 알 수 없는 키로 거부한다. 해당 필드는 Claude 호환성을 위해 보존하고, Codex 호출 정책은 agents/openai.yaml과 실제 로더로 검증한다.
- `constraint` 데스크톱 UI 자동화는 Computer Use의 앱 접근 제한으로 차단되었다. app-server 검증을 UI 검증으로 보고하지 않는다.
- `why` 훅 비활성화 검증은 CLI -c 오버라이드가 아니라 임시 config.toml의 설치 설정을 변경해 확인했다. 오버라이드에서는 훅이 남아 작성 규칙 Codex 평가 15개를 완전히 격리한 설정으로 다시 실행했다.
- `context` 개인 원본 14개 자동 검사, 실제 로더의 9개 스킬·4개 훅, Claude manifest 검증, 양쪽 15개 작성 규칙 실행, 승인 스냅샷·새 세션 execute를 완료했다. 실행 성공과 응답 품질 판정은 구분하며 자세한 결과는 validation.md에 둔다.
- `constraint` 전용 원격 테스트 저장소가 제공되지 않아 실제 push·PR·댓글과 위키 게시 E2E는 미검증이다. 로컬 구현·이식 완료와 전체 배포 검증 완료를 구분한다.
