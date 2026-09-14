# llm-wiki

코드에 없는 사실(정책·결정 근거·외부 계약·함정)을 별도 git 저장소에 모으고, 그 문서 목록을 세션 시작 시 주입하는 플러그인입니다. 위키는 플러그인 저장소 밖에 있어 여러 머신과 팀원이 같은 저장소를 공유합니다.

| 스킬 | 트리거 예 | 역할 |
| --- | --- | --- |
| `/llm-wiki:init` | "위키 초기화", "이 레포 위키에 등록" | 위키 clone 또는 생성, 프로젝트·레포 등록, 로컬 경로 기록 |
| `/llm-wiki:update` | "위키 업데이트", "머지 반영" | 등록 레포를 커서부터 훑어 머지 diff에서 사실을 뽑아 무인 반영, 커서 전진 |
| `/llm-wiki:add` | "위키에 정리해줘", "정책으로 기록해줘" | 건넨 자료·대화에서 확정된 사실을 질문 한 라운드로 반영 |
| `/llm-wiki:audit` | "위키 정리", "중복 정리" | 조각·중복·낡음·규약 위반을 승인 표 하나로 정리 |

## 설치

```
/plugin marketplace add argon1025/my-claude-plugin-market
/plugin install llm-wiki@my-claude-plugin-market
```

설치 후 새 세션에서 `/llm-wiki:init`을 실행해 위키 저장소를 놓습니다. 위키 경로 기본값은 `~/.ai-docs/wiki`이며, 바꾸려면 `~/.claude/settings.json`의 `env`에 지정합니다.

```json
{ "env": { "LLM_WIKI_ROOT": "/절대/경로/wiki" } }
```

## 전제 조건

- **python3·git**: 훅과 스크립트가 둘 다 씀 — `python3`가 없으면 주입 없이 조용히 끝남
- **원격 저장소**: 위키는 원격이 있어야 다른 머신·팀원과 공유되며, 원격 없이도 동작하지만 로컬 전용이 됨

## 동작 방식

- **SessionStart**: 규약(`rules/agent-guide.md`)과 도메인 루트·현재 레포 목록을 주입하며, matcher가 없어 startup·resume·clear·compact 모두에서 다시 실행됨
- **주입 범위**: 현재 레포가 속한 도메인 루트 전수(레포 폴더 제외) + 현재 레포 폴더 전수, 형제 레포와 다른 도메인은 이름 한 줄 — 목록이 소프트 8,000토큰을 넘으면 정리 권고가 붙고 하드 12,000토큰을 넘으면 가장 큰 목록이 전체 보기 명령 한 줄로 접힘
- **레포 판정**: origin(없으면 upstream) URL을 정규화해 `registry.json`과 맞추고 실패하면 URL 마지막 경로 요소를 slug로 씀 — 미등록이면 규약과 등록 안내(`/llm-wiki:register`)만 주입
- **낡음 신호**: 마지막 확인이 180일을 넘은 문서에 `!`가 붙고, 레포 커서가 HEAD보다 뒤처지면 몇 커밋 뒤인지가 헤더에 표시됨
- **동기화**: 위키에 원격이 있고 마지막 fetch가 60분을 넘었으면 백그라운드로 `pull --ff-only`를 걸고 3초까지 기다리며, 지연·실패는 헤더 한 줄로 알림
- **확인 필요 인박스**: 무인 갱신이 판정하지 못한 충돌은 `inbox.md`에 쌓이고 세션 헤더에 건수가 표시되며 `/llm-wiki:add`가 소비함

## 위키 구조

```
~/.ai-docs/wiki/                    # LLM_WIKI_ROOT. 별도 git 저장소
├── registry.json                   # register가 편집: 도메인과 레포 등록. 있으면 위키가 초기화된 것
├── state/{slug}.json               # update만 편집: {"cursor", "at"}
├── inbox.md                        # update가 남긴 확인 필요 인박스, add가 소비
├── .gitignore                      # .local/
├── .local/paths.json               # 머신별 로컬 경로 (미추적, 훅·register가 기록)
└── knowledge/
    └── {조직}-{도메인}/             # 도메인 루트 — 레포를 지워도 참인 사실
        ├── index.md                # 예약·필수: 레포 구성·의존 방향·역인덱스·접근 좌표
        ├── adr/                    # 선택
        └── {레포 slug}/            # 레포 종속 — 이 레포를 지우면 거짓이 되는 사실
            └── adr/                # 선택
```

위치 판정은 "이 레포를 지워도 참인가" 한 단계이며, 회사 전체 공통 폴더는 두지 않고 레포는 한 도메인에만 속합니다.

```json
{
  "domains": { "onestore-devcenter": {}, "personal-trendlog": {} },
  "repos": {
    "devcenter-api": { "domain": "onestore-devcenter", "remotes": ["bitbucket.example.com/cms/devcenter-api"], "branch": "develop" },
    "trendlog-backend": { "domain": "personal-trendlog", "remotes": ["github.com/argon1025/trendlog-backend"], "branch": "main" }
  }
}
```

문서 규격과 사실 판정 기준은 `references/doc-contract.md`에 있고 스킬 실행 시에만 읽힙니다. `scripts/catalog.py --check`가 기계로 볼 항목(frontmatter 3키·날짜·설명 60자 상한·위치·설명 중복)을 검사합니다.

## 무인 갱신 범위

- **대상**: `.local/paths.json`에 로컬 경로가 있는 등록 레포만 — 그 레포에서 세션을 한 번 열면 훅이 경로를 기록함
- **범위**: 커서부터 대상 브랜치까지의 first-parent 커밋, 레포별 기본 20건
- **권한**: `관찰` 출처만 만들어 기존 값을 덮지 않고 보강만 하며, 도메인 루트와 레포 폴더를 모두 직접 보강하고 충돌만 `inbox.md`로 보냄

## 미이전 기능

사내 위키 플러그인에서 옮기지 않은 것입니다.

- **영구 제외**: 팀 PR 게이트에 묶인 반영 절차와 그 원자재 대장·원장·샤드·잠금 파일, PR 본문 생성, 이슈 트래커 기반 범위 리뷰, 동기화 전용 스킬(훅이 pull하고 스킬이 push함), 매 턴 리마인더 훅, 출처 병합 스크립트(규약으로 대체), 테스트 파일
- **추후 후보**: 대형 PDF 전처리, 문서 재구조화·분할·보완 모드, 문서별 드리프트 표시, 프로젝트 하위 레포 층, 레포 안 지식 오버레이, 성격별 폴더 분류
