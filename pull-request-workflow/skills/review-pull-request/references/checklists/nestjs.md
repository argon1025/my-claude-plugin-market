# pr-review Layer 1 체크리스트 — NestJS

- common.md에 더해 적용(TS 언어 항목은 typescript-react.md의 타입 탈출도 병용). Layer 2(프로젝트 문서)가 같은 주제를 다루면 Layer 2 우선
- 전 항목 공통: 보고 조건 충족 AND 미보고 조건 미해당일 때만 보고

## 결함

### 입력 검증 누락
- 보고 조건: 외부 입력 DTO에 class-validator 데코레이터 부재, ValidationPipe 미적용 라우트, whitelist 미설정으로 임의 필드 통과
- 미보고 조건: 전역 ValidationPipe가 부트스트랩에서 적용됨, 별도 검증 계층이 같은 경로에서 수행
- 등급 가이드: Bug — 인젝션·권한 우회 등 보안 노출 경로면 Blocker

### 프로바이더 스코프 오류
- 보고 조건: 싱글톤 프로바이더의 인스턴스 필드에 요청·사용자별 가변 상태 저장, request-scoped 프로바이더를 싱글톤에 직접 주입(스코프 버블링·상태 고착)
- 미보고 조건: 불변 설정값, ModuleRef/ContextId로 스코프 해석 처리 존재
- 등급 가이드: 동시 요청 간 사용자 데이터가 섞이면 Blocker, 그 외 Bug

### async 핸들러 floating promise
- 보고 조건: 컨트롤러·서비스에서 await/return 없는 promise — 실패가 침묵하거나 응답 반환 후 미완료 작업 잔존
- 미보고 조건: fire-and-forget이 의도이고 실패 처리(.catch·이벤트 큐) 존재
- 등급 가이드: Bug

### 예외 매핑 누락
- 보고 조건: 도메인·인프라 예외가 HttpException 매핑 없이 전파되어 일괄 500 응답·내부 정보 노출
- 미보고 조건: 전역 예외 필터가 해당 예외를 처리
- 등급 가이드: Bug — 스택·내부 구조가 응답으로 노출되면 Blocker

### Guard·Interceptor 누락
- 보고 조건: 보호가 필요한 신규 라우트에 인증·인가 Guard 누락, 실행 순서에 의존하는 Guard/Interceptor/Pipe 조합의 순서 오류
- 미보고 조건: 전역 Guard가 커버하고 공개 라우트 데코레이터가 의도됨
- 등급 가이드: 인증·인가 우회가 가능하면 Blocker, 순서 오류는 Bug

### ORM 트랜잭션 경계 누락
- 보고 조건: 복수 쓰기(생성+갱신, 다중 repository)가 단일 트랜잭션 없이 수행되어 부분 실패 가능
- 미보고 조건: 단건 쓰기, 트랜잭션 데코레이터·QueryRunner·interactive transaction 존재
- 등급 가이드: 부분 실패로 데이터 정합이 깨지는 경로가 확인되면 Blocker, 그 외 Bug

## 설계

### 순환 의존·forwardRef 봉합
- 보고 조건: 신규 코드가 모듈·프로바이더 순환 의존을 도입하고 forwardRef로 봉합
- 미보고 조건: 기존 순환 구조의 유지보수 변경
- 등급 가이드: 개선

### ConfigService 우회
- 보고 조건: 애플리케이션 코드에서 process.env 직접 접근 신설 — 검증·기본값 계층 우회
- 미보고 조건: 부트스트랩 이전 단계(main.ts 초기화, config 로더 자체)
- 등급 가이드: 개선
