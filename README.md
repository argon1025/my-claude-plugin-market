# my-claude-plugin-market

argon1025의 개인 Claude Code 플러그인 마켓플레이스예요.

## 설치

Claude Code에서 마켓플레이스를 등록하고 원하는 플러그인을 설치해요.

```
/plugin marketplace add argon1025/my-claude-plugin-market
/plugin install communication-rules@my-claude-plugin-market
/plugin install pull-request-workflow@my-claude-plugin-market
/plugin install dev-harness@my-claude-plugin-market
```

## 플러그인 목록

| 플러그인 | 설명 | 요구 사항 |
| --- | --- | --- |
| [communication-rules](./communication-rules/README.md) | 사용자 대면 산출물(최종 응답·PR 본문·문서) 작성 규칙을 세션 시작 시 자동 주입 | `python3` |
| [pull-request-workflow](./pull-request-workflow/README.md) | GitHub PR 생성·AI 리뷰·리뷰 코멘트 반영 스킬 3종 | `gh` CLI 설치 + 로그인(`gh auth status`) |
| [dev-harness](./dev-harness/README.md) | 프로젝트 위키·플랜 스냅샷·피드백 워크플로 규약 자동 주입 + 스킬 6종 | `python3`, 프로젝트에 `.harness/` (없으면 `/dev-harness:init`으로 생성) |

### communication-rules

최종 응답, PR 본문, 문서 파일 같은 사용자 대면 산출물에 일관된 작성 규칙을 적용해요. 세션 시작 시 실질 규칙(내용 구성)과 문체 규칙을 컨텍스트로 주입하고, 매 턴마다 핵심 규칙 리마인더를 반복해요.

### pull-request-workflow

GitHub PR 워크플로를 스킬 3종으로 지원해요. 모두 `gh` CLI 기반이라 별도 MCP 서버가 필요 없어요.

- `/pull-request-workflow:create-pull-request` — 완성된 기능 브랜치로 PR 생성 (리뷰어·본문 컨벤션 자동 파악)
- `/pull-request-workflow:review-pull-request` — 파일 단위 AI 코드 리뷰 + 반증 검증, 승인 후 코멘트 게시
- `/pull-request-workflow:resolve-review-comments` — 미해결 리뷰 코멘트 트리아지·수정·답글을 배치로 처리

### dev-harness

프로젝트 위키(`.harness/docs/`)와 브랜치 작업 기록(`.harness/workspace/`)을 중심으로 한 계획 → 실행 → 리뷰 → 문서 수확 워크플로예요. 프로젝트에 `.harness/`가 있으면 세션 시작 시 운영 규약을 자동 주입하고, 없으면 조용히 비활성화돼요.

- `/dev-harness:init` — 프로젝트에 `.harness/` 데이터 디렉토리 스캐폴딩 (멱등)
- `/dev-harness:planning` — 플랜모드 보강 (질문 커버리지·플랜 자기완결성·승인 스냅샷 커밋)
- `/dev-harness:executing-plan` — 승인된 플랜 스냅샷을 새 세션에서 실행
- `/dev-harness:walkthrough` — 브랜치 작업 인터랙티브 설명 + 리뷰 기록
- `/dev-harness:writing-docs` — 머지 브랜치 피드백을 위키로 수확
- `/dev-harness:harvest-docs` — 위키 코퍼스 주기 감사

## 라이선스

[MIT](./LICENSE)
