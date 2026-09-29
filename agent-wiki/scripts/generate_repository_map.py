#!/usr/bin/env python3
# 세션 주입의 레포 지도 블록(같은 도메인 레포 전수와 책임, 의존 표식)을 출력한다.
# 표식은 deps.json의 그룹 키와 to만 읽으며, deps.json이 없거나 깨지면 표식 없이 출력한다.
import json
import sys
from pathlib import Path

HEAD = """## {domain} 도메인의 전체 레포지토리

`{ws}/{{slug}}`

작업 전 영향도·의존성·선행 작업 파악이 필요하면 해당 레포 코드를 직접 확인하세요. 의존 표식은 참고용이므로 책임만으로도 의존이 의심되면 코드로 확인합니다. 위 경로는 자유롭게 써도 되지만 다른 에이전트가 덮어쓸 수 있어 변경 사항이 사라질 수 있습니다. 폴더가 없으면 사용자의 로컬 체크아웃을 찾거나 `{base}/registry.json`의 remote를 clone해 쓰세요.
"""


def row(label, node, marks):
    text = " · ".join(node.get("responsibilities") or []) or node.get("summary") or ""
    return f"- {label}" + (f" ({', '.join(marks)})" if marks else "") + (f" — {text}" if text else "")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: generate_repository_map.py <baseRoot> <workspace.root> <domain>/<slug>")
    base, ws, cur = Path(sys.argv[1]).expanduser(), Path(sys.argv[2]).expanduser(), sys.argv[3]
    domain, slug = cur.split("/", 1)
    domains = json.loads((base / "registry.json").read_text())["domains"]
    try:
        deps = json.loads((base / "deps.json").read_text())["deps"]
        uses = {e["to"] for e in deps.get(cur, [])}
        used_by = {k for k, es in deps.items() if any(e["to"] == cur for e in es)}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        uses, used_by = set(), set()

    def marks(key):
        return [m for m, on in (("현재", key == cur), ("현재 레포가 의존", key in uses), ("현재 레포에 의존", key in used_by)) if on]

    lines = [HEAD.format(domain=domain, ws=ws, base=base)]
    lines += [row(s, n, marks(f"{domain}/{s}")) for s, n in domains[domain]["repos"].items()]
    for key in sorted((uses | used_by) - {cur}):
        d, _, s = key.partition("/")
        if d != domain and s in domains.get(d, {}).get("repos", {}):
            lines.append(row(key, domains[d]["repos"][s], marks(key)))
    print("\n".join(lines))
