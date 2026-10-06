#!/usr/bin/env python3
# 세션 주입의 문서 목록 블록(레포 전용 문서, 도메인 공유 문서 이름, 다른 도메인)을 출력하고, --full이면 색인용 문서별 description을 출력한다.
# 문서 행은 frontmatter의 description 한 줄만 읽고, 문서가 없는 블록은 제목째 생략한다.
import json
import sys
from pathlib import Path


def description(path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("description:"):
            return line[len("description:"):].strip().strip("\"'")
    return ""


def block(title, path_line, rows, note=""):
    return f"## {title}\n\n`{path_line}`{note}\n\n" + "\n".join(rows) if rows else ""


def doc_rows(folder):
    files = sorted(folder.glob("*.md")) if folder.is_dir() else []
    return [f"- {f.stem}" + (f" — {d}" if (d := description(f)) else "") for f in files if f.is_file()]


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--full"]
    if len(args) != 2:
        raise SystemExit("usage: generate_document_list.py <baseRoot> <domain>/<slug> [--full]")
    base = Path(args[0]).expanduser()
    domain, slug = args[1].split("/", 1)
    shared = doc_rows(base / "knowledge" / domain)
    shared_path, own_path = f"{base}/knowledge/{domain}/{{name}}.md", f"{base}/knowledge/{domain}/{slug}/{{name}}.md"
    own = block(f"{slug} 전용 문서", own_path, doc_rows(base / "knowledge" / domain / slug))
    if len(args) < len(sys.argv) - 1:
        blocks = [block("도메인 공유 문서", shared_path, shared), own]
    else:
        domains = json.loads((base / "registry.json").read_text())["domains"]
        others = [f"- {d}" + (f" — {g['description']}" if g.get("description") else "")
                  for d, g in domains.items() if d != domain]
        names = [r[2:].split(" — ", 1)[0] for r in shared]
        blocks = [
            own,
            block(f"도메인 공유 문서 {len(names)}개", shared_path, [", ".join(names)] if names else [],
                  " — 문서별 용도(description)는 색인 파일에 있음"),
            block("다른 도메인 문서", f"{base}/knowledge/{{domain}}/", others),
        ]
    print("\n\n".join(b for b in blocks if b))
