---
name: register
description: Use when the current git repo must be registered in the wiki, moved to another domain, or its status inspected ("이 레포 위키에 등록", "레포 등록", "도메인 이동", "위키 상태", session header says 미등록 레포 or index.md 없음) — picks or creates the {조직}-{도메인} domain, records repos.{slug} (domain·remotes·branch) in registry.json, scaffolds or updates knowledge/{domain}/index.md, records the local path, commits and pushes, prints the repo status table. NOT for creating the wiki repo itself (that is /llm-wiki:init's job) and NOT for writing facts (that is /llm-wiki:add and /llm-wiki:update's job).
disable-model-invocation: true
---

현재 레포를 위키에 등록하고 도메인 지도(`index.md`) 골격을 만듭니다. 규격은 `${CLAUDE_PLUGIN_ROOT}/references/doc-contract.md` 3·9장이 정본이며, 이 스킬은 사실을 쓰지 않습니다.

## 1. 전제

- **위키**: `{WIKI_ROOT}/registry.json`이 없으면 `/llm-wiki:init` 안내 후 중단, 있으면 `git -C {WIKI_ROOT} pull --ff-only` — 충돌·분기는 멈추고 보고
- **레포**: 현재 디렉터리가 git 레포가 아니면 중단, 인자 `--status`만 있으면 6장으로
- **slug**: origin(없으면 upstream) URL의 마지막 경로 요소에서 `.git` 제거·소문자·비허용 문자 하이픈 치환, remote가 없으면 `git rev-parse --path-format=absolute --git-common-dir`의 부모 디렉터리명 — 다른 remote의 레포와 slug가 겹치면 `{domain}-{name}`을 제안
- **기존 등록**: `repos.{slug}`가 이미 있으면 2장에서 도메인 이동·remote 추가 여부를 묻고, 둘 다 아니면 `.local/paths.json`만 갱신해 6장으로

## 2. 질문 — 정지점 하나

- **도메인**: `registry.json`의 `domains` 목록 중 선택 또는 신규 `{조직}-{도메인}`(`^[a-z0-9]+-[a-z0-9-]+$`) + 한 줄 설명 — 신규면 index.md 첫 단락이 됨
- **기본 브랜치**: `git symbolic-ref refs/remotes/origin/HEAD`의 꼬리를 초안으로 제시(없으면 `main`)
- **기존 등록 레포**: 도메인 이동(대상 도메인)과 remote 추가(현재 URL을 `remotes`에 더함) 여부를 같은 라운드에 물음
- **스택 초안**: `package.json`·`pom.xml`·`build.gradle`에서 언어·프레임워크를 읽어 `## 레포 구성` 행에 넣음 — 못 읽으면 `—`

## 3. registry.json

- **repos**: `repos.{slug}` = `{"domain", "remotes": [정규화 URL…], "branch"}` 3키만
- **domains**: 신규 도메인이면 `domains.{d}: {}` 추가 — 설명은 index.md 본문에만 둠
- **커서**: `state/`는 만들지 않음 — 첫 `/llm-wiki:update`가 HEAD로 부트스트랩하며 과거 소급은 `--baseline-days N`

## 4. index.md와 폴더

- **신규 도메인**: `knowledge/{d}/index.md`를 규약 9장 템플릿으로 생성 — 제목·한 줄 설명·`## 레포 구성` 1행(스택 초안, 접점 `—`, 소관 "아직 정해지지 않음"), 나머지 절은 두지 않음, `description`은 고정문 `{d} 레포 소관·역인덱스·변경 파급을 볼 때`
- **기존 도메인**: `knowledge/{d}/index.md`의 `## 레포 구성`에 행 추가 — 없으면 신규와 같이 생성
- **도메인 이동 — 승인 하나**: `knowledge/{old}/{slug}/`가 있으면 `git mv knowledge/{old}/{slug} knowledge/{new}/{slug}` 대상·건수를 보이고 승인 후 실행, 양쪽 index.md의 `## 레포 구성` 행을 옮기고 역인덱스 행의 slug는 `{old}/{slug}` 꼴이 되지 않게 확인, `deps.json`의 `{old}/{slug}` 끝점을 `{new}/{slug}`로 치환하고 `--check`로 대조 — 같은 커밋에 담음
- **레포 폴더**: `knowledge/{d}/{slug}/`는 만들지 않음 — 첫 레포 종속 문서가 생길 때 add·update가 만듦

## 5. 로컬 경로·커밋

- **paths.json**: `.local/paths.json`에 `{slug: git toplevel 절대경로}` 갱신 — 미추적 파일이라 머신마다 따로 쌓임
- **검사**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/catalog.py" --check --root {WIKI_ROOT}/knowledge {index.md 절대경로}` 에러 0
- **커밋**: `chore(register): {slug} → {domain}` 한 커밋(이동이면 `chore(register): {slug} {old} → {new}`), `git -C {WIKI_ROOT} pull --rebase && git push` — 실패는 로컬 커밋 상태와 함께 보고

## 6. 상태 표·보고

- **상태 표**: `registry.json`·`state/*.json`·`.local/paths.json` 3파일을 Read해 `| 레포 | 도메인 | 브랜치 | 커서 | 갱신일 | 로컬 경로 |` 표를 출력 — 커서 없음은 `없음`, 경로 없음은 `없음`(그 레포에서 세션을 열거나 register하면 기록됨)
- **다음**: 세션을 다시 열면 `index.md` 본문과 도메인·레포 목록이 주입되고, 머지 반영은 `/llm-wiki:update`, 자료 반영은 `/llm-wiki:add`
