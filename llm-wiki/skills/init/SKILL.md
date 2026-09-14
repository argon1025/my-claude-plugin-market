---
name: init
description: Use when the wiki repo is not present on this machine or the current repo is not registered ("위키 초기화", "위키 세팅", "이 레포 위키에 등록") — clones the shared wiki into the wiki root (or git-inits a new one and asks for the remote), registers the project and the current repo in registry.json, records the local path, prints the catalog. NOT for writing facts (that is /llm-wiki:add and /llm-wiki:update's job).
disable-model-invocation: true
---

위키 저장소를 이 머신에 놓고 현재 레포를 등록합니다. 위키 경로는 `LLM_WIKI_ROOT`이며 기본값은 `~/.ai-docs/wiki`입니다. 이 스킬은 사실을 쓰지 않습니다.

## 1. 저장소

- **있음**: `git -C {WIKI_ROOT} pull --ff-only` 후 2장으로 — 충돌·분기는 멈추고 보고
- **없음**: 원격 URL을 물어 `git clone {URL} {WIKI_ROOT}`, 사용자가 새로 만들겠다고 하면 `git init`
- **새로 만들 때**: `state/` 생성, `.gitignore`에 `.local/`, `registry.json`에 `{"domains": {}, "repos": {}}`를 쓰고 첫 커밋 — 원격 URL을 받았으면 `git remote add origin`과 `push -u`
- **원격 없음 경고**: 원격을 끝내 못 받으면 "다른 머신·팀원과 공유되지 않음"을 보고에 남김

## 2. 레포 등록

- **대상**: 현재 디렉터리가 git 레포이고 `registry.json`에 없을 때만 — 이미 등록됐으면 경로만 갱신하고 3장으로
- **slug**: origin(없으면 upstream) URL의 마지막 경로 요소에서 `.git` 제거·소문자·비허용 문자 하이픈 치환, remote가 없으면 `git rev-parse --path-format=absolute --git-common-dir`의 부모 디렉터리명 — 이미 쓰는 slug와 겹치면 `{domain}-{name}`을 제안
- **질문 한 라운드**: AskUserQuestion으로 도메인(기존 `domains` 목록 또는 신규 `{조직}-{도메인}`)·기본 브랜치를 함께 물음
- **기록**: `registry.json`의 `repos.{slug}`에 `domain`·`remotes`·`branch`, 신규 도메인이면 `domains.{d}: {}`도 함께
- **로컬 경로**: `.local/paths.json`에 `{slug: 저장소 절대경로}` — 추적하지 않는 파일이라 머신마다 따로 쌓임
- **커서 없음**: `state/`는 만들지 않음 — 첫 `/llm-wiki:update`가 HEAD로 부트스트랩하며, 과거를 소급하려면 `--baseline-days N`

## 3. 커밋·보고

- **커밋**: `registry.json` 변경을 `chore(init): {slug} 등록` 한 커밋으로, `git pull --rebase && git push`
- **목록**: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/catalog.py" --root {WIKI_ROOT}/knowledge/{domain} --shallow --label "도메인 {domain}"` 출력
- **안내**: 다음 세션부터 규약과 목록이 자동 주입된다는 것, 머지 반영은 `/llm-wiki:update`, 자료 반영은 `/llm-wiki:add`
