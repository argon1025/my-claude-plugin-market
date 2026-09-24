#!/usr/bin/env python3
"""레인별 증거 인벤토리 — register 4레인 조사의 누락 대조용 분모를 낸다.

레인 에이전트는 자기 관용구를 판별한 뒤 자유롭게 탐색하므로 "무엇을 안 봤는지"를 스스로
말하지 못한다. 여기서 grep 그물로 같은 분모를 매번 같은 방식으로 만들고, 메인은 이 파일
집합에서 네 레인이 낸 `evidence` 파일 집합을 뺀 잔여만 재질의한다.

판정하지 않는다 — 어느 행이 간선인지, 상대가 누구인지는 정하지 않고 파일·줄·원문·힌트만
낸다. 그물은 오탐이 많고 거르는 것은 레인 에이전트의 일이다.

표준 라이브러리만 쓴다. graph.py와 같은 이유로 pip 없는 맨 python3에서 돈다.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

LANES = ("library", "http", "message", "data", "responsibilities")

SKIP_DIRS = {".git", "node_modules", "target", "build", "dist", ".next", "out", ".gradle",
             ".idea", ".venv", "venv", "__pycache__", ".mvn", "coverage", ".turbo"}
# 테스트 코드의 호출은 계약이 아니라 레인 에이전트가 근거로 대지 않으므로 분모에서도 뺀다.
TEST_PATH = re.compile(r"(^|/)(src/test|test|tests|__tests__)/|\.(test|spec)\.\w+$|\.min\.js$")

JAVA_EXT = {".java", ".kt"}
WEB_EXT = {".jsp", ".js", ".jsx", ".ts", ".tsx", ".html", ".htm", ".vue"}
CFG_EXT = {".yml", ".yaml", ".properties"}
BUILD_FILES = ("pom.xml", "build.gradle", "build.gradle.kts", "package.json",
               "pyproject.toml", "requirements.txt", "go.mod")

# --- 패턴 ---------------------------------------------------------------

FEIGN = re.compile(r"@FeignClient\s*\((?:[^()]|\([^()]*\))*\)", re.S)
MAPPING = re.compile(r"@(?P<m>Get|Post|Put|Delete|Patch|Request)Mapping\s*\((?P<body>(?:[^()]|\([^()]*\))*)\)", re.S)
CLASS_AHEAD = re.compile(r"^\s*(?:@\w+(?:\([^)]*\))?\s*)*(?:public|abstract|final|\s)*\s*(?:class|interface)\s")
URLLIT = re.compile(r"[\"'](https?://[^\"'\s<>]+)[\"']")
WEBCLIENT = re.compile(r"(WebClient\s*\.\s*(?:create|builder)|\.baseUrl\s*\(|"
                       r"restTemplate\s*\.\s*(?:exchange|getFor|postFor|put|delete)|"
                       r"UriComponentsBuilder\s*\.\s*fromHttpUrl|HttpClient\.newHttpClient|"
                       r"new\s+Request\.Builder|OkHttpClient)")
AJAX = re.compile(r"(\$\.ajax\s*\(|\$\.(?:get|post)\s*\(|location\.href\s*=|<form[^>]+action\s*=|"
                  r"<c:url\s+value\s*=|<iframe[^>]+src\s*=)", re.I)
JSFETCH = re.compile(r"(fetch\s*\(|axios\.create\s*\(|axios\.(?:get|post|put|delete)\s*\(|baseURL\s*[:=])")
ENVREF = re.compile(r"process\.env\.([A-Z0-9_]*(?:URL|HOST|API|ENDPOINT|BASE|ORIGIN)[A-Z0-9_]*)")
HTTP_BEAN = re.compile(r"<bean[^>]+class=\"[^\"]*(RestTemplate|HttpInvoker|WebServiceTemplate|HttpClient)[^\"]*\"|"
                       r"<int-http:outbound[^>]*>")
PROP = re.compile(r"^\s*([\w.\-\[\]]+)\s*[:=]\s*(\S.*)$", re.M)
HOSTISH = re.compile(r"^(https?://|[a-z0-9][\w\-]*\.[\w\-.]+\.[a-z]{2,})", re.I)
QUEUE_KEY = re.compile(r"(queue|exchange|routing-?key|topic|binding)", re.I)

LISTENER = re.compile(r"@(RabbitListener|KafkaListener|JmsListener|RabbitHandler)\b")
PUBLISH = re.compile(r"(convertAndSend|convertSendAndReceive|rabbitTemplate\s*\.\s*send|"
                     r"amqpTemplate\s*\.\s*\w+|kafkaTemplate\s*\.\s*send)\s*\(")
AMQP_XML = re.compile(r"<(rabbit:(?:listener-container|listener|queue|binding|topic-exchange|"
                      r"direct-exchange|fanout-exchange|template)|int-amqp:[\w-]+)[^>]*>")

JDBC = re.compile(r"(jdbc:[\w:]+://?[^\"'\s,;]+|mongodb(?:\+srv)?://[^\"'\s,;]+|redis://[^\"'\s,;]+)")
SQLFROM = re.compile(r"\b(?:FROM|JOIN|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+([A-Za-z_][\w$]*(?:\.[A-Za-z_][\w$]*)?)", re.I)
SQL_NOISE = {"SELECT", "DUAL", "SET", "WHERE", "VALUES", "AS", "ON"}
JPATABLE = re.compile(r"@(?:Table|SecondaryTable)\s*\(\s*(?:name\s*=\s*)?\"([^\"]+)\"")
ESDOC = re.compile(r"@Document\s*\([^)]*indexName\s*=\s*\"?([^\",)]+)\"?")

SCHED = re.compile(r"@Scheduled\s*\([^)]*\)")
BATCHBEAN = re.compile(r"\b(?:Job|Step|Tasklet)\s+(\w+)\s*\(")
RUNNER = re.compile(r"implements\s+(?:CommandLineRunner|ApplicationRunner)")
SERVLET = re.compile(r"<url-pattern>\s*([^<]+)\s*</url-pattern>")
NEXT_ROUTE = re.compile(r"(^|/)app/.*/(page|route)\.(tsx?|jsx?)$")
PUBLIC_TYPE = re.compile(r"public\s+(?:final\s+|abstract\s+)?(?:class|interface|enum|record)\s+(\w+)")
SURFACE_DIR = re.compile(r"src/main/java/.*/(api|client|dto|config|support)/")
AUTOCONF_FILES = ("spring.factories", "org.springframework.boot.autoconfigure.AutoConfiguration.imports")

# 호출이 아닌 URL — 네임스페이스·taglib·스키마·예시·주석
NOISE_HOST = re.compile(
    r"(^|\.)(w3\.org|java\.sun\.com|sun\.com|oracle\.com|springframework\.org|apache\.org|"
    r"mybatis\.org|jboss\.org|opensymphony\.com|xmlsoap\.org|jcp\.org|schema\.org|jquery\.com|"
    r"googleapis\.com|gstatic\.com|googletagmanager\.com|json-schema\.org|purl\.org|"
    r"example\.com|example\.org|example|localhost)$", re.I)
NOISE_LINE = re.compile(r"(<%@\s*taglib|xmlns(:\w+)?\s*=|xsi:schemaLocation|@see\s+http|DOCTYPE|"
                        r"<!--.*http|^\s*\*\s|//\s*https?://)", re.I)
TLD = re.compile(r"\.(kr|net|com|io|co|org|jp|us|cn|dev|shop|re|gov|services|cloud|app)$", re.I)


# --- 보조 ---------------------------------------------------------------


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def line_at(text: str, pos: int) -> str:
    return text.split("\n")[text.count("\n", 0, pos)]


def find_line(text: str, needle: str) -> int:
    index = text.find(needle)
    return line_of(text, index) if index >= 0 else 1


def noisy(url: str, line: str) -> bool:
    host = re.sub(r"^\w+://", "", url).split("/")[0].split("?")[0].split(":")[0].lower()
    return ("." not in host or bool(NOISE_HOST.search(host)) or not TLD.search(host)
            or bool(NOISE_LINE.search(line)))


def tag(node) -> str:
    """네임스페이스를 뗀 XML 태그 — pom.xml은 네임스페이스가 있기도 없기도 하다."""
    return node.tag.rsplit("}", 1)[-1]


class Rows:
    """레인별 행 모음. 같은 (레인, 파일, 줄)은 한 번만 담는다."""

    def __init__(self) -> None:
        self.lanes: dict[str, list[dict]] = {lane: [] for lane in LANES}
        self.seen: set[tuple[str, str, int]] = set()

    def add(self, lane: str, file: str, line: int, raw: str, hint: str) -> None:
        if (lane, file, line) in self.seen:
            return
        self.seen.add((lane, file, line))
        self.lanes[lane].append({"file": file, "line": line,
                                 "raw": re.sub(r"\s+", " ", raw).strip()[:300], "hint": hint})

    def hits(self, lane: str, file: str, text: str, pattern: re.Pattern, hint: str,
             whole: bool = False) -> None:
        """패턴이 걸린 줄마다 한 행. whole이면 매치 전체를, 아니면 그 줄을 원문으로."""
        for match in pattern.finditer(text):
            self.add(lane, file, line_of(text, match.start()),
                     match.group(0) if whole else line_at(text, match.start()), hint)


# --- 레인 ---------------------------------------------------------------


def scan_build(where: str, name: str, text: str, rows: Rows) -> None:
    """빌드 파일의 의존 좌표와 공개 표면. 멀티모듈·워크스페이스라 최상위 하나만 보지 않는다."""
    if name == "pom.xml":
        try:
            tree = ET.fromstring(text)
        except ET.ParseError:
            return
        for node in tree.iter():
            if tag(node) in ("dependency", "parent"):
                coord = {tag(child): (child.text or "").strip() for child in node}
                group, artifact = coord.get("groupId", ""), coord.get("artifactId", "")
                if group and artifact:
                    rows.add("library", where, find_line(text, f"<artifactId>{artifact}</artifactId>"),
                             f"{tag(node)} {group}:{artifact}", "maven")
    elif name == "package.json":
        try:
            package = json.loads(text)
        except json.JSONDecodeError:
            return
        for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
            for dep, version in (package.get(section) or {}).items():
                rows.add("library", where, find_line(text, f'"{dep}"'), f'{section} "{dep}": "{version}"', "npm")
        if package.get("exports") or package.get("main") or package.get("bin"):
            rows.add("responsibilities", where, 1, f"npm {package.get('name', '')} exports/main/bin", "surface")
    elif name == "requirements.txt":
        for number, line in enumerate(text.split("\n"), 1):
            if line.strip() and not line.startswith("#"):
                rows.add("library", where, number, line, "pip")


def scan_java(where: str, text: str, rows: Rows) -> None:
    rows.hits("http", where, text, FEIGN, "feign", whole=True)
    rows.hits("http", where, text, WEBCLIENT, "webclient")
    rows.hits("message", where, text, LISTENER, "listener")
    rows.hits("message", where, text, PUBLISH, "publish")
    rows.hits("data", where, text, JPATABLE, "jpa", whole=True)
    rows.hits("data", where, text, ESDOC, "es", whole=True)
    rows.hits("responsibilities", where, text, SCHED, "job")
    if "@Configuration" in text and re.search(r"\bJobBuilder|StepBuilder|JobRepository", text):
        rows.hits("responsibilities", where, text, BATCHBEAN, "job")
    if RUNNER.search(text):
        rows.add("responsibilities", where, find_line(text, "Runner"), "CommandLineRunner", "job")
    if SURFACE_DIR.search(where):
        types = PUBLIC_TYPE.findall(text)
        if types:
            rows.add("responsibilities", where, 1, "public types: " + ", ".join(types[:10]), "surface")
    if "@Controller" in text or "@RestController" in text:
        scan_routes(where, text, rows)


def scan_routes(where: str, text: str, rows: Rows) -> None:
    """클래스 매핑과 메서드 매핑을 결합한 완전 경로 — 조각만 보면 라우트가 서로 섞인다."""
    base = ""
    methods = []
    for match in MAPPING.finditer(text):
        if CLASS_AHEAD.match(text[match.end():match.end() + 400]):
            base = base or mapping_path(match.group("body"))
        else:
            methods.append(match)
    for match in methods:
        method = match.group("m").upper()
        if method == "REQUEST":
            found = re.search(r"method\s*=\s*\{?\s*(?:RequestMethod\.)?(\w+)", match.group("body"))
            method = found.group(1) if found else "ANY"
        full = (base + mapping_path(match.group("body"))).replace("//", "/") or "/"
        rows.add("responsibilities", where, line_of(text, match.start()), f"{method} {full}", "route")


def mapping_path(body: str) -> str:
    """매핑 애노테이션 본문의 경로 리터럴. `value=`·`path=`·생략형을 모두 본다."""
    for key in ("value", "path"):
        found = re.search(key + r"\s*=\s*(?:\"([^\"]*)\"|\{\s*\"([^\"]*)\")", body)
        if found:
            return found.group(1) or found.group(2) or ""
    if "=" in body.split("\"")[0]:
        return ""
    found = re.search(r"\"([^\"]*)\"", body)
    return found.group(1) if found else ""


def scan_web(where: str, text: str, rows: Rows) -> None:
    rows.hits("http", where, text, JSFETCH, "fetch")
    rows.hits("http", where, text, AJAX, "ajax")
    rows.hits("http", where, text, ENVREF, "env")
    if NEXT_ROUTE.search(where):
        segment = re.sub(r"\([^/)]+\)/?", "", re.sub(r"/(page|route)\.\w+$", "", re.sub(r"^.*?app/", "/", where)))
        rows.add("responsibilities", where, 1, f"route {segment or '/'}", "route")


def scan_xml(where: str, name: str, text: str, rows: Rows) -> None:
    rows.hits("http", where, text, HTTP_BEAN, "bean", whole=True)
    rows.hits("message", where, text, AMQP_XML, "amqp-xml", whole=True)
    if name == "web.xml":
        rows.hits("responsibilities", where, text, SERVLET, "servlet", whole=True)
    elif re.search(r"(mapper|sqlmap|ibatis)", where, re.I):
        tables = {item for item in SQLFROM.findall(text) if item.upper() not in SQL_NOISE}
        if tables:
            rows.add("data", where, 1, "tables: " + ", ".join(sorted(tables)[:20]), "sql")


def scan_config(where: str, text: str, rows: Rows) -> None:
    """설정의 호스트·큐 키. 프로퍼티 해석은 하지 않고 리터럴이 보이는 줄만 담는다."""
    for match in PROP.finditer(text):
        key, value = match.group(1), match.group(2).strip().strip("\"'")
        if QUEUE_KEY.search(key):
            if value not in ("{}", "[]"):
                rows.add("message", where, line_of(text, match.start()), match.group(0), "queue-prop")
        elif HOSTISH.match(value) and not noisy(value, match.group(0)):
            rows.add("http", where, line_of(text, match.start()), match.group(0), "prop")


def inventory(root: Path) -> dict:
    """한 번 걸으며 파일마다 확장자·이름에 맞는 레인 그물을 건다."""
    rows = Rows()
    builds: dict[str, int] = {}
    exts: dict[str, int] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [item for item in dirnames if item not in SKIP_DIRS]
        for name in filenames:
            path = Path(dirpath) / name
            where = str(path.relative_to(root))
            if TEST_PATH.search(where):
                continue
            suffix = path.suffix.lower()
            if name in BUILD_FILES:
                builds[name] = builds.get(name, 0) + 1
            if suffix in JAVA_EXT | WEB_EXT | {".py", ".go", ".sql"}:
                exts[suffix] = exts.get(suffix, 0) + 1
            if name not in BUILD_FILES and name not in AUTOCONF_FILES and name != "web.xml" \
                    and suffix not in JAVA_EXT | WEB_EXT | CFG_EXT | {".xml"}:
                continue
            try:
                if path.stat().st_size > 3_000_000:
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                continue

            if name in AUTOCONF_FILES:
                rows.add("responsibilities", where, 1, name, "surface")
            if name in BUILD_FILES:
                scan_build(where, name, text, rows)
                continue
            if suffix in JAVA_EXT | WEB_EXT | CFG_EXT | {".xml"}:
                rows.hits("data", where, text, JDBC, "jdbc")
                for match in URLLIT.finditer(text):
                    line = line_at(text, match.start())
                    if not noisy(match.group(1), line):
                        rows.add("http", where, line_of(text, match.start()), line, "url")
            if suffix in JAVA_EXT:
                scan_java(where, text, rows)
            elif suffix in WEB_EXT:
                scan_web(where, text, rows)
            elif suffix == ".xml":
                scan_xml(where, name, text, rows)
            elif suffix in CFG_EXT:
                scan_config(where, text, rows)

    top = sorted(exts.items(), key=lambda item: (-item[1], item[0]))[:5]
    hints = [f"{name} {count}개" for name, count in builds.items()] + [f"{ext} {count}파일" for ext, count in top]
    return {"lanes": rows.lanes, "stack_hint": hints}


# --- CLI ----------------------------------------------------------------


def cmd_inventory(args) -> int:
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"# {root} 없음", file=sys.stderr)
        return 1
    payload = inventory(root)
    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    lanes = payload["lanes"]
    files = {row["file"] for lane in LANES for row in lanes[lane]}
    print(f"# 인벤토리 {out} · " + " · ".join(f"{lane} {len(lanes[lane])}행" for lane in LANES)
          + f" · 파일 {len(files)}개 — 판정이 아니라 레인 evidence에 없는 파일의 재질의 분모")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="레포를 레인별로 훑어 register 조사의 누락 대조용 인벤토리를 낸다.")
    sub = parser.add_subparsers(dest="command", required=True)
    cmd = sub.add_parser("inventory", help="레인별 증거 행을 JSON 한 파일로 낸다")
    cmd.add_argument("--root", metavar="PATH", required=True, help="조사할 레포의 git toplevel")
    cmd.add_argument("--out", metavar="PATH", required=True, help="출력 JSON 경로")
    cmd.set_defaults(func=cmd_inventory)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
