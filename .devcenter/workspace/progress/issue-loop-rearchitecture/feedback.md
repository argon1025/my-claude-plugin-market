# 이슈 루프 플러그인 재구성 작업 기록

- `constraint` 이 마켓에서 기존 사용자가 쓰고 있는 플러그인은 새 플러그인으로 대체하더라도 같은 작업에서 지우지 않고, 사용자들에게 공지하고 완전히 대체된 뒤에 삭제함. auto-flow 재구성에서 plan-workflow와 pr-workflow를 함께 제거하기로 했다가 공존으로 바뀜
  - source: 사용자 확인 2026-11-25
- `constraint` 역할을 나눈 봇에게 루프의 한 단계만 맡기려면 그 단계가 스킬 하나로 대응해야 함. 스킬 하나의 범위를 호출 문장으로 좁히는 방식은 봇의 역할 경계가 문장 해석에 달려, 문장이 빠지면 봇이 맡지 않은 단계까지 수행함. auto-flow를 스킬 하나로 설계했다가 단계별 스킬 넷으로 바뀜
  - source: 사용자 확인 2026-11-25
- `constraint` 사내 마켓(`onestore-devcenter-claude-plugin-marketplace`)의 agent-wiki는 위키 원격이 Bitbucket이라 `references/publish.md`를 고유 파일로 가짐. add가 PR 없이 기준 브랜치에 바로 반영하는 절차(개인판 0.16.0의 `publish.md` 3장)를 사내판에 옮길 때는 파일을 복사하지 않고 사내 `publish.md`에 같은 절차를 따로 써야 함. 사내판에는 auto-flow가 없음(2026-11-25 기준 agent-wiki 0.13.1)
  - evidence: 사내판 `plugins/agent-wiki/references/publish.md`, `.ai-docs/workspace/argon1025-agent-wiki-update-0.7.0/feedback.md`
- `constraint` auto-flow에서 환경마다 다른 값(이슈·PR·대화 도구, 관계자를 찾는 곳, 이슈 상태)은 `auto-flow/references/environment.md` 한 파일에만 두고, 스킬과 단계 문서는 그 문서의 절 번호(1 이슈, 2 PR, 3 대화, 4 관계자, 5 이슈 상태)를 가리킴. 사내판처럼 다른 배포판으로 옮길 때는 이 파일만 그 환경의 내용으로 바꾸고 절의 제목과 번호를 그대로 둬야 하며, 테스트가 이 제목을 검사함
  - source: 사용자 확인 2026-11-25
  - evidence: tests/test_plugins.py
- `constraint` auto-flow 이슈 템플릿에서 다른 실행자가 나중에 채우는 항목(미결 사항, 완료 조건, 작업 단위, 리뷰 기록)은 표로 두지 않고 목록으로 씀. 가상 실행에서 Jira 위키 문법으로 쓴 표의 빈 칸에 뒤 단계 봇이 값을 덧붙이다 칸 수가 깨진 사례가 두 이슈에서 나왔음. 표로 남긴 관련 정책과 에이전트 개선 피드백은 빈 칸을 `-`로 채움
  - evidence: 가상 실행 평가(사례 C와 D), tests/test_plugins.py
- `context` 이슈 본문에는 요청 원문을 붙이지 않고 "요청" 절에 정리해 적음. 원문을 다시 볼 곳이 없을 때만 `[auto-flow] 요청 원문` 댓글 하나로 남김. 처음에는 원문을 본문에 인용으로 남겼으나 본문을 읽기 쉽게 하려고 바꿈
  - source: 사용자 확인 2026-11-25
