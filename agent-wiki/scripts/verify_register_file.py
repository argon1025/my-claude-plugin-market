#!/usr/bin/env python3
# register가 기록한 현재 레포 노드(registry.json)와 자기 간선 블록(deps.json)을 검증한다.
# 다른 노드·블록은 보지 않으며, 수정·커밋은 호출한 스킬이 맡는다.
import json
import sys
from pathlib import Path

NODE_KEYS = {"remote", "defaultBranch", "status", "stack", "summary", "responsibilities", "hosts"}
HOST_KEYS = {"qa", "stg", "prod"}


def text(v):
    return isinstance(v, str) and v.strip() != ""


def check(root, key):
    try:
        registry = json.loads((root / "registry.json").read_text())
        deps = json.loads((root / "deps.json").read_text())
    except (OSError, ValueError) as e:
        return [f"json: {e}"]
    domain, _, slug = key.partition("/")
    group = registry.get("domains", {}).get(domain)
    if not isinstance(group, dict):
        return [f"domain missing: {domain}"]
    errors = [] if text(group.get("description")) else [f"{domain}.description: empty"]
    node = group.get("repos", {}).get(slug)
    if not isinstance(node, dict):
        return errors + [f"node missing: {key}"]
    if node.keys() != NODE_KEYS:
        errors.append(f"{key}: missing {sorted(NODE_KEYS - node.keys())}, unknown {sorted(node.keys() - NODE_KEYS)}")
    errors += [f"{key}.{k}: empty" for k in ("remote", "defaultBranch", "summary") if k in node and not text(node[k])]
    if node.get("status") != "active":
        errors.append(f"{key}.status: must be active")
    errors += [f"{key}.{k}: must be non-empty string array" for k in ("stack", "responsibilities")
               if not (isinstance(node.get(k), list) and node[k] and all(text(x) for x in node[k]))]
    if not (isinstance(hosts := node.get("hosts"), dict) and all(h in HOST_KEYS and text(v) for h, v in hosts.items())):
        errors.append(f"{key}.hosts: keys qa/stg/prod with non-empty values")
    nodes = {f"{d}/{s}" for d, g in registry["domains"].items() for s in g.get("repos", {})}
    edges = deps.get("deps", {}).get(key, [])
    if not isinstance(edges, list) or key in deps.get("deps", {}) and not edges:
        return errors + [f"deps.{key}: must be non-empty array, delete the key when no edges"]
    seen = set()
    for i, e in enumerate(edges):
        if not isinstance(e, dict) or set(e) != {"to", "desc"} or not (text(e["to"]) and text(e["desc"])):
            errors.append(f"deps.{key}[{i}]: keys must be exactly to/desc with non-empty values")
            continue
        if e["to"] not in nodes or e["to"] == key or e["to"] in seen:
            errors.append(f"deps.{key}[{i}].to: {e['to']} unregistered, self or duplicate")
        seen.add(e["to"])
    return errors


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: verify_register_file.py <wiki-root> <domain>/<slug>")
    errs = check(Path(sys.argv[1]).expanduser(), sys.argv[2])
    if errs:
        sys.exit("\n".join(errs))
    print(f"ok {sys.argv[2]}")
