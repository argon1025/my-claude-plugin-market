#!/usr/bin/env python3
# 위키 대상이 아닌 세션의 주입 블록(대상 아님 고지, 위키 문서 사용 규칙, 도메인 목록)을 출력한다.
# 인자는 baseRoot와 현재 프로젝트 표시 이름이며 registry.json의 도메인 description만 읽는다.
import json
import sys
from pathlib import Path

OVERVIEW = """# 위키 — 대상 외 프로젝트({label})

현재 프로젝트는 위키에 등록된 레포가 아니므로 이 프로젝트 전용 문서는 없습니다. 사용자가 아래 도메인의 서비스·기능·정책을 물으면 위키 문서를 근거로 답하고, 질문이 아래 도메인과 무관하면 위키를 읽지 않습니다.

- 질문에 맞는 도메인을 고른 뒤 그 도메인 문서 폴더를 하위 폴더까지 `^description:`으로 grep해 문서별 용도를 보고 맞는 문서를 읽으세요. 레포별 책임이 필요하면 `{base}/registry.json`에서 그 도메인의 `repos`를 봅니다.
- 문서끼리 다르면 한쪽을 고르지 말고 두 값을 함께 알리세요.
- 위키 폴더는 세션 시작마다 원격 기준으로 초기화되므로 직접 고치지 말고, 고쳐야 할 내용이 있으면 사용자에게 알리고 `/agent-wiki:add`로 반영을 제안하세요.

## 도메인

`{base}/knowledge/{{domain}}/` — 도메인 공유 문서, 하위 `{{slug}}/` 폴더는 레포 전용 문서

{rows}"""

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: generate_domain_overview.py <baseRoot> <label>")
    base = Path(sys.argv[1]).expanduser()
    domains = json.loads((base / "registry.json").read_text())["domains"]
    rows = [f"- {d}" + (f" — {g['description']}" if g.get("description") else "") for d, g in domains.items()]
    print(OVERVIEW.format(label=sys.argv[2], base=base, rows="\n".join(rows)))
