# llm-wiki

코드에 없는 사실(정책·결정 근거·외부 계약·함정)을 별도 git 저장소에 모으고, 그 문서 목록을 세션 시작 시 주입하는 플러그인입니다. 위키는 플러그인 저장소 밖에 있어 여러 머신과 팀원이 같은 저장소를 공유합니다.

| 스킬 | 트리거 예 | 역할 |
| --- | --- | --- |
| `/llm-wiki:init` | "위키 초기화", "위키 세팅" | 위키 clone 또는 생성, 원격 연결, 골격 생성 |
| `/llm-wiki:register` | "이 레포 위키에 등록", "도메인 이동" | 현재 레포를 1회 조사해 노드·나가는 간선 기록, 도메인 선택·신설, 로컬 경로 기록, 상태 표 |
| `/llm-wiki:update` | "위키 업데이트", "머지 반영" | 대상 도메인을 확인한 뒤 그 도메인 레포를 커서부터 훑어 머지 diff에서 사실을 뽑아 무인 반영, 커서 전진 |
| `/llm-wiki:add` | "위키에 정리해줘", "정책으로 기록해줘" | 건넨 자료·대화에서 확정된 사실을 반영, 근거 없이 기존 값을 덮는 건만 질문 한 라운드 |
| `/llm-wiki:audit` | "위키 정리", "중복 정리" | 조각·중복·낡음·규약 위반을 승인 표 하나로 정리 |

## 설치

```
/plugin marketplace add argon1025/my-claude-plugin-market
/plugin install llm-wiki@my-claude-plugin-market
```

설치 후 새 세션에서 `/llm-wiki:init`으로 위키 저장소를 놓고, 각 레포에서 `/llm-wiki:register`로 등록합니다. 위키 경로 기본값은 `~/.ai-docs/wiki`이며, 바꾸려면 `~/.claude/settings.json`의 `env`에 지정합니다.

```json
{ "env": { "LLM_WIKI_ROOT": "/절대/경로/wiki" } }
```

## 전제 조건

- **python3·git**: 훅과 스크립트가 둘 다 씀 — `python3`가 없으면 주입 없이 조용히 끝남
- **원격 저장소**: 위키는 원격이 있어야 다른 머신·팀원과 공유되며, 원격 없이도 동작하지만 로컬 전용이 됨

## 동작 방식

- **SessionStart**: 규약(`rules/agent-guide.md`)과 그래프 파생 블록(도메인 목록 → 접근 좌표 → 역인덱스 → 현재 레포 기준 두 묶음 간선 → 인접 레포 좌표), 도메인 루트와 현재 레포 문서 목록을 주입하며, matcher가 없어 startup·resume·clear·compact·fork 모두에서 다시 실행됨
- **그래프 파생**: 역인덱스·도메인 간 의존 요약·인접 좌표는 저장하지 않고 `scripts/graph.py`가 `registry.json` 노드와 `deps.json` 간선에서 매번 계산 — 같은 사실을 사람이 쓰는 지도 문서에도 두면 갱신 규칙이 하나 더 늘고 두 값이 갈림
- **주입 범위**: 도메인 전체의 이름·설명·업무 영역과 현재 도메인과의 의존 집계, 현재 도메인의 접근 좌표·역인덱스 전수, 현재 레포의 선행 조건·파급 대상 간선과 그 상대 레포 좌표, 현재 도메인 루트 전수(레포 폴더 제외) + 현재 레포 폴더 전수 — 다른 도메인의 문서 목록·역인덱스는 주입하지 않고 `python3 scripts/graph.py map --domain {d}`로 한 번에 봄
- **세 가지 질문**: 업무 낱말로 수정 대상 레포를 찾는 것은 역인덱스, 코드를 쓰기 전 상대 계약 대응 여부를 보는 것은 `이 레포가 의존` 간선과 인접 좌표의 로컬 경로·remote, 변경의 타 도메인 파급을 보는 것은 `이 레포에 의존` 간선이 답함
- **레포 판정**: origin(없으면 upstream) URL을 정규화해 `registry.json`과 맞추고 실패하면 URL 마지막 경로 요소를 slug로 씀 — 미등록이면 규약·등록 안내(`/llm-wiki:register`)·도메인 목록만 주입
- **낡음 신호**: 마지막 확인이 180일을 넘은 문서와 간선에 `!`가 붙고, 레포 커서가 HEAD보다 뒤처지면 몇 커밋 뒤인지가 헤더에 표시됨
- **동기화**: startup·resume 이벤트에서만, 위키에 원격이 있고 마지막 fetch가 10분(`LLM_WIKI_SYNC_MINUTES`로 조정)을 넘었으면 백그라운드로 `pull --ff-only`를 걸고 3초까지 기다리며, 지연·실패는 헤더 한 줄로 알림
- **확인 필요 인박스**: 무인 갱신이 판정하지 못한 충돌, 근거를 얻지 못한 교체 요청, 새 업무 영역 후보는 도메인별 `inbox/{domain}.md`에 쌓이고 현재 레포 도메인의 건수만 세션 헤더에 표시되며 `/llm-wiki:add`가 소비함 — 담당자가 다른 도메인이 한 파일을 append하며 생기는 push 충돌을 피하기 위해 나눔
- **소프트 예산**: 목록은 어떤 크기에서도 줄이지 않으며 주입이 약 8,000토큰을 넘으면 정리 권고 한 줄이 붙음

## 위키 구조

```
~/.ai-docs/wiki/                    # LLM_WIKI_ROOT. 별도 git 저장소
├── registry.json                   # register가 편집: 도메인과 레포 노드. 있으면 위키가 초기화된 것
├── deps.json                       # register·update(관찰)·add(확인)가 편집: 레포 간 의존 간선
├── state/{slug}.json               # update만 편집: {"cursor", "at"}
├── inbox/{도메인}.md               # update·add·audit이 남긴 확인 필요 인박스, 도메인마다 하나, add가 소비
├── .gitignore                      # .local/
├── .local/paths.json               # 머신별 로컬 경로 (미추적, 훅·register가 기록)
└── knowledge/
    └── {조직}-{도메인}/             # 도메인 루트 — 레포를 지워도 참인 사실
        ├── adr/                    # 선택
        └── {레포 slug}/            # 레포 종속 — 이 레포를 지우면 거짓이 되는 사실
            └── adr/                # 선택
```

위치 판정은 "이 레포를 지워도 참인가" 한 단계이며, 회사 전체 공통 폴더는 두지 않고 레포는 한 도메인에만 속합니다. 레포 소관·역인덱스·접근 좌표·의존은 문서가 아니라 아래 노드와 간선에 둡니다.

```json
{
  "domains": {
    "onestore-devcenter": {
      "description": "개발자센터 셀러 콘솔·앱 등록 레포 모음",
      "access": ["Bitbucket 프로젝트 DEVCENTER — https://bitbucket.example.com/projects/DEVCENTER"]
    }
  },
  "repos": {
    "devcenter-api": {
      "domain": "onestore-devcenter",
      "remotes": ["bitbucket.example.com/scm/devcenter/devcenter-api"],
      "branch": "develop",
      "status": "active",
      "stack": "Java 21 · Boot 3.5",
      "summary": "백엔드 API. 로그인 룰 체인·세션과 공지·메뉴·파일",
      "areas": { "onestore-devcenter/로그인·세션": "룰 체인·세션·핸드오프" },
      "hosts": ["api.devcenter.example.com", "com.onestorecorp.devcenter:devcenter-client"],
      "source": "확인 — register 조사, 2026-09-16"
    }
  }
}
```

```json
{
  "edges": [
    {
      "from": "onestore-display/display-front",
      "to": "onestore-devcenter/devcenter-agent",
      "kind": "message",
      "note": "product.deployed",
      "source": "관찰 — register 조사, 2026-09-16"
    }
  ]
}
```

간선 방향은 `kind`(`library`·`http`·`message`·`data`)와 무관하게 "`from`이 `to`의 계약에 의존"으로 하나이며, 메시지는 발행자가 `to`입니다. 문서 규격과 사실 판정 기준은 `references/doc-contract.md`에 있고 스킬 실행 시에만 읽힙니다. `scripts/catalog.py --check`가 문서를, `scripts/graph.py check`가 노드·간선을 검사하며 전자가 후자를 함께 냅니다.

## 무인 갱신 범위

- **선택**: 실행 시작에 `update.py domains`가 도메인별 레포와 미반영 커밋 수를 내고 그중 고른 도메인만 처리 — `--domain`·`--repo`·`--range`·`--all`이 주어진 실행은 묻지 않으며, 미반영 수는 fetch 전 로컬 ref 기준이라 실제 처리량이 더 늘 수 있음
- **대상**: `.local/paths.json`에 로컬 경로가 있고 `status`가 `active`인 등록 레포만 — 그 레포에서 세션을 한 번 열면 훅이 경로를 기록함
- **범위**: 커서부터 대상 브랜치까지의 first-parent 커밋, 레포별 기본 20건 — 추출은 머지 5건 또는 diff 500KB 중 먼저 닿는 묶음 단위로 서브에이전트 1회씩(diff 1건은 400KB에서 절단)
- **권한**: `관찰` 출처만 만들어 기존 값을 덮지 않고 보강만 하며, 도메인 루트와 레포 폴더를 모두 직접 보강하고 충돌만 그 도메인의 `inbox/{domain}.md`로 보냄
- **그래프 보강**: 간선은 대상이 어느 노드의 `hosts`에 있을 때만 생기고, 업무 영역은 기존 키에 레포를 붙이는 것까지만 — 새 영역 이름과 미등록 상대는 인박스·보고로 남고 `/llm-wiki:add`나 `/llm-wiki:register`가 처리함

## 미이전 기능

사내 위키 플러그인에서 옮기지 않은 것입니다.

- **영구 제외**: 팀 PR 게이트에 묶인 반영 절차와 그 원자재 대장·원장·샤드·잠금 파일, PR 본문 생성, 이슈 트래커 기반 범위 리뷰, 동기화 전용 스킬(훅이 pull하고 스킬이 push함), 매 턴 리마인더 훅, 출처 병합 스크립트(규약으로 대체), 테스트 파일
- **추후 후보**: 대형 PDF 전처리, 문서 재구조화·분할·보완 모드, 문서별 드리프트 표시, 레포 안 지식 오버레이, 성격별 폴더 분류
- **보류(사용 후 재검토)**: 다중 위키, 조직·도메인 무관 사실의 자리(always 도메인), 레포 다중 도메인, frontmatter keywords와 grep 1회 규칙(검색 보강)
