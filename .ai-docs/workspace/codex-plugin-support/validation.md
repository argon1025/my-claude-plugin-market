# Codex 공용 플러그인 검증 기록

2026-11-05, macOS. 개인 원본 4개 패키지·9개 스킬에 공용 지원을 적용했다. 로컬 CLI 검증과 구현은 완료했으며, 데스크톱 화면과 실제 원격 게시를 포함한 전체 E2E 완료 판정은 보류한다.

## 환경

- Codex CLI 0.166.0, 기본 모델 gpt-6.1-sol. 임시 CODEX_HOME에 로컬 마켓플레이스를 설치했다.
- Claude Code 2.1.318, 기본 모델 claude-opus-5-5. 작성 규칙 평가에는 로컬 --plugin-dir를 사용했다.
- 사용자 전역 설정과 실제 위키를 변경하지 않았다. 가상 위키·임시 Git 저장소를 사용했으며 외부 push·PR·댓글 게시를 실행하지 않았다.
- 단위 검사는 모델을 호출하지 않는다. tests/check_codex.py는 임시 설치와 실제 app-server 로더만 사용한다.

## 완료한 검사

| 검사 | 결과와 범위 |
| --- | --- |
| unittest | 14개 통과. manifest·카탈로그·9개 스킬 참조, 명시 호출 정책, 실행 파일·훅 이벤트, 공백 경로, cwd·Git 루트, 기록 길이 제한, 위키 주입·동기화 실패·타임아웃 |
| 실제 Codex 로더 | 4종 설치, 9개 스킬, SessionStart 3개·UserPromptSubmit 1개. 설치 직후 untrusted 확인. 설정에서 작성 규칙을 비활성화하면 해당 훅 2개 제거 |
| 실제 훅 신뢰·주입 | CLI /hooks에서 스크립트를 검토·신뢰한 뒤 모델이 도구 호출 없이 작성 규칙과 fixture 위키 sample 도메인을 확인 |
| 호출 정책 | 실제 모델의 암시적 스킬 목록에서 agent-wiki:add만 노출. init·register·update는 제외 |
| PR 스킬 smoke | 설치 캐시의 create와 참조 문서를 읽고 Git 저장소가 아닌 위치에서 전제조건에 따라 중단. 원격 PR 생성의 검증은 아님 |
| 계획·새 세션 실행 | 승인된 한 줄 변경 계획의 plan.md·feedback.md 저장 후 스냅샷 커밋. 그 세션에서 greeting.txt 미변경 확인. 새 세션 execute에서 hello world와 개행으로 변경, 지정 Python 검증과 feat: update greeting 로컬 커밋, clean 상태 확인 |
| Claude 패키지 | marketplace와 4개 plugin validate 통과. 각 플러그인의 선택적 아이콘 없음 경고만 발생 |
| 작성 규칙 모델 실행 | 동일 15개 입력을 각 클라이언트에서 실행, 30/30 실행 성공 및 코드 fixture 미변경. 전체 응답을 별도 JSON에 보존 |

작성 규칙 입력은 [기존 cases.json](../codex-better-communication/cases.json), 응답은 [communication-evaluation.json](communication-evaluation.json)에 있다. 수동 검토에서 실패·미검증 상태와 조건을 보존하는지 확인했으며, 30/30은 자동 품질 점수가 아니다. 상세 비교는 길이가 길고, 일부 Claude 응답은 입력 밖 정책을 제안한다. 이번 작업은 작성 규칙 내용 자체를 재설계하지 않는다.

## 확인된 클라이언트 차이

- CLI 0.166.0에서 루트 plugin.json이 있으면 스킬은 발견되지만 번들 훅이 누락됐다. 최소 재현과 .codex-plugin 단독 경로를 비교해 확인했으며, 배포에는 .claude-plugin과 .codex-plugin만 사용한다.
- 같은 CLI의 -c plugins.*.enabled=false 오버라이드는 hooks/list에서 훅을 제거하지 않았다. 임시 config.toml의 설치 설정을 실제로 비활성화한 검사와 평가를 최종 증거로 사용했다. 최초 Codex 작성 규칙 실행은 격리 불충분으로 제외하고 15개 전부 다시 실행했다.
- Codex 기본 quick_validate.py는 Claude의 disable-model-invocation 필드를 거부한다. 기존 Claude 필드를 유지하고 agents/openai.yaml 및 실제 Codex 로더로 호출 정책을 검증했다.
- 계획 fixture의 첫 workspace-write 실행은 Git index.lock 쓰기 권한 때문에 스냅샷 커밋에서 중단됐다. 구현을 진행하지 않았음을 확인한 뒤 일반 승인 절차가 있는 세션에서 스냅샷 커밋과 별도 execute를 완료했다.

## 미검증 범위와 다음 확인

- 데스크톱 실제 화면: Computer Use가 앱 접근을 차단했다. 앱에서 로컬 마켓 등록·설치, Hooks 신뢰, 9개 스킬 노출과 새 세션 주입을 직접 확인해야 한다. app-server 결과를 UI 성공으로 대체하지 않는다.
- PR create·review·fix의 실제 GitHub·Bitbucket 게시, 위키 init·register·update·add 전체 게시 흐름: 전용 테스트 저장소 주소가 필요하다. 준비되면 읽기·분석·승인 대기·승인 후 게시·오류 복구를 검증한다. 현재 테스트는 이 전체 흐름의 성공을 보장하지 않는다.
- 위임은 실제 세션에 노출된 도구에 의존한다. 설치만으로 서브에이전트 제공을 보장하지 않으며, 도구가 없으면 공통 runtime 안내에 따라 중단한다.
- Cloud·웹·Windows 셸, 업무 저장소 일괄 활성화는 이번 범위 밖이다. 원격 기본 브랜치 반영·게시도 아직 수행하지 않았다.

## 재현 명령

~~~bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tests/check_codex.py
claude plugin validate .
git diff --check
~~~

실제 모델 검증은 임시 설치 후 CLI /hooks의 신뢰 검토를 거쳐 수행한다. 테스트를 위해 신뢰 검사를 우회하거나 실제 위키를 초기화하지 않는다.
