---
name: init
description: Create the wiki skeleton if the configured remote is empty, then force-sync the read-only local wiki copy.
disable-model-invocation: true
---

`${CLAUDE_PLUGIN_ROOT}/config.json`의 `wiki` 값(`baseRoot`·`remote`·`baseBranch`)을 사용합니다. git 명령은 모두 `GIT_TERMINAL_PROMPT=0`을 붙여 실행합니다. `baseRoot`는 읽기 전용 사본이며 쓰기는 임시 clone에서 합니다.

## 1. 빈 원격 확인

원격에 `baseBranch`가 있는지 확인합니다.

```
git ls-remote --heads {remote} {baseBranch}
```

출력이 비면 2절, 있으면 3절로 갑니다.

## 2. 골격 생성

`mktemp -d`가 출력한 경로를 `{tmp}`로 쓰고, 임시 clone에서 골격을 커밋해 push합니다.

```
git clone {remote} {tmp}
bash ${CLAUDE_PLUGIN_ROOT}/scripts/write_skeleton.sh {tmp}
git -C {tmp} add -A
git -C {tmp} commit -m "chore(init): 위키 골격"
git -C {tmp} branch -M {baseBranch}
git -C {tmp} push -u origin {baseBranch}
rm -rf {tmp}
```

`write_skeleton.sh`가 종료 코드 1이면 기존 파일이 있다는 의미이므로 중단 후 보고합니다.

## 3. 위키 동기화

`baseRoot`를 clone하거나 원격 `baseBranch`로 강제 정리합니다.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sync_wiki.py {baseRoot} {remote} {baseBranch}
```

`fail`이면 원인을 보고하고 중단합니다.

## 4. 실패 처리

인증·네트워크 오류면 사용자가 `! git ls-remote {remote}`로 인증을 마친 뒤 다시 실행하도록 안내합니다. 그 밖의 실패는 해소하지 않고 원인만 보고합니다.

## 5. 보고

위키 경로, 수행 결과, `git -C {baseRoot} log -1 --oneline`을 보고합니다.
