# 위키 PR 절차

update·add 스킬이 위키 원격 호스트와 주고받는 절차만 담습니다. 위키 원격 호스트를 바꾸면 이 파일만 고칩니다. 현재 절차는 GitHub `gh` CLI 기준이며, 명령은 모두 위키 clone `{tmp}`에서 실행합니다.

## 1. 열린 update PR

update는 시작할 때와 게시 직전에 확인합니다. 준비할 때 위키 clone의 전체 HEAD SHA를 `{base}`로 보관합니다. GitHub에서는 다음과 같이 열린 PR을 마지막 페이지까지 읽습니다. 명령이 실패하면 멈춥니다. 이전 실행 결과를 사용하지 않습니다.

```sh
gh api --paginate --slurp 'repos/{owner}/{repo}/pulls?state=open&per_page=100' --jq '{complete:true,pulls:[.[][] | {head:.head.ref,base:.base.ref,url:.html_url,sha:.head.sha}]}' > "{work}/open-prs.json"
git -C "{tmp}" fetch origin "refs/heads/{baseBranch}:refs/remotes/origin/{baseBranch}"
python3 "{PLUGIN_ROOT}/scripts/check_update_publication.py" --wiki "{tmp}" --base "{base}" --base-branch "{baseBranch}" --open-prs "{work}/open-prs.json"
```

게시 직전에는 같은 조회를 다시 하고 마지막 명령에 `--ready`를 붙입니다. 같은 기준 브랜치에 add 또는 수동 PR이 열려 있다면 그 판본의 실제 diff를 읽습니다. 같은 정책의 대상·조건·기존값·새값·원문 판본과 문서 이동을 이번 변경과 대조합니다. 해당 도메인을 건드리지 않았다면 변경 경로만 확인합니다. `{work}/compared.json`에 PR URL을 키로 `{"sha":"조회한 head SHA","overlap":false,"reason":"확인한 파일과 주장"}`을 적고 게시 직전 검사에 `--compared "{work}/compared.json"`을 넘깁니다. 중복되는 행은 `overlap:true`로 표시합니다. 일부만 중복되면 해당 주장과 이에 의존하는 커서를 빼고 남은 독립 변경을 다시 검토할 수 있습니다. 중복 결론을 적용하기 전에 PR 목록과 head를 새로 읽습니다. 판본이 바뀌거나 조회가 실패하면 게시하지 않습니다.

종료 코드 10이면 기존 PR 링크나 변경 없음 사유를 보고하고 종료합니다. 1이면 조회 오류 또는 판본 변경 사유를 보고하며 게시하지 않습니다. 호스트가 다르면 해당 호스트에서 전체 목록을 읽어 같은 `complete,pulls` 형식으로 넘깁니다.

## 2. 게시

`{branch}`는 스킬이 만든 `wiki-update/{domain}-{base 전체 SHA}` 또는 `wiki-add/{YYYYMMDD-HHMM}`이고, 제목은 update `update({domain}): {YYYY-MM-DD} 머지 {N}건 · 문서 {M}장`, add `add({domain}): {자료 대표 이름} · 문서 {M}장`입니다.

```
# update는 원격 브랜치가 없을 때만 생성한다. 같은 기준 판본의 동시 실행이 서로의 변경을 덮을 수 없다.
git -C {tmp} push --force-with-lease=refs/heads/{branch}: -u origin HEAD:refs/heads/{branch}
# add는 기존 고유 브랜치를 git push -u origin {branch}로 게시한다.
gh pr create --base {baseBranch} --head {branch} --title "{제목}" --body-file {work}/pr.md
```

같은 update 브랜치가 이미 존재하거나 PR 생성 응답만 유실됐으면 그 head의 열린 PR·기준 브랜치 반영 여부를 다시 조회합니다. 열린 PR은 링크를 반환하고, 이미 반영됐으면 변경 없음으로 종료합니다. push만 된 브랜치는 원격 커밋의 전체 트리와 기준 커밋이 이번 검토 결과와 일치할 때만 같은 head의 PR 생성을 재개합니다. 다르면 양쪽 판본을 보고하고 중단합니다. 다른 이름의 브랜치를 만들어 재게시하지 않습니다.

본문이 60,000바이트를 넘으면 본문을 "사실 목록은 첫 코멘트" 한 줄로 바꿔 PR을 만든 뒤 `{work}/pr.md`를 코멘트로 올립니다.

```
gh pr comment {url} --body-file {work}/pr.md
```

실패하면 단계·브랜치 이름·오류 한 줄을 보고합니다.

## 3. 인증 실패

`gh` 인증 오류면 사용자가 `! gh auth login`을 마친 뒤 스킬을 다시 실행하도록 안내합니다.
