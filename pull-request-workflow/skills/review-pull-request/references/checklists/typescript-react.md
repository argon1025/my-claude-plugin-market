# pr-review Layer 1 체크리스트 — TypeScript/React (Next.js 포함)

- common.md에 더해 적용. Layer 2(프로젝트 문서)가 같은 주제를 다루면 Layer 2 우선
- 전 항목 공통: 보고 조건 충족 AND 미보고 조건 미해당일 때만 보고

## 결함

### 타입 탈출
- 보고 조건: `as any`·`@ts-ignore`·사유 주석 없는 `@ts-expect-error`·non-null `!`·외부 데이터(JSON.parse, 브라우저 입력) 무검증 `as` 리터럴 단언
- 미보고 조건: 수용 지점 1곳 격리 후 타입 복원된 라이브러리 any, 테스트 fixture 단언, 자사 내부 백엔드 응답 타입 신뢰(zod 미적용이 정책)
- 등급 가이드: 무검증 단언이 런타임 오류 경로면 Bug(핵심 흐름 크래시·기존 소비처 파손이면 Blocker), 동작은 정상이고 타입 안전성만 훼손이면 개선

### Hooks stale closure
- 보고 조건: useEffect/useCallback/useMemo deps 누락·오기재로 오래된 값 참조가 실동작 버그로 이어지는 경우
- 미보고 조건: 의도가 명백한 mount-only(deps `[]`), 참조 값이 실질 불변
- 등급 가이드: Bug — 사용자 데이터가 잘못 저장·전송되는 경로면 Blocker

### 렌더 중 사이드이펙트
- 보고 조건: 컴포넌트 본문(렌더 경로)에서 상태 변경·구독·스토리지/네트워크 I/O 실행
- 미보고 조건: 이벤트 핸들러·useEffect 내부 실행
- 등급 가이드: Bug

### 컴포넌트 내부 컴포넌트 선언
- 보고 조건: 컴포넌트 함수 본문 안에서 다른 컴포넌트 정의 — 렌더마다 재마운트·상태 소실
- 미보고 조건: 모듈 레벨 선언, 컴포넌트가 아닌 JSX 조각 변수
- 등급 가이드: Bug

### XSS·위험 실행
- 보고 조건: dangerouslySetInnerHTML·innerHTML·eval·new Function에 미검증 외부 입력, 미검증 URL의 href/src/라우터 이동 사용(`javascript:` 스킴 등)
- 미보고 조건: 정적 문자열, 서버 통제 콘텐츠+기존 새니타이즈 경로 경유
- 등급 가이드: Blocker

### key={index} 오용
- 보고 조건: 재정렬·삽입·삭제 가능한 목록의 key로 배열 index 사용
- 미보고 조건: 정적·불변 목록, 고유 id 부재+순서 고정이 계약
- 등급 가이드: Bug

### props·state 직접 변이
- 보고 조건: props 객체·useState 값·store 상태를 setter 없이 직접 수정(push, 속성 대입)
- 미보고 조건: 로컬 복사본 변이, 변이 API가 계약인 store(immer 등)
- 등급 가이드: Bug

## 설계

### 렌더 재생성 객체 하위 전파
- 보고 조건: 렌더마다 새 객체·배열·함수를 memo 컴포넌트·deps·context value에 전달해 재렌더·effect 재실행을 실측 가능하게 유발
- 미보고 조건: 일반 DOM·비-memo 자식 전달 — 기계적 useMemo/useCallback 지적 금지
- 등급 가이드: 개선 — effect 재실행이 실동작 버그(중복 요청 등)로 이어지면 Bug

### 단일 책임 훅
- 보고 조건: 한 훅이 상태+쿼리+뮤테이션+검증+props 조립 등 복수 변경 사유 전담, 순수 조립·판정이 훅 내부에 잔류
- 미보고 조건: 소규모 배선 전용 훅
- 등급 가이드: 개선

## lint SSOT 제외 항목 (체크리스트 관리자 참고 — 누락 아님)

대상 repo의 eslint 설정이 error로 차단하는 항목은 수록 금지 — 이 체크리스트는 그 기준으로 var·`==`·함수 선언식·curly·throw 리터럴·type import 분리·unused vars·import 정렬·파일/폴더 네이밍·조건부 훅 호출(rules-of-hooks)·JSX 스타일(self-closing 등)을 제외했다. warn 수준(게이트 비차단)으로 흔한 no-explicit-any·no-array-index-key·exhaustive-deps는 위 항목으로 수록 유지. 각 프로젝트는 자체 lint 설정을 기준으로 판단.
