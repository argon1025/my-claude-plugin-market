# pr-review Layer 1 체크리스트 — Java/Kotlin + Spring Boot

- common.md에 더해 적용. Layer 2(프로젝트 문서)가 같은 주제를 다루면 Layer 2 우선
- 전 항목 공통: 보고 조건 충족 AND 미보고 조건 미해당일 때만 보고

## 결함

### @Transactional 경계 오류
- 보고 조건: 같은 클래스 내부 메서드 호출(self-invocation)로 프록시가 우회되어 트랜잭션 미적용, 쓰기 경로 메서드에 readOnly=true, 복수 쓰기가 단일 트랜잭션 밖에서 부분 실패 가능
- 미보고 조건: 단건 조회 등 트랜잭션 불필요가 명백, AopContext/TransactionTemplate 등 우회 처리 존재
- 등급 가이드: 부분 실패로 데이터 정합이 깨지는 경로가 확인되면 Blocker, 그 외 Bug

### N+1·LazyInitializationException
- 보고 조건: 루프 안에서 lazy 연관 접근으로 쿼리가 건수만큼 반복, 트랜잭션·세션 경계 밖 lazy 연관 접근
- 미보고 조건: fetch join·@EntityGraph·batch size 등 로딩 전략 존재, 소량 고정 데이터 명백
- 등급 가이드: LazyInitializationException은 Bug(핵심 흐름 크래시면 Blocker), N+1은 개선(목록·배치 등 대량 경로가 확인되면 Bug)

### 싱글톤 빈 가변 상태 공유
- 보고 조건: 싱글톤 빈의 인스턴스 필드에 요청·사용자별 가변 상태 저장 — 동시 요청 간 상태 오염
- 미보고 조건: 불변 설정값, 동시성 안전 구조(ConcurrentHashMap 등)가 캐시 용도로 의도됨
- 등급 가이드: 동시 요청 간 사용자 데이터가 섞이면 Blocker, 그 외 Bug

### 과대 catch·예외 정보 소실
- 보고 조건: catch(Exception) 광역 포획 후 복구 없이 진행, checked 예외를 원인(cause) 없이 래핑해 스택 소실
- 미보고 조건: 최상위 경계(스케줄러·컨트롤러 어드바이스)의 의도된 광역 처리+로깅
- 등급 가이드: Bug

### 입력 검증 누락
- 보고 조건: 외부 입력 DTO에 검증 어노테이션 부재 또는 컨트롤러 파라미터 @Valid/@Validated 누락으로 무검증 진입
- 미보고 조건: 별도 검증 계층이 같은 요청 경로에서 수행, 내부 시스템 간 신뢰 경계가 정책
- 등급 가이드: Bug — 인젝션·권한 우회 등 보안 노출 경로면 Blocker

### 리소스 누수
- 보고 조건: Closeable 자원(스트림·커넥션·클라이언트)을 try-with-resources·finally 해제 없이 사용
- 미보고 조건: 컨테이너·프레임워크가 수명 관리(스프링 관리 빈, @Transactional 커넥션)
- 등급 가이드: Bug

### JPA 엔티티 equals·hashCode 함정
- 보고 조건: 가변 필드 또는 영속화 전 null인 id 기반 equals/hashCode를 Set·Map 키로 사용
- 미보고 조건: 컬렉션 비교에 쓰이지 않는 엔티티, 불변 비즈니스 키 기반
- 등급 가이드: Bug

### SQL·JPQL 문자열 조립
- 보고 조건: 사용자 입력을 문자열 연결로 SQL/JPQL/네이티브 쿼리에 삽입
- 미보고 조건: 파라미터 바인딩 사용, 화이트리스트 상수만 조립(동적 정렬 컬럼 등)
- 등급 가이드: Blocker

### Optional 무검증 get
- 보고 조건: 존재 검사 없는 Optional.get() 등 부재 시 NoSuchElementException으로 터지는 경로
- 미보고 조건: 직전 로직이 존재를 보장, orElseThrow로 도메인 예외 매핑
- 등급 가이드: Bug

## 설계

### 필드 주입
- 보고 조건: @Autowired 필드 주입 신설 — 불변성·테스트 주입 불가
- 미보고 조건: 기존 코드베이스가 필드 주입 일관 사용 중이고 변경 파일이 그 관례를 따름
- 등급 가이드: 개선
