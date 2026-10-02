# 위키 PR 절차

update·add 스킬이 위키 원격 호스트와 주고받는 절차만 담습니다. 위키 원격 호스트를 바꾸면 이 파일만 고칩니다. 현재 절차는 GitHub `gh` CLI 기준이며, 명령은 모두 위키 clone `{tmp}`에서 실행합니다.

## 1. 열린 update PR

update만 확인합니다.

```
gh pr list --state open --json url,headRefName
```

`headRefName`이 `wiki-update/`로 시작하는 PR이 있으면 그 링크를 보고하고 중단합니다. 커서가 PR 머지 전까지 기준 브랜치에 없어 같은 머지를 두 번 추출하기 때문입니다. 명령이 실패해도 오류 한 줄을 보고하고 중단합니다.

## 2. 게시

`{branch}`는 스킬이 만든 `wiki-update/{YYYYMMDD-HHMM}` 또는 `wiki-add/{YYYYMMDD-HHMM}`이고, 제목은 update `update({domain}): {YYYY-MM-DD} 머지 {N}건 · 문서 {M}장`, add `add({domain}): {자료 대표 이름} · 문서 {M}장`입니다.

```
git -C {tmp} push -u origin {branch}
gh pr create --base {baseBranch} --head {branch} --title "{제목}" --body-file {work}/pr.md
```

본문이 60,000바이트를 넘으면 본문을 "사실 목록은 첫 코멘트" 한 줄로 바꿔 PR을 만든 뒤 `{work}/pr.md`를 코멘트로 올립니다.

```
gh pr comment {url} --body-file {work}/pr.md
```

실패하면 단계·브랜치 이름·오류 한 줄을 보고합니다.

## 3. update PR 읽기

add가 update PR의 `사실 목록` 표를 읽을 때 씁니다.

```
gh pr view {url} --json body,comments
```

본문에 표가 없으면 첫 코멘트의 표를 읽습니다.

## 4. 인증 실패

`gh` 인증 오류면 사용자가 `! gh auth login`을 마친 뒤 스킬을 다시 실행하도록 안내합니다.
