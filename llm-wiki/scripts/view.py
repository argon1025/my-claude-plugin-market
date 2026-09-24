#!/usr/bin/env python3
"""레포 의존 그래프 화면 — registry.json 노드와 deps.json 간선을 브라우저용 자기완결 HTML로 낸다.

`graph.py map/repo`는 텍스트 출력뿐이라 도메인 4개·레포 45개·간선 64건을 한눈에 보기 어렵다.
이 스크립트는 같은 로더(graph.load_registry·load_edges·load_paths)로 읽은 데이터를 화면용
JSON 하나로 바꿔 templates/graph.html 안에 인라인 삽입하고 `{wiki}/.local/graph.html`에 쓴다.

정적 HTML이 데이터를 fetch하는 방식은 쓰지 않는다 — `file://`에서는 fetch가 CORS로 막혀
매번 로컬 서버가 필요하다. 데이터가 수십 KB라 인라인 삽입이 부담 없다.

표준 라이브러리만 쓴다. scripts/의 다른 모듈처럼 pip 없는 맨 python3에서 돌아야 한다.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import graph

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "graph.html"
PLACEHOLDER = "/*__GRAPH_DATA__*/"
DEFAULT_OUT = Path(".local") / "graph.html"


def build_view(registry: dict, edges: list[dict], paths: dict, wiki: str = "") -> dict:
    """화면용 JSON. 노드 id는 graph.py의 endpoint 형식(`도메인/slug`)이라 간선 from/to와 바로 조인된다."""
    repos = []
    out_degree: dict[str, int] = {}
    in_degree: dict[str, int] = {}
    for edge in edges:
        out_degree[edge["from"]] = out_degree.get(edge["from"], 0) + 1
        in_degree[edge["to"]] = in_degree.get(edge["to"], 0) + 1

    for slug, info in sorted(registry["repos"].items()):
        domain = info["domain"]
        node_id = f"{domain}/{slug}"
        hosts = info.get("hosts") if isinstance(info.get("hosts"), dict) else {}
        repos.append({
            "id": node_id,
            "slug": slug,
            "domain": domain,
            "status": "dormant" if graph.is_dormant(info) else "active",
            "reason": str(info.get("reason") or ""),
            "summary": str(info.get("summary") or ""),
            "responsibilities": graph.text_list(info.get("responsibilities")),
            "stack": graph.text_list(info.get("stack")),
            "hosts": {env: str(url) for env, url in hosts.items() if isinstance(url, str) and url},
            "project": str(info.get("project") or ""),
            "remote": str(info.get("remote") or ""),
            "defaultBranch": str(info.get("defaultBranch") or ""),
            "local": paths.get(slug) if isinstance(paths.get(slug), str) else None,
            "outDegree": out_degree.get(node_id, 0),
            "inDegree": in_degree.get(node_id, 0),
        })

    domains = []
    for name in sorted(registry["domains"]):
        members = [repo for repo in repos if repo["domain"] == name]
        domains.append({
            "id": name,
            "description": str(registry["domains"][name].get("description") or ""),
            "repoCount": len(members),
            "dormantCount": sum(1 for repo in members if repo["status"] == "dormant"),
        })

    rows = []
    for index, edge in enumerate(edges):
        rows.append({
            "id": f"e{index}",
            "from": edge["from"],
            "to": edge["to"],
            "kind": str(edge.get("kind") or "?").strip(),
            "contracts": graph.text_list(edge.get("contracts")),
        })

    return {
        "generatedAt": date.today().isoformat(),
        "wiki": wiki,
        "domains": domains,
        "repos": repos,
        "edges": rows,
    }


def render_html(template: str, view: dict) -> str:
    """JSON을 `<script type="application/json">` 안에 넣는다. `</`만 이스케이프하면 스크립트가 조기 종료되지 않는다."""
    payload = json.dumps(view, ensure_ascii=False).replace("</", "<\\/")
    if PLACEHOLDER not in template:
        raise ValueError(f"템플릿에 자리 표시자 {PLACEHOLDER} 가 없음: {TEMPLATE}")
    return template.replace(PLACEHOLDER, payload, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description="레포 의존 그래프를 브라우저 HTML로 낸다")
    parser.add_argument("--wiki", default=graph.DEFAULT_WIKI, help="위키 루트 (기본값: %(default)s)")
    parser.add_argument("--out", metavar="PATH", help=f"출력 HTML 경로 (기본값: {{wiki}}/{DEFAULT_OUT})")
    parser.add_argument("--no-open", action="store_true", help="브라우저로 열지 않고 경로만 출력")
    args = parser.parse_args()

    wiki = Path(args.wiki).expanduser()
    view = build_view(graph.load_registry(wiki), graph.load_edges(wiki), graph.load_paths(wiki), str(wiki))
    html = render_html(TEMPLATE.read_text(encoding="utf-8"), view)

    out = Path(args.out).expanduser() if args.out else wiki / DEFAULT_OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(out)

    if not args.no_open and sys.platform == "darwin":
        subprocess.run(["open", str(out)], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
