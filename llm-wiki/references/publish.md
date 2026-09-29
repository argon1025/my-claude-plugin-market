# 위키 저장소 절차

쓰기 스킬(init·register·add·audit·update)이 위키 사본을 다루는 시작과 끝입니다. 변형 배포는 이 파일을 통째로 바꾸므로 `##` 절 제목은 스킬이 참조하는 계약이며 바꾸지 않습니다.

- **저장소**: 고정하지 않음 — init이 clone URL 또는 새로 만들기를 물음
- **기준 브랜치**: `main`
- **커밋 링크**: `https://{remote}/commit/{sha}` — `remote`는 registry 노드 값

## 1. 시작

- **동기화**: `git -C {WIKI_ROOT} switch main && git -C {WIKI_ROOT} pull --ff-only` — 실패하면 보고 후 중단(팀원 커밋과 갈라진 상태에서 편집 금지)
- **열린 update PR**: update이고 `--dry-run`이 아니면 `WIKI_ROOT`에서 `gh pr list --state open --json url,headRefName` — `wiki-update/` 브랜치 PR이 있으면 그 링크를 보고하고 중단(머지 전 재실행은 같은 머지를 두 번 추출함), 명령이 실패하면(GitHub 원격 없음·미인증) 오류 한 줄을 보고하고 중단

## 2. 브랜치

- **update**: 추적 파일을 처음 고치기 전에 `git -C {WIKI_ROOT} switch -c wiki-update/{YYYYMMDD-HHMM}`
- **그 외**: 브랜치 없이 `main`에서 편집·커밋

## 3. 게시

- **update**: `git -C {WIKI_ROOT} push -u origin {branch}` 후 `WIKI_ROOT`에서 `gh pr create --base main --head {branch} --title "update: {YYYY-MM-DD} 머지 {N}건 · 문서 {M}장" --body-file {본문}` — 실패하면 단계·브랜치 이름·오류 한 줄 보고
- **긴 본문**: 본문이 60,000바이트를 넘으면 `추출 사실` 절을 떼어 본문에 "사실 원장은 첫 코멘트" 한 줄을 두고, PR 생성 뒤 뗀 절을 `gh pr comment {url} --body-file`로 게시
- **그 외**: `git -C {WIKI_ROOT} pull --rebase && git -C {WIKI_ROOT} push` — 실패는 로컬 커밋 상태와 함께 보고
- **변경 0건**: 커밋이 없으면 게시하지 않고, 브랜치를 만들었으면 `git -C {WIKI_ROOT} switch main && git -C {WIKI_ROOT} branch -D {branch}`

## 4. 종료

- **복귀**: 브랜치를 만든 실행은 성공·실패와 무관하게 어느 단계에서 끝나든 미커밋 편집을 `git -C {WIKI_ROOT} stash -u`로 치우고 `git -C {WIKI_ROOT} switch main` — 세션 주입과 다른 쓰기 스킬이 미승인 편집을 읽지 않게 함
- **보고**: push한 스킬은 "다음 세션 목록에 반영", update는 PR 링크와 "머지 후 다음 세션에 반영"
