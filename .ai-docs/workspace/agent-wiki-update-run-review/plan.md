# agent-wiki update 실행 리뷰 판정과 0.8.1 반영

## Context

- **요청**: 사내판 루트 `agent-wiki-update-review.md`(2026-10-06 실행 A·B 개선 제안 15건)를 비판 검토해 수용 여부를 정함 — 기준은 "간결한 구조와 프롬프트 최우선, 실측되고 개선 가능한 것만, 진행 중 자연 회복되는 문제는 무시"
- **판정 근거**: 개인판 0.8.0 소스(`agent-wiki/`, 사내판 `plugins/agent-wiki`와 고유 3파일 외 동일), 위키 PR #23·#24 본문의 실제 액션, 위키 `update-skill`·`wiki-apply-procedure` 결정, `.ai-docs/workspace/agent-wiki-update-review`·`argon1025-agent-wiki-update-0.7.0` 기록
- **결과**: 수용 2건(커서 커밋 1개화, 검토 입력의 `assign.json` 참조), 기각 13건

## 판정

| 항목 | 판정 | 근거 |
|---|---|---|
| 1-1 처리량 상한 | 기각 | 이월은 부트스트랩 백로그라 반복 실행으로 소진되고 이월 건수는 이미 집계 보고됨, `--max-merges` 존재, 연속 모드는 커서가 미머지 브랜치에 남아 열린 PR 중단 규칙과 충돌 |
| 1-2 소형 머지 비용 | 기각 | 머지 1건 추출은 토큰 약 2.3배를 감수한 기록된 결정(재현율 0.87 대 0.85), 규약 1~2장은 약 4KB라 38k 중 대부분은 에이전트 고정비 |
| 1-3 커서 커밋 수 + 1-4 셸 의존 | 수용(스크립트 제외) | "레포마다 커밋" 지시가 셸 반복문 오작동(zsh 단어 분리)의 원인이므로 Write 후 `git add state` 커밋 1개로 반복 자체를 없앰, `write_cursors.py`는 "커서 파일도 에이전트가 씀" 결정과 상충 |
| 1-5 PR 본문 이중 적재 | 기각 | 24KB 1회분으로 실행 전체(서브에이전트 51회) 대비 1% 미만, 호스트별 수행 방안 비안내 결정(2026-10-03) |
| 2-1 뒤 머지가 거짓으로 만든 앞 사실 | 기각 | 현행 4장 대체는 `order` 전역 순서라 레포 무관이며 PR #24에서 F11→F55, F53→F56 모두 `대체`로 처리됨, PR #23 F6은 `동일`·F15 `추가`로 결과 정상 — 위험은 가정뿐 |
| 2-2 결함 처리 경로 | 기각 | 결함 수정 머지가 같은 식별자를 바꾸면 2장 같은 식별자 규칙으로 함정 문장이 고쳐짐, 실측 1건(F13) |
| 3-1 단일 사실 신규 문서 | 기각 | 규약 7장 대조가 이미 기존 문서 우선, 신규 문서 사전 필터 기각 결정(2026-10-03), 병합은 감사 몫 |
| 3-2 같은 파일명 | 기각 | 규약 2장 분리(도메인 루트 의무·레포 폴더 구현)가 만드는 같은 주제 쌍이고, 세션 주입이 절별 경로 틀로 구분함 |
| 3-3 제목·파일명 불일치 | 기각 | 1건, 문서 선택은 description 기준, 이름 변경 흐름 추가 비용이 큼 |
| 3-4 메인 수작업 | 부분 수용 | 실행 B의 문서별 지시 파일 생성 원인인 검토 프롬프트 `{id·fact 목록}`·`{check}`·`{input}` 조립을 `assign.json` 항목 참조로 대체(반영 프롬프트와 같은 방식), 스크립트 3종은 "스크립트 최소화" 결정과 상충 |
| 4-1 추적 안 되는 삭제 | 기각 | PR diff에 드러나고 0.8.0 단일 사실 표 결정과 상충, 0.7.0 실행 1건 |
| 4-2 레포 밖 심볼 확인 | 기각 | 검토가 의존 레포를 읽어 스스로 교정함(자연 회복) |
| 4-3 코드값 표 행 수 | 기각 | 중복 코드는 enum 결함 자체(F12·F13)이고 표는 상수 4종을 그대로 전사함 |
| 5-1 검토 모델 지정 | 기각 | 0.8.0 실행 B에서 미재현, `model` 생략은 기본 서브에이전트 모델이 설정된 환경에서 메인 모델이 아님 |
| 5-2 MCP 연결 지연 | 기각 | 실행 B에서 재검색으로 회복(자연 회복), 사내판 고유 `publish.md` 소관 |

## 변경

### 1. 커서 커밋 1개 — `agent-wiki/skills/update/SKILL.md` 7절(89~94행)

```
`apply.md` 6·7장을 실행합니다. `--dry-run`이 아니면 이어서 커서를 정한 레포마다 `{tmp}/state/{slug}.json`에 `{"cursor": "{전체 sha}", "at": "YYYY-MM-DD"}`를 Write하고, 모두 쓴 뒤 커밋 한 개로 남깁니다. 본문은 레포마다 `{slug} {sha7}` 한 줄입니다.

git -C {tmp} add state
git -C {tmp} commit -m "chore(update): 커서 {N}개 레포 · 머지 {M}건" -m "{본문}"
```

- **전제 확인**: `collect_update_merges.py`는 커밋 또는 부트스트랩 레포가 있을 때만 0을 반환하므로 7절에는 커서가 1개 이상 있음 — 빈 커밋 분기 불필요

### 2. 검토 입력 참조화 — `agent-wiki/references/apply.md` 3장

- **54행**: 마지막 문장 "`{check}`는 사실 id별 `check`, `{input}`은 사실 행 `input`의 합집합입니다." 삭제
- **58행 입력 줄**: `입력: {work}/assign.json \`docs\`에서 \`doc\`이 "{doc}"인 항목의 사실 행(id·fact, 코드 확인 대상 check, 자료 원문 input), 문서 {tmp}/knowledge/{domain}/{doc}, 이번 변경 ...(현행 유지), 다른 문서 목록 ...(현행 유지).`로 교체
- **재배정**: 4장 "입력은 `{work}/assign-re.json`" 문장이 2·3장 모두에 적용되므로 수정 없음, add도 같은 `assign.json` 행 형식이라 수정 없음

### 3. 버전·미러링

- **개인판**: `agent-wiki/.claude-plugin/plugin.json` 0.8.0 → 0.8.1, `.claude-plugin/marketplace.json` `metadata.version` 4.2.0 → 4.2.1, 브랜치 `feat/agent-wiki-update-0.8.1`에 커밋 1개(`fix: agent-wiki update 커서 커밋 1개·검토 입력 assign.json 참조 v0.8.1`)
- **사내판**: `plugins/agent-wiki/skills/update/SKILL.md`·`references/apply.md`·`.claude-plugin/plugin.json`을 개인판으로 복사(고유 3파일 `config.json`·`references/publish.md`·`README.md` 제외), `.claude-plugin/marketplace.json` agent-wiki 항목 0.8.1·`metadata.version` 4.3.0 → 4.3.1, 브랜치 생성 후 커밋
- **게시**: push·PR은 사용자 요청 시 진행

### 4. 사내판 위키 사본 경로 분리 — 사내판 고유 파일만

- **충돌 원인**: 두 마켓플레이스의 agent-wiki가 모두 `wiki.baseRoot` `~/.agent-wiki`를 쓰고, 세션 시작 훅마다 `sync_wiki.py`가 그 사본을 각자의 원격(GitHub `main`·Bitbucket `master`)으로 `remote set-url`·강제 checkout함 — 두 훅이 같은 세션에서 경합해 나중에 끝난 쪽 위키가 다른 쪽 주입에 읽힘(현재 사본 origin은 GitHub)
- **`plugins/agent-wiki/config.json`**: `wiki.baseRoot`를 `~/.onestore-llm-wiki`로 변경(원격 저장소 이름과 일치), 개인판 `config.json`은 그대로
- **`plugins/agent-wiki/README.md`**: 설정 표 `wiki.baseRoot` 기본값과 위키 구조 블록 첫 줄을 새 경로로 수정
- **워크스페이스 유지**: `workspace.root` `~/.agent-wiki-workspace`는 공유 — clone이 `{slug}` 폴더 단위이고 두 위키의 등록 slug가 겹치지 않으며 어떤 스크립트도 목록 밖 폴더를 지우지 않음
- **전환 영향**: 사내판 0.8.1 설치 뒤 새 경로가 없으면 훅이 `위키 없음 — /agent-wiki:init 실행`만 주입하므로 사내 사용자마다 `/agent-wiki:init` 1회 필요, 사내판만 쓰던 사용자의 기존 `~/.agent-wiki`는 삭제 가능 — README는 현재 상태만 적는 규칙이라 사내판 커밋·PR 본문에 기재

### 5. 작업 기록 — `.ai-docs/workspace/agent-wiki-update-run-review/`

- **plan.md**: 이 계획 스냅샷
- **feedback.md**: 첫 기록 전 `record-format.md`를 읽고 `context`(판정 확정과 사용자 기준 문장, 사내판 baseRoot 분리 요청), `why`(커서 커밋을 스크립트 대신 단일 커밋으로 해결한 이유), `why`(2-1 기각 근거 PR #24 F11·F53 대체 실측), `constraint`(두 마켓플레이스 agent-wiki를 함께 설치하면 같은 baseRoot를 훅이 서로 다른 원격으로 강제 정리함)를 기록

## 특이 사항

- **위키 불일치**: 위키 `wiki-pr-body` 문서는 "제외된 사실 목록은 본문에 남김"이라 적지만 0.8.0 `templates/wiki-pr.md`는 `## 사실 목록` 표 하나뿐이므로 두 값이 다름 — 구현 후 `/agent-wiki:add`로 이 문서와 `internal-plugin-mirror`(사내판 baseRoot 분리 사실) 반영을 제안함

## 검증

- **잔존 확인**: `grep -n "{id·fact\|{check}\|{input}\|add state/{slug}" agent-wiki` 결과 0건, 사내판 `diff -rq`가 고유 3파일만 표시, 사내판 `grep -rn "\.agent-wiki\b" plugins/agent-wiki`가 워크스페이스 경로 외 0건
- **경로 분리**: 사내판 `config.json`을 임시 플러그인 루트로 복사한 스크래치 환경에서 `session_start.py`를 실행해 새 경로가 없을 때 init 안내 한 줄만 나오고 `~/.agent-wiki` origin이 GitHub 그대로인지 확인
- **커서 커밋**: 스크래치 git 저장소에서 `state/a.json`·`state/b.json`을 Write한 뒤 7절 명령 그대로 실행해 `git log --stat -1`이 커밋 1개·파일 2개인지 확인
- **검토 입력**: 개인 위키 문서 1장과 사실 2건짜리 스크래치 `assign.json`(check에 실제 레포 경로·sha)으로 새 3장 프롬프트 검토 에이전트 1회를 실행해, 출력 `review/*.json`의 `ids`가 assign 행 id와 맞고 코드 확인이 각 사실 rev로 이뤄졌는지 확인
