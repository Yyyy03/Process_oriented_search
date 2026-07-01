#!/usr/bin/env python3
"""Search and triage open-source software that may run on HarmonyOS PC.

The radar searches multiple public sources, but final records still require
both open-source evidence and HarmonyOS PC executable/build evidence.
"""

from __future__ import annotations

import argparse
import base64
import csv
import datetime as dt
import html
import json
import os
import re
import sys
import textwrap
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import quote_plus, urljoin, urlparse

try:
    import requests
except ModuleNotFoundError:  # Allows --help and manual-link-only mode before dependency install.
    requests = None  # type: ignore[assignment]

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:  # The script still supports --help and dry runs before install.
    BeautifulSoup = None  # type: ignore[assignment]


GITHUB_API = "https://api.github.com"

OUTPUT_FIELDS = [
    "name",
    "category",
    "status",
    "score",
    "source",
    "repo_url",
    "market_url",
    "demo_url",
    "article_url",
    "license",
    "description",
    "tech_stack",
    "build_method",
    "install_method",
    "harmony_pc_evidence",
    "open_source_evidence",
    "risk",
    "recommendation",
    "last_checked",
]

AUDIT_FIELDS = [
    "name",
    "source",
    "discovery_query",
    "repo_url",
    "kept",
    "decision",
    "status",
    "score",
    "license",
    "description",
    "tech_stack",
    "build_method",
    "install_method",
    "harmony_pc_evidence",
    "open_source_evidence",
    "risk",
    "last_checked",
]

SOURCE_CANDIDATE_FIELDS = [
    "source",
    "query",
    "name",
    "repo_url",
    "market_url",
    "demo_url",
    "article_url",
    "source_url",
    "license",
    "description",
    "harmony_pc_evidence",
    "open_source_evidence",
    "risk",
    "decision",
]

ALL_SOURCES = ["github", "gitcode", "bilibili", "appgallery"]

DEFAULT_QUERIES = [
    "鸿蒙 PC 开源软件",
    "鸿蒙 PC 应用 开源",
    "鸿蒙 PC HAP",
    "鸿蒙 PC DevEco",
    "鸿蒙 PC ArkTS",
    "鸿蒙 PC Qt",
    "鸿蒙 PC Electron",
    "鸿蒙 PC 终端",
    "鸿蒙 PC Linux",
    "鸿蒙 PC 移植",
    "鸿蒙电脑 开源软件",
    "鸿蒙电脑 应用",
    "鸿蒙 PC Markdown",
    "鸿蒙 PC 笔记",
    "鸿蒙 PC 编辑器",
    "鸿蒙 PC 开发工具",
    "鸿蒙 PC Shell",
    "鸿蒙 PC 包管理器",
    "鸿蒙 PC 网络调试",
    "鸿蒙 PC SSH",
    "鸿蒙 PC Git",
    "鸿蒙 PC Rust",
    "鸿蒙 PC Go",
    "鸿蒙 PC C++",
    "鸿蒙 PC Flutter",
    "HarmonyOS PC open source app",
    "HarmonyOS Computer open source",
    "HarmonyOS Computer app",
    "HarmonyOS NEXT PC app",
    "OpenHarmony PC app",
    "OpenHarmony desktop app",
    "OpenHarmony PC software",
    "HarmonyOS HAP PC",
    "ArkTS desktop app",
    "ohos qt",
    "ohos electron",
    "ohos markdown",
    "ohos terminal",
    "HarmonyOS PC terminal",
    "HarmonyOS PC Qt",
    "HarmonyOS PC Electron",
    "HarmonyOS PC DevEco",
    "HarmonyOS PC hvigor",
    "HarmonyOS PC HAP",
    "HarmonyOS Computer terminal",
    "OpenHarmony PC Qt",
    "OpenHarmony PC Electron",
]

EXPANDED_GITHUB_QUERIES = [
    '"HarmonyOS PC"',
    '"HarmonyOS Computer"',
    '"HarmonyOS NEXT PC"',
    '"OpenHarmony PC"',
    '"OpenHarmony desktop"',
    '"鸿蒙 PC"',
    '"鸿蒙PC"',
    '"鸿蒙电脑"',
    '"鸿蒙桌面"',
    '"Qt for HarmonyOS"',
    '"Qt for OpenHarmony"',
    '"Electron for HarmonyOS"',
    '"Electron for OpenHarmony"',
    "HarmonyOS DevEco hvigor",
    "OpenHarmony DevEco hvigor",
    "HarmonyOS ArkTS desktop",
    "OpenHarmony ArkTS desktop",
    "HarmonyOS HAP PC",
    "OpenHarmony HAP PC",
    "ohos desktop",
    "ohos pc",
    "ohos qt",
    "ohos electron",
    "oh-package.json5 HarmonyOS",
    "hvigorfile HarmonyOS",
    "entry/src/main/ets HarmonyOS",
]

CODE_SEARCH_QUERIES = [
    '"HarmonyOS PC" in:file',
    '"HarmonyOS Computer" in:file',
    '"HarmonyOS NEXT PC" in:file',
    '"OpenHarmony PC" in:file',
    '"OpenHarmony desktop" in:file',
    '"鸿蒙 PC" in:file',
    '"鸿蒙PC" in:file',
    '"鸿蒙电脑" in:file',
    '"鸿蒙桌面" in:file',
    '"Qt for HarmonyOS" in:file',
    '"Qt for OpenHarmony" in:file',
    '"Electron for HarmonyOS" in:file',
    '"Electron for OpenHarmony" in:file',
    "filename:oh-package.json5 HarmonyOS",
    "filename:hvigorfile.ts HarmonyOS",
    "filename:module.json5 HarmonyOS",
    "filename:build-profile.json5 HarmonyOS",
]

PC_TERMS = [
    "harmonyos pc",
    "harmonyos_pc",
    "harmonyos-pc",
    "harmony os pc",
    "harmonyos computer",
    "harmonyos next pc",
    "openharmony pc",
    "openharmony_pc",
    "openharmony-pc",
    "openharmony desktop",
    "open harmony pc",
    "鸿蒙 pc",
    "鸿蒙pc",
    "鸿蒙电脑",
    "鸿蒙计算机",
    "鸿蒙 桌面",
    "鸿蒙桌面",
]

HARMONY_TERMS = [
    "harmonyos",
    "harmony os",
    "openharmony",
    "open harmony",
    "harmonyos next",
    "ohos",
    "鸿蒙",
    "开源鸿蒙",
]

BUILD_TERMS = {
    "DevEco": ["deveco", "dev eco"],
    "hvigor": ["hvigor", "hvigorfile"],
    "ArkTS": ["arkts", ".ets", "entry/src/main/ets"],
    "Stage Model": ["stage model", "abilitystage", "module.json5"],
    "Qt for HarmonyOS": ["qt for harmonyos", "qt for openharmony", "qml"],
    "Electron for HarmonyOS": ["electron for harmonyos", "electron for openharmony"],
    "qmake": ["qmake", ".pro"],
    "cmake": ["cmake", "cmakelists.txt"],
    "npm": ["package.json", "npm install", "npm run"],
    "cargo": ["cargo.toml", "cargo build"],
}

TECH_TERMS = {
    "ArkTS": ["arkts", ".ets", "entry/src/main/ets"],
    "Qt": ["qt", "qmake", ".pro", "qml"],
    "Electron": ["electron"],
    "C++": ["c++", "cpp", "cmake"],
    "Rust": ["rust", "cargo.toml"],
    "Go": ["golang", " go ", "go.mod"],
    "Flutter": ["flutter", "pubspec.yaml"],
    "WebView": ["webview"],
    "HAP": [".hap", "hap "],
}

DESKTOP_PORTING_TERMS = [
    "qt",
    "electron",
    "desktop",
    "pc",
    "computer",
    "terminal",
    "shell",
    "ssh",
    "markdown",
    "editor",
    "ide",
    "移植",
    "桌面",
    "终端",
]

DEMO_TERMS = [
    "bilibili",
    "b站",
    "video",
    "demo",
    "演示",
    "运行截图",
    "运行展示",
    "移植教程",
]

HIGH_PRIVILEGE_TERMS = [
    "root",
    "sudo",
    "system permission",
    "privileged",
    "高权限",
    "系统权限",
]

README_LOW_INFO_THRESHOLD = 240

LIBRARY_TOPICS = {
    "library",
    "sdk",
    "framework",
    "package",
    "component",
    "crate",
    "npm-package",
    "rust-crate",
}

LIBRARY_TEXT_PATTERNS = [
    r"\blibrary\b",
    r"\bsdk\b",
    r"\bframework\b",
    r"\bcomponent\b",
    r"\bcrate\b",
    r"\bplugin\b",
    r"组件库",
    r"工具包",
    r"依赖库",
    r"sdk for",
    r"a library",
    r"an sdk",
]

STAR_BONUS_TIERS = [
    (10000, 12),
    (1000, 8),
    (100, 4),
    (10, 1),
]

PORTING_TEXT_TERMS = [
    "移植",
    "适配",
    "adaptation",
    "for harmonyos",
    "for openharmony",
    "鸿蒙版",
    "harmonyos port",
]

DESKTOP_APP_CATEGORIES = {
    "终端与运行环境",
    "开发工具",
    "桌面软件移植项目",
    "原生鸿蒙 PC 应用",
    "普通桌面应用",
}


class RadarError(RuntimeError):
    """A user-facing error raised by the radar."""


@dataclass
class ProjectRecord:
    name: str
    category: str
    status: str
    score: int
    source: str
    repo_url: str
    market_url: str = ""
    demo_url: str = ""
    article_url: str = ""
    license: str = ""
    description: str = ""
    tech_stack: str = ""
    build_method: str = ""
    install_method: str = ""
    harmony_pc_evidence: List[str] = field(default_factory=list)
    open_source_evidence: List[str] = field(default_factory=list)
    risk: List[str] = field(default_factory=list)
    recommendation: str = ""
    last_checked: str = ""


@dataclass
class CandidateAudit:
    name: str
    source: str
    discovery_query: str
    repo_url: str
    kept: bool
    decision: str
    status: str = ""
    score: int = 0
    license: str = ""
    description: str = ""
    tech_stack: str = ""
    build_method: str = ""
    install_method: str = ""
    harmony_pc_evidence: List[str] = field(default_factory=list)
    open_source_evidence: List[str] = field(default_factory=list)
    risk: List[str] = field(default_factory=list)
    last_checked: str = ""


@dataclass
class SourceCandidate:
    source: str
    query: str
    name: str
    source_url: str
    repo_url: str = ""
    market_url: str = ""
    demo_url: str = ""
    article_url: str = ""
    license: str = ""
    description: str = ""
    page_text: str = ""
    stars: int = 0
    harmony_pc_evidence: List[str] = field(default_factory=list)
    open_source_evidence: List[str] = field(default_factory=list)
    risk: List[str] = field(default_factory=list)
    decision: str = "raw"


@dataclass
class RepoBundle:
    item: Dict[str, Any]
    readme: str
    license_name: str
    releases: List[Dict[str, Any]]
    paths: List[str]


class GitHubClient:
    def __init__(self, token: Optional[str] = None, timeout: int = 20) -> None:
        if requests is None:
            raise RadarError("Missing dependency: requests. Run `pip install -r requirements.txt` first.")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "User-Agent": "harmony-pc-oss-radar/1.0",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def get_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            raise RadarError(f"GitHub request failed: {exc}") from exc

        if response.status_code == 403:
            remaining = response.headers.get("X-RateLimit-Remaining")
            reset_at = response.headers.get("X-RateLimit-Reset")
            hint = "GitHub API limit reached. Set GITHUB_TOKEN in .env or reduce --max-results."
            if remaining == "0" and reset_at:
                hint += f" Rate limit reset timestamp: {reset_at}."
            raise RadarError(hint)

        if response.status_code == 404:
            return None

        if response.status_code >= 400:
            snippet = response.text[:300].replace("\n", " ")
            raise RadarError(f"GitHub API returned {response.status_code}: {snippet}")

        return response.json()

    def search_repositories(
        self, query: str, max_results: int, since: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if max_results <= 0:
            return []

        q = f"{query} in:name,description,readme"
        if since:
            q += f" pushed:>={since}"

        results: List[Dict[str, Any]] = []
        per_page = min(100, max_results)
        max_pages = (max_results + per_page - 1) // per_page

        for page in range(1, max_pages + 1):
            payload = self.get_json(
                f"{GITHUB_API}/search/repositories",
                params={
                    "q": q,
                    "sort": "updated",
                    "order": "desc",
                    "per_page": per_page,
                    "page": page,
                },
            )
            if not payload:
                break
            items = payload.get("items", [])
            results.extend(items)
            if len(items) < per_page or len(results) >= max_results:
                break
        return results[:max_results]

    def search_code(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        if max_results <= 0:
            return []

        results: List[Dict[str, Any]] = []
        per_page = min(100, max_results)
        max_pages = (max_results + per_page - 1) // per_page

        for page in range(1, max_pages + 1):
            payload = self.get_json(
                f"{GITHUB_API}/search/code",
                params={
                    "q": query,
                    "sort": "indexed",
                    "order": "desc",
                    "per_page": per_page,
                    "page": page,
                },
            )
            if not payload:
                break
            items = payload.get("items", [])
            results.extend(items)
            if len(items) < per_page or len(results) >= max_results:
                break
        return results[:max_results]

    def fetch_bundle(self, item: Dict[str, Any]) -> RepoBundle:
        full_name = item["full_name"]
        default_branch = item.get("default_branch") or "main"
        readme = self.fetch_readme(full_name)
        license_name = self.fetch_license_name(item, full_name)
        releases = self.fetch_releases(full_name)
        paths = self.fetch_tree_paths(full_name, default_branch)
        return RepoBundle(
            item=item,
            readme=readme,
            license_name=license_name,
            releases=releases,
            paths=paths,
        )

    def fetch_readme(self, full_name: str) -> str:
        payload = self.get_json(f"{GITHUB_API}/repos/{full_name}/readme")
        if not payload:
            return ""
        content = payload.get("content")
        if not content:
            return ""
        try:
            raw = base64.b64decode(content).decode("utf-8", errors="replace")
        except (ValueError, TypeError):
            return ""
        return raw

    def fetch_license_name(self, item: Dict[str, Any], full_name: str) -> str:
        license_obj = item.get("license") or {}
        spdx = license_obj.get("spdx_id") or ""
        if spdx and spdx != "NOASSERTION":
            return spdx

        payload = self.get_json(f"{GITHUB_API}/repos/{full_name}/license")
        if not payload:
            return ""
        license_payload = payload.get("license") or {}
        spdx = license_payload.get("spdx_id") or ""
        if spdx and spdx != "NOASSERTION":
            return spdx
        return license_payload.get("name") or ""

    def fetch_releases(self, full_name: str) -> List[Dict[str, Any]]:
        payload = self.get_json(
            f"{GITHUB_API}/repos/{full_name}/releases", params={"per_page": 5}
        )
        if isinstance(payload, list):
            return payload
        return []

    def fetch_tree_paths(self, full_name: str, branch: str) -> List[str]:
        payload = self.get_json(
            f"{GITHUB_API}/repos/{full_name}/git/trees/{branch}",
            params={"recursive": "1"},
        )
        if not payload or not isinstance(payload.get("tree"), list):
            return []
        paths = []
        for entry in payload["tree"]:
            path = entry.get("path")
            if path:
                paths.append(path)
        return paths[:5000]


class WebClient:
    def __init__(self, timeout: int = 20) -> None:
        if requests is None:
            raise RadarError("Missing dependency: requests. Run `pip install -r requirements.txt` first.")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0 Safari/537.36 harmony-pc-oss-radar/1.0"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
        )

    def fetch_text(self, url: str) -> str:
        try:
            response = self.session.get(url, timeout=self.timeout)
        except requests.RequestException as exc:
            raise RadarError(f"Web request failed for {url}: {exc}") from exc
        if response.status_code >= 400:
            raise RadarError(f"Web request returned {response.status_code} for {url}")
        response.encoding = response.encoding or "utf-8"
        return response.text

    def fetch_json(self, url: str, referer: str = "") -> Any:
        headers = {"Accept": "application/json,text/plain,*/*"}
        if referer:
            headers["Referer"] = referer
        try:
            response = self.session.get(url, headers=headers, timeout=self.timeout)
        except requests.RequestException as exc:
            raise RadarError(f"Web JSON request failed for {url}: {exc}") from exc
        if response.status_code >= 400:
            raise RadarError(f"Web JSON request returned {response.status_code} for {url}")
        try:
            return response.json()
        except ValueError as exc:
            raise RadarError(f"Web JSON request returned non-JSON for {url}") from exc


def dedupe_preserve_order(values: Iterable[str]) -> List[str]:
    seen = set()
    output = []
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(normalized)
    return output


def load_env_file(path: Path) -> Dict[str, str]:
    """Load simple KEY=value pairs from a .env file without extra dependencies."""
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    if not path.is_file():
        raise RadarError(f"Env file path is not a file: {path}")

    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        raise RadarError(f"Failed to read env file {path}: {exc}") from exc

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            print(f"[radar] skip malformed .env line {line_number}: missing '='", file=sys.stderr)
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            print(f"[radar] skip malformed .env line {line_number}: invalid key", file=sys.stderr)
            continue
        values[key] = strip_env_value(value.strip())
    return values


def strip_env_value(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    return value


def resolve_github_token(cli_token: str, env_file: Path) -> str:
    if cli_token:
        return cli_token
    if os.environ.get("GITHUB_TOKEN"):
        return os.environ["GITHUB_TOKEN"]
    env_values = load_env_file(env_file)
    return env_values.get("GITHUB_TOKEN", "")


def build_query_plan(user_queries: Optional[Sequence[str]], search_profile: str) -> List[str]:
    base_queries = list(user_queries or DEFAULT_QUERIES)
    if search_profile == "expanded":
        base_queries = base_queries + DEFAULT_QUERIES + EXPANDED_GITHUB_QUERIES
    return dedupe_preserve_order(base_queries)


def build_code_search_plan(user_queries: Sequence[str], search_profile: str) -> List[str]:
    if search_profile == "expanded":
        return dedupe_preserve_order(CODE_SEARCH_QUERIES)
    phrase_queries = []
    for query in user_queries:
        query = query.strip()
        if not query:
            continue
        if query.startswith('"') and query.endswith('"'):
            phrase_queries.append(f"{query} in:file")
        elif contains_any(query, PC_TERMS):
            phrase_queries.append(f'"{query}" in:file')
    return dedupe_preserve_order(phrase_queries)


def parse_sources(value: str) -> List[str]:
    if not value or value.lower() == "all":
        return list(ALL_SOURCES)
    sources = [item.strip().lower() for item in value.split(",") if item.strip()]
    invalid = [source for source in sources if source not in ALL_SOURCES]
    if invalid:
        raise argparse.ArgumentTypeError(f"Unknown source(s): {', '.join(invalid)}")
    return dedupe_preserve_order(sources)


def html_to_text(markup: str) -> str:
    if not markup:
        return ""
    if BeautifulSoup is not None:
        soup = BeautifulSoup(markup, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return normalize_whitespace(soup.get_text(" "))
    no_script = re.sub(r"<(script|style|noscript)\b.*?</\1>", " ", markup, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", no_script)
    return normalize_whitespace(html.unescape(text))


def html_title(markup: str) -> str:
    if not markup:
        return ""
    if BeautifulSoup is not None:
        soup = BeautifulSoup(markup, "html.parser")
        if soup.title and soup.title.string:
            return normalize_whitespace(soup.title.string)
        heading = soup.find(["h1", "h2"])
        if heading:
            return normalize_whitespace(heading.get_text(" "))
    match = re.search(r"<title[^>]*>(.*?)</title>", markup, flags=re.I | re.S)
    return normalize_whitespace(html.unescape(match.group(1))) if match else ""


def extract_links(markup: str, base_url: str) -> List[Tuple[str, str]]:
    links: List[Tuple[str, str]] = []
    if not markup:
        return links
    if BeautifulSoup is not None:
        soup = BeautifulSoup(markup, "html.parser")
        for anchor in soup.find_all("a", href=True):
            href = urljoin(base_url, anchor.get("href", ""))
            label = normalize_whitespace(anchor.get_text(" "))
            links.append((href, label))
        return links

    for match in re.finditer(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", markup, flags=re.I | re.S):
        href = urljoin(base_url, html.unescape(match.group(1)))
        label = normalize_whitespace(re.sub(r"<[^>]+>", " ", html.unescape(match.group(2))))
        links.append((href, label))
    return links


def normalize_url(url: str) -> str:
    return html.unescape(url or "").strip().rstrip(".,;，。；)")


def normalize_repo_url(url: str) -> str:
    url = normalize_url(url)
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    parts = [part for part in parsed.path.split("/") if part]
    if host.endswith("github.com") and len(parts) >= 2:
        return f"https://github.com/{parts[0]}/{parts[1]}"
    if host.endswith("gitcode.com") and len(parts) >= 2:
        if parts[0] in {"search", "explore", "codechina"}:
            return ""
        return f"https://gitcode.com/{parts[0]}/{parts[1]}"
    if host.endswith("gitee.com") and len(parts) >= 2:
        return f"https://gitee.com/{parts[0]}/{parts[1]}"
    return ""


def extract_repo_urls(text: str) -> List[str]:
    if not text:
        return []
    patterns = [
        r"https?://(?:www\.)?github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[^\s<>'\")\]]*)?",
        r"https?://(?:www\.)?gitcode\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[^\s<>'\")\]]*)?",
        r"https?://(?:www\.)?gitee\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[^\s<>'\")\]]*)?",
    ]
    urls: List[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            repo_url = normalize_repo_url(match.group(0))
            if repo_url:
                urls.append(repo_url)
    return dedupe_preserve_order(urls)


def detect_license_from_text(text: str) -> str:
    license_patterns = [
        ("Apache-2.0", r"\bApache(?: License)? 2\.0\b|\bApache-2\.0\b"),
        ("MIT", r"\bMIT License\b|\bMIT\b"),
        ("GPL-3.0", r"\bGPL-?3(?:\.0)?\b|\bGNU General Public License v3\b"),
        ("GPL-2.0", r"\bGPL-?2(?:\.0)?\b|\bGNU General Public License v2\b"),
        ("AGPL-3.0", r"\bAGPL-?3(?:\.0)?\b"),
        ("LGPL", r"\bLGPL\b"),
        ("MulanPSL-2.0", r"\bMulanPSL-?2\.0\b|木兰宽松许可证"),
        ("BSD", r"\bBSD(?:-Clause)?\b"),
    ]
    for name, pattern in license_patterns:
        if re.search(pattern, text or "", flags=re.I):
            return name
    return ""


def infer_name_from_url(url: str) -> str:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    if parts:
        return parts[-1]
    return parsed.netloc or url


def find_first_repo_url(candidate: SourceCandidate) -> str:
    if candidate.repo_url:
        return candidate.repo_url
    text = "\n".join([candidate.description, candidate.page_text, candidate.source_url])
    urls = extract_repo_urls(text)
    return urls[0] if urls else ""


def contains_any(text: str, terms: Sequence[str]) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in terms)


def find_terms(text: str, terms: Sequence[str]) -> List[str]:
    lower = text.lower()
    return [term for term in terms if term.lower() in lower]


def compact_text(parts: Iterable[str]) -> str:
    return "\n".join(part for part in parts if part)


def release_asset_names(releases: Sequence[Dict[str, Any]]) -> List[str]:
    names = []
    for release in releases:
        for asset in release.get("assets", []) or []:
            name = asset.get("name")
            if name:
                names.append(name)
    return names


def release_urls(releases: Sequence[Dict[str, Any]]) -> List[str]:
    urls = []
    for release in releases:
        url = release.get("html_url")
        if url:
            urls.append(url)
    return urls


def detect_tech_stack(text: str, paths: Sequence[str], language: str) -> List[str]:
    haystack = (text + "\n" + "\n".join(paths)).lower()
    stack = []
    for tech, terms in TECH_TERMS.items():
        if any(term.lower() in haystack for term in terms):
            stack.append(tech)
    if language:
        language_clean = language.strip()
        if language_clean and language_clean not in stack:
            stack.append(language_clean)
    return dedupe_preserve_order(stack)


def detect_build_methods(text: str, paths: Sequence[str]) -> List[str]:
    haystack = (text + "\n" + "\n".join(paths)).lower()
    methods = []
    for method, terms in BUILD_TERMS.items():
        if any(term.lower() in haystack for term in terms):
            methods.append(method)
    return dedupe_preserve_order(methods)


def detect_install_methods(text: str, releases: Sequence[Dict[str, Any]]) -> List[str]:
    methods = []
    assets = release_asset_names(releases)
    lower = (text + "\n" + "\n".join(assets)).lower()
    if ".hap" in lower or re.search(r"\bhap\b", lower):
        methods.append("HAP")
    if releases:
        methods.append("Release")
    if contains_any(lower, ["appgallery", "应用市场", "华为应用市场"]):
        methods.append("应用市场")
    if contains_any(lower, ["source build", "源码编译", "build from source"]):
        methods.append("源码编译")
    return dedupe_preserve_order(methods)


def classify_category(text: str, tech_stack: Sequence[str]) -> str:
    lower = text.lower()
    if contains_any(lower, ["terminal", "shell", "ssh", "termux", "终端", "命令行"]):
        return "终端与运行环境"
    if contains_any(lower, ["ide", "editor", "markdown", "git client", "开发工具", "编辑器"]):
        return "开发工具"
    if any(tech in tech_stack for tech in ["Qt", "Electron", "Flutter", "Rust", "Go", "C++"]):
        return "桌面软件移植项目"
    if any(tech in tech_stack for tech in ["ArkTS", "HAP"]):
        return "原生鸿蒙 PC 应用"
    if contains_any(lower, ["note", "music", "video", "file manager", "clipboard", "screenshot", "笔记", "音乐", "视频", "文件"]):
        return "普通桌面应用"
    return "未分类桌面应用"


def repository_is_recent(updated_at: str, now: dt.datetime) -> bool:
    try:
        updated = dt.datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    return updated >= now - dt.timedelta(days=365)


def has_harmony_pc_signal(
    combined_text: str, paths: Sequence[str], releases: Sequence[Dict[str, Any]]
) -> Tuple[bool, List[str]]:
    evidence = []
    pc_matches = find_terms(combined_text, PC_TERMS)
    for term in pc_matches[:6]:
        evidence.append(f"文本明确命中鸿蒙 PC 关键词: {term}")

    assets = release_asset_names(releases)
    path_text = "\n".join(paths).lower()
    asset_text = "\n".join(assets).lower()
    lower = combined_text.lower()

    has_harmony = contains_any(lower, HARMONY_TERMS) or contains_any(path_text, ["ohos", "harmony"])
    has_desktop_port = contains_any(lower + "\n" + path_text, DESKTOP_PORTING_TERMS)
    has_build = bool(detect_build_methods(combined_text, paths))
    has_hap = ".hap" in asset_text or ".hap" in lower or re.search(r"\bhap\b", lower)

    if has_hap:
        evidence.append("发现 HAP 安装包或 HAP 安装线索")

    build_methods = detect_build_methods(combined_text, paths)
    if build_methods:
        evidence.append(f"发现鸿蒙相关构建/工程线索: {', '.join(build_methods)}")

    if contains_any(lower, ["qt for harmonyos", "qt for openharmony", "electron for harmonyos", "electron for openharmony"]):
        evidence.append("发现 Qt/Electron for HarmonyOS/OpenHarmony 构建说明")

    explicit_pc = bool(pc_matches)
    porting_pc_like = has_harmony and has_desktop_port and (has_build or has_hap)
    return explicit_pc or porting_pc_like, dedupe_preserve_order(evidence)


def status_for_record(combined_text: str, evidence: Sequence[str], releases: Sequence[Dict[str, Any]]) -> str:
    lower = combined_text.lower()
    explicit_pc = contains_any(lower, PC_TERMS)
    has_release = bool(releases)
    has_hap = ".hap" in lower or any(name.lower().endswith(".hap") for name in release_asset_names(releases))
    has_demo = contains_any(lower, DEMO_TERMS)
    has_build = any("构建/工程线索" in item or "构建说明" in item for item in evidence)

    if explicit_pc and (has_release or has_hap or has_build or has_demo):
        return "confirmed"
    if has_demo and explicit_pc:
        return "ported-demo"
    return "buildable"


def has_porting_signal(combined_text: str) -> bool:
    lower = combined_text.lower()
    if any(term in lower for term in PORTING_TEXT_TERMS):
        return True
    return bool(re.search(r"\bport\b", lower))


def popularity_bonus(stars: int) -> int:
    for threshold, bonus in STAR_BONUS_TIERS:
        if stars >= threshold:
            return bonus
    return 0


def harmony_port_bonus(combined_text: str, category: str) -> int:
    if category in DESKTOP_APP_CATEGORIES and has_porting_signal(combined_text):
        return 8
    return 0


def is_library_or_package(
    name: str,
    description: str,
    topics: Sequence[str],
    has_release: bool,
    has_hap: bool,
    has_market: bool,
    install_methods: Sequence[str],
    category: str,
) -> Tuple[bool, str]:
    """Conservatively detect pure libraries/SDKs/packages/frameworks.

    Scans the repo name + one-line description (NOT the full README) for library
    signals, plus author-curated topics. Borderline cases (library signal but
    also a runnable artifact) return (False, "borderline-library") so the caller
    can apply a penalty instead of filtering.
    """
    headline = (name + "\n" + description).lower()
    topic_hit = any(str(t).strip().lower() in LIBRARY_TOPICS for t in topics)
    text_hit = any(re.search(pat, headline) for pat in LIBRARY_TEXT_PATTERNS)
    if not (topic_hit or text_hit):
        return False, ""
    has_runnable = (
        has_release
        or has_hap
        or has_market
        or bool(install_methods)
        or (category and category != "未分类桌面应用")
    )
    if has_runnable:
        return False, "borderline-library"
    return True, "filtered: library/SDK/package/framework (no runnable artifact)"


def score_record(
    bundle: RepoBundle,
    combined_text: str,
    tech_stack: Sequence[str],
    build_methods: Sequence[str],
    harmony_evidence: Sequence[str],
    risks: List[str],
    now: dt.datetime,
    category: str = "",
    library_borderline: bool = False,
) -> int:
    score = 0
    explicit_pc = contains_any(combined_text, PC_TERMS)
    has_license = bool(bundle.license_name)
    has_release = bool(bundle.releases)
    has_hap = ".hap" in combined_text.lower() or any(
        name.lower().endswith(".hap") for name in release_asset_names(bundle.releases)
    )
    has_demo = contains_any(combined_text, DEMO_TERMS)
    has_source = bool(bundle.item.get("html_url"))
    is_recent = repository_is_recent(bundle.item.get("updated_at", ""), now)

    if explicit_pc:
        score += 25
    if has_source:
        score += 20
    if has_license:
        score += 10
    if has_hap or has_release:
        score += 15
    if build_methods:
        score += 10
    if has_demo:
        score += 10
    if is_recent:
        score += 5
    if set(tech_stack) & {"ArkTS", "Qt", "Electron", "C++", "Rust", "Go", "Flutter", "HAP"}:
        score += 5

    if not has_license:
        score -= 10
        risks.append("License 不明确")
    if has_demo and not contains_any(combined_text, ["harmonyos", "openharmony", "ohos", "鸿蒙"]):
        score -= 15
        risks.append("只有演示线索，缺少鸿蒙适配源码证据")
    if not explicit_pc:
        score -= 10
        risks.append("缺少明确 PC 运行证据")
    if not build_methods and not has_release and not has_hap:
        score -= 10
        risks.append("构建步骤不完整")
    if contains_any(combined_text, HIGH_PRIVILEGE_TERMS):
        score -= 15
        risks.append("可能依赖高权限或系统能力")
    if not is_recent:
        score -= 10
        risks.append("最近 12 个月可能未维护")
    if len(bundle.readme.strip()) < README_LOW_INFO_THRESHOLD:
        score -= 10
        risks.append("README 信息较少")

    stars = int(bundle.item.get("stargazers_count") or 0)
    score += popularity_bonus(stars)
    score += harmony_port_bonus(combined_text, category)
    if library_borderline:
        score -= 8
        risks.append("疑似库/SDK但含可执行产物,保留并降分")

    if not harmony_evidence:
        score = min(score, 39)

    return max(0, min(100, score))


def recommendation_for_score(score: int) -> str:
    if score >= 80:
        return "优先验证"
    if score >= 60:
        return "值得关注"
    if score >= 40:
        return "候选观察"
    return "过滤"


def analyze_bundle(bundle: RepoBundle, now: dt.datetime) -> Optional[ProjectRecord]:
    item = bundle.item
    repo_url = item.get("html_url", "")
    language = item.get("language") or ""
    description = item.get("description") or ""
    topics = " ".join(item.get("topics") or [])
    paths = bundle.paths
    releases = bundle.releases
    release_links = release_urls(releases)
    assets = release_asset_names(releases)

    combined_text = compact_text(
        [
            item.get("name", ""),
            description,
            topics,
            bundle.readme,
            "\n".join(paths),
            "\n".join(assets),
        ]
    )

    open_source_evidence = [f"公开源码仓库: {repo_url}"]
    if bundle.license_name:
        open_source_evidence.append(f"LICENSE: {bundle.license_name}")
    if bundle.readme:
        open_source_evidence.append("README 可访问")
    if paths:
        open_source_evidence.append("源码目录结构可访问")
    if release_links:
        open_source_evidence.append("Release 页面可访问: " + release_links[0])

    has_harmony_pc, harmony_evidence = has_harmony_pc_signal(combined_text, paths, releases)
    if not repo_url or not open_source_evidence or not has_harmony_pc:
        return None

    tech_stack = detect_tech_stack(combined_text, paths, language)
    build_methods = detect_build_methods(combined_text, paths)
    install_methods = detect_install_methods(combined_text, releases)
    risks: List[str] = []
    score = score_record(
        bundle,
        combined_text,
        tech_stack,
        build_methods,
        harmony_evidence,
        risks,
        now,
    )
    if score < 40:
        return None

    category = classify_category(combined_text, tech_stack)
    status = status_for_record(combined_text, harmony_evidence, releases)

    return ProjectRecord(
        name=item.get("full_name") or item.get("name", ""),
        category=category,
        status=status,
        score=score,
        source="GitHub",
        repo_url=repo_url,
        market_url="",
        demo_url=extract_first_url(bundle.readme, ["bilibili.com", "b23.tv", "youtube.com", "youtu.be"]),
        article_url=extract_first_url(bundle.readme, ["csdn.net", "juejin.cn", "zhihu.com", "ost.51cto.com"]),
        license=bundle.license_name or "License 不明确",
        description=normalize_whitespace(description)[:500],
        tech_stack=", ".join(tech_stack),
        build_method=", ".join(build_methods),
        install_method=", ".join(install_methods),
        harmony_pc_evidence=harmony_evidence,
        open_source_evidence=open_source_evidence,
        risk=dedupe_preserve_order(risks),
        recommendation=recommendation_for_score(score),
        last_checked=now.date().isoformat(),
    )


def analyze_bundle_with_audit(
    bundle: RepoBundle,
    now: dt.datetime,
    source: str,
    discovery_query: str,
) -> Tuple[Optional[ProjectRecord], CandidateAudit]:
    item = bundle.item
    repo_url = item.get("html_url", "")
    language = item.get("language") or ""
    description = item.get("description") or ""
    topics = " ".join(item.get("topics") or [])
    paths = bundle.paths
    releases = bundle.releases
    release_links = release_urls(releases)
    assets = release_asset_names(releases)
    name = item.get("full_name") or item.get("name", "")
    last_checked = now.date().isoformat()

    combined_text = compact_text(
        [
            item.get("name", ""),
            description,
            topics,
            bundle.readme,
            "\n".join(paths),
            "\n".join(assets),
        ]
    )

    open_source_evidence = []
    if repo_url:
        open_source_evidence.append(f"公开源码仓库: {repo_url}")
    if bundle.license_name:
        open_source_evidence.append(f"LICENSE: {bundle.license_name}")
    if bundle.readme:
        open_source_evidence.append("README 可访问")
    if paths:
        open_source_evidence.append("源码目录结构可访问")
    if release_links:
        open_source_evidence.append("Release 页面可访问: " + release_links[0])

    has_harmony_pc, harmony_evidence = has_harmony_pc_signal(combined_text, paths, releases)
    tech_stack = detect_tech_stack(combined_text, paths, language)
    build_methods = detect_build_methods(combined_text, paths)
    install_methods = detect_install_methods(combined_text, releases)
    category = classify_category(combined_text, tech_stack)
    has_hap = ".hap" in combined_text.lower() or any(
        name.lower().endswith(".hap") for name in release_asset_names(releases)
    )
    is_library, library_reason = is_library_or_package(
        item.get("name", ""),
        description,
        item.get("topics") or [],
        has_release=bool(releases),
        has_hap=has_hap,
        has_market=False,
        install_methods=install_methods,
        category=category,
    )
    library_borderline = library_reason == "borderline-library"
    risks: List[str] = []
    score = score_record(
        bundle,
        combined_text,
        tech_stack,
        build_methods,
        harmony_evidence,
        risks,
        now,
        category=category,
        library_borderline=library_borderline,
    )
    status = status_for_record(combined_text, harmony_evidence, releases) if has_harmony_pc else ""

    decision = "kept"
    kept = True
    if not repo_url or not open_source_evidence:
        kept = False
        decision = "filtered: missing open-source evidence"
    elif not has_harmony_pc:
        kept = False
        decision = "filtered: missing HarmonyOS PC executable/build evidence"
    elif is_library:
        kept = False
        decision = library_reason
    elif score < 40:
        kept = False
        decision = "filtered: score below 40"

    audit = CandidateAudit(
        name=name,
        source=source,
        discovery_query=discovery_query,
        repo_url=repo_url,
        kept=kept,
        decision=decision,
        status=status,
        score=score,
        license=bundle.license_name or "License 不明确",
        description=normalize_whitespace(description)[:500],
        tech_stack=", ".join(tech_stack),
        build_method=", ".join(build_methods),
        install_method=", ".join(install_methods),
        harmony_pc_evidence=harmony_evidence,
        open_source_evidence=open_source_evidence,
        risk=dedupe_preserve_order(risks),
        last_checked=last_checked,
    )

    if not kept:
        return None, audit

    record = ProjectRecord(
        name=name,
        category=category,
        status=status,
        score=score,
        source=source,
        repo_url=repo_url,
        market_url="",
        demo_url=extract_first_url(bundle.readme, ["bilibili.com", "b23.tv", "youtube.com", "youtu.be"]),
        article_url=extract_first_url(bundle.readme, ["csdn.net", "juejin.cn", "zhihu.com", "ost.51cto.com"]),
        license=bundle.license_name or "License 不明确",
        description=normalize_whitespace(description)[:500],
        tech_stack=", ".join(tech_stack),
        build_method=", ".join(build_methods),
        install_method=", ".join(install_methods),
        harmony_pc_evidence=harmony_evidence,
        open_source_evidence=open_source_evidence,
        risk=dedupe_preserve_order(risks),
        recommendation=recommendation_for_score(score),
        last_checked=last_checked,
    )
    return record, audit


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def extract_first_url(text: str, domains: Sequence[str]) -> str:
    if not text:
        return ""
    urls = re.findall(r"https?://[^\s)>\]\"']+", text)
    for url in urls:
        lower = url.lower()
        if any(domain in lower for domain in domains):
            return url.rstrip(".,;")
    return ""


def merge_records(existing: ProjectRecord, incoming: ProjectRecord) -> ProjectRecord:
    existing_sources = dedupe_preserve_order(existing.source.split(",") + incoming.source.split(","))
    existing.source = ", ".join(existing_sources)
    for attr in ["market_url", "demo_url", "article_url"]:
        if not getattr(existing, attr) and getattr(incoming, attr):
            setattr(existing, attr, getattr(incoming, attr))
    existing.harmony_pc_evidence = dedupe_preserve_order(
        existing.harmony_pc_evidence + incoming.harmony_pc_evidence
    )
    existing.open_source_evidence = dedupe_preserve_order(
        existing.open_source_evidence + incoming.open_source_evidence
    )
    existing.risk = dedupe_preserve_order(existing.risk + incoming.risk)
    if incoming.score > existing.score:
        existing.score = incoming.score
        existing.status = incoming.status
        existing.recommendation = incoming.recommendation
    return existing


def write_csv(records: Sequence[ProjectRecord], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow(flatten_record(record))


def write_audit_csv(audits: Sequence[CandidateAudit], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIT_FIELDS)
        writer.writeheader()
        for audit in audits:
            writer.writerow(flatten_audit(audit))


def write_jsonl(records: Sequence[ProjectRecord], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")


def write_markdown(records: Sequence[ProjectRecord], path: Path) -> None:
    groups = {
        "confirmed": "一、confirmed：已确认可执行",
        "buildable": "二、buildable：源码可构建，需进一步验证",
    }
    lines = [
        "# 鸿蒙 PC 可执行开源软件清单",
        "",
        f"生成时间：{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "本报告只包含同时具备开源证据与鸿蒙 PC 可执行/可构建证据的项目。GitCode、B站、应用市场结果需人工复核后再合并。",
        "",
    ]

    for status, title in groups.items():
        lines.extend([f"## {title}", ""])
        group_records = [record for record in records if record.status == status]
        if not group_records:
            lines.extend(["暂无自动确认结果。", ""])
            continue
        for record in sorted(group_records, key=lambda item: item.score, reverse=True):
            lines.extend(render_record_markdown(record))

    lines.extend(["## 三、优先验证建议", ""])
    top_records = sorted(records, key=lambda item: item.score, reverse=True)[:10]
    if not top_records:
        lines.extend(
            [
                "暂无候选项目。请先降低关键词范围、在 `.env` 中配置 `GITHUB_TOKEN`，或根据 `manual_review_links.csv` 做人工复核。",
                "",
            ]
        )
    else:
        for index, record in enumerate(top_records, start=1):
            reason = record.harmony_pc_evidence[0] if record.harmony_pc_evidence else "证据待复核"
            lines.append(f"{index}. **{record.name}**（{record.score} 分，{record.recommendation}）：{reason}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def render_record_markdown(record: ProjectRecord) -> List[str]:
    return [
        f"### {record.name}",
        "",
        f"- 项目简介：{record.description or '暂无简介'}",
        f"- 源码地址：{record.repo_url}",
        f"- 运行证据：{'; '.join(record.harmony_pc_evidence) or '待复核'}",
        f"- 开源证据：{'; '.join(record.open_source_evidence) or '待复核'}",
        f"- 技术栈：{record.tech_stack or '待判断'}",
        f"- 安装 / 构建方式：{record.install_method or record.build_method or '待判断'}",
        f"- 风险：{'; '.join(record.risk) or '暂无明显风险'}",
        f"- 推荐程度：{record.recommendation}（{record.score} 分）",
        "",
    ]


def flatten_record(record: ProjectRecord) -> Dict[str, Any]:
    data = asdict(record)
    data["harmony_pc_evidence"] = "; ".join(record.harmony_pc_evidence)
    data["open_source_evidence"] = "; ".join(record.open_source_evidence)
    data["risk"] = "; ".join(record.risk)
    return data


def flatten_audit(audit: CandidateAudit) -> Dict[str, Any]:
    data = asdict(audit)
    data["harmony_pc_evidence"] = "; ".join(audit.harmony_pc_evidence)
    data["open_source_evidence"] = "; ".join(audit.open_source_evidence)
    data["risk"] = "; ".join(audit.risk)
    return data


def write_manual_review_links(queries: Sequence[str], path: Path) -> None:
    rows = []
    for query in queries:
        encoded = quote_plus(query)
        rows.extend(
            [
                {
                    "source": "GitCode",
                    "query": query,
                    "url": f"https://gitcode.com/search?keyword={encoded}",
                    "review_note": "人工确认源码、LICENSE、README、鸿蒙 PC 证据后再合并。",
                },
                {
                    "source": "Bilibili",
                    "query": query,
                    "url": f"https://search.bilibili.com/all?keyword={encoded}",
                    "review_note": "视频只能作为运行证据；必须反查源码仓库。",
                },
                {
                    "source": "AppGallery",
                    "query": query,
                    "url": f"https://appgallery.huawei.com/search/{quote_plus(query)}",
                    "review_note": "应用市场可安装不等于开源；必须反查公开源码。",
                },
            ]
        )
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source", "query", "url", "review_note"])
        writer.writeheader()
        writer.writerows(rows)


def write_source_candidates_jsonl(candidates: Sequence[SourceCandidate], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for candidate in candidates:
            handle.write(json.dumps(asdict(candidate), ensure_ascii=False) + "\n")


def write_source_candidates_csv(candidates: Sequence[SourceCandidate], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=SOURCE_CANDIDATE_FIELDS)
        writer.writeheader()
        for candidate in candidates:
            data = asdict(candidate)
            data["harmony_pc_evidence"] = "; ".join(candidate.harmony_pc_evidence)
            data["open_source_evidence"] = "; ".join(candidate.open_source_evidence)
            data["risk"] = "; ".join(candidate.risk)
            writer.writerow({field: data.get(field, "") for field in SOURCE_CANDIDATE_FIELDS})


def scrape_gitcode_candidates(
    web: WebClient,
    queries: Sequence[str],
    max_results: int,
    errors: List[str],
) -> List[SourceCandidate]:
    candidates: List[SourceCandidate] = []
    seen: set[str] = set()
    for query in queries:
        if max_results <= 0:
            break
        search_url = f"https://gitcode.com/search?keyword={quote_plus(query)}"
        print(f"[radar] GitCode search: {query}", file=sys.stderr)
        api_candidates = scrape_gitcode_api_candidates(web, query, max_results, errors)
        for candidate in api_candidates:
            key = normalize_repo_key(candidate.repo_url or candidate.source_url)
            if key and key not in seen:
                seen.add(key)
                candidates.append(candidate)
        if api_candidates:
            continue

        try:
            markup = web.fetch_text(search_url)
        except RadarError as exc:
            errors.append(f"GitCode {query}: {exc}")
            continue

        links = extract_links(markup, search_url)
        text = html_to_text(markup)
        repo_urls = extract_repo_urls(text)
        for href, _label in links:
            repo_url = normalize_repo_url(href)
            if repo_url:
                repo_urls.append(repo_url)

        for repo_url in dedupe_preserve_order(repo_urls):
            if len([item for item in candidates if item.query == query]) >= max_results:
                break
            key = normalize_repo_key(repo_url)
            if key in seen:
                continue
            seen.add(key)
            page_text = ""
            title = infer_name_from_url(repo_url)
            try:
                repo_markup = web.fetch_text(repo_url)
                page_text = html_to_text(repo_markup)
                title = html_title(repo_markup) or title
            except RadarError as exc:
                errors.append(f"GitCode repo {repo_url}: {exc}")
            candidates.append(
                SourceCandidate(
                    source="GitCode",
                    query=query,
                    name=normalize_whitespace(title)[:180],
                    source_url=repo_url,
                    repo_url=repo_url,
                    description=normalize_whitespace(page_text)[:600],
                    page_text=page_text,
                    license=detect_license_from_text(page_text),
                )
            )
    return candidates


def scrape_gitcode_api_candidates(
    web: WebClient,
    query: str,
    max_results: int,
    errors: List[str],
) -> List[SourceCandidate]:
    url = f"https://gitcode.com/api/v1/search/nauth/query?q={quote_plus(query)}&page=1&per_page={max_results}"
    try:
        payload = web.fetch_json(url, referer=f"https://gitcode.com/search?keyword={quote_plus(query)}")
    except RadarError as exc:
        errors.append(f"GitCode API {query}: {exc}")
        return []

    items = payload.get("content") or []
    candidates: List[SourceCandidate] = []
    for item in items[:max_results]:
        repo_url = normalize_repo_url(item.get("web_url") or "")
        if not repo_url:
            path_with_namespace = item.get("path_with_namespace") or ""
            if "/" in path_with_namespace:
                repo_url = f"https://gitcode.com/{path_with_namespace.strip('/')}"
        import_url = normalize_url(item.get("import_url") or "")
        github_import = normalize_repo_url(import_url)
        license_obj = item.get("license") or {}
        license_name = license_obj.get("key") or license_obj.get("name") or license_obj.get("nickname") or ""
        tags = []
        for tag in (item.get("tags") or []) + (item.get("topic_names") or []):
            if isinstance(tag, dict) and tag.get("name"):
                tags.append(str(tag["name"]))
        description = normalize_whitespace(
            item.get("description_cn")
            or item.get("description")
            or item.get("hl_desc")
            or ""
        )
        page_text = compact_text(
            [
                item.get("name") or "",
                item.get("name_with_namespace") or "",
                description,
                item.get("main_language") or item.get("language") or "",
                " ".join(tags),
                repo_url,
                import_url,
            ]
        )
        open_source_evidence = [f"GitCode 仓库可访问: {repo_url}"] if repo_url else []
        if github_import:
            open_source_evidence.append(f"GitHub 上游/导入仓库: {github_import}")
        if license_name:
            open_source_evidence.append(f"GitCode License: {license_name}")
        candidates.append(
            SourceCandidate(
                source="GitCode",
                query=query,
                name=item.get("name_with_namespace") or item.get("name") or infer_name_from_url(repo_url),
                source_url=repo_url or f"https://gitcode.com/search?keyword={quote_plus(query)}",
                repo_url=repo_url or github_import,
                article_url=github_import if github_import and not repo_url else "",
                license=license_name,
                description=description,
                page_text=page_text,
                open_source_evidence=open_source_evidence,
            )
        )
    return candidates


def scrape_bilibili_candidates(
    web: WebClient,
    queries: Sequence[str],
    max_results: int,
    errors: List[str],
) -> List[SourceCandidate]:
    candidates: List[SourceCandidate] = []
    seen: set[str] = set()
    for query in queries:
        if max_results <= 0:
            break
        search_url = f"https://search.bilibili.com/all?keyword={quote_plus(query)}"
        print(f"[radar] Bilibili search: {query}", file=sys.stderr)
        try:
            markup = web.fetch_text(search_url)
        except RadarError as exc:
            errors.append(f"Bilibili {query}: {exc}")
            continue

        video_links: List[Tuple[str, str]] = []
        for href, label in extract_links(markup, search_url):
            parsed = urlparse(href)
            if "bilibili.com" in parsed.netloc and "/video/" in parsed.path:
                video_links.append((href.split("?")[0], label))

        # Some Bilibili pages keep links in JSON strings rather than anchor tags.
        for match in re.finditer(r"https?:\\/\\/www\.bilibili\.com\\/video\\/(BV[0-9A-Za-z]+)", markup):
            video_links.append((f"https://www.bilibili.com/video/{match.group(1)}", ""))

        if not video_links:
            page_text = html_to_text(markup)
            candidates.append(
                SourceCandidate(
                    source="Bilibili",
                    query=query,
                    name=f"Bilibili search: {query}",
                    source_url=search_url,
                    demo_url=search_url,
                    description=normalize_whitespace(page_text)[:600],
                    page_text=page_text,
                    risk=["B站搜索页可能需要验证码或浏览器渲染，需人工复核"],
                    decision="needs_browser_review",
                )
            )
            continue

        for video_url, label in dedupe_link_pairs(video_links):
            if len([item for item in candidates if item.query == query]) >= max_results:
                break
            key = normalize_url(video_url).lower()
            if key in seen:
                continue
            seen.add(key)
            page_text = ""
            title = label or infer_name_from_url(video_url)
            try:
                video_markup = web.fetch_text(video_url)
                page_text = html_to_text(video_markup)
                title = html_title(video_markup) or title
            except RadarError as exc:
                errors.append(f"Bilibili video {video_url}: {exc}")

            repo_urls = extract_repo_urls("\n".join([title, label, page_text]))
            repo_url = repo_urls[0] if repo_urls else ""
            candidates.append(
                SourceCandidate(
                    source="Bilibili",
                    query=query,
                    name=normalize_whitespace(title)[:180],
                    source_url=video_url,
                    repo_url=repo_url,
                    demo_url=video_url,
                    description=normalize_whitespace(page_text)[:600],
                    page_text=page_text,
                    license=detect_license_from_text(page_text),
                )
            )
    return candidates


def scrape_appgallery_candidates(
    web: WebClient,
    queries: Sequence[str],
    max_results: int,
    errors: List[str],
) -> List[SourceCandidate]:
    candidates: List[SourceCandidate] = []
    seen: set[str] = set()
    for query in queries:
        if max_results <= 0:
            break
        search_url = f"https://appgallery.huawei.com/search/{quote_plus(query)}"
        print(f"[radar] AppGallery search: {query}", file=sys.stderr)
        try:
            markup = web.fetch_text(search_url)
        except RadarError as exc:
            errors.append(f"AppGallery {query}: {exc}")
            continue

        app_links: List[Tuple[str, str]] = []
        for href, label in extract_links(markup, search_url):
            parsed = urlparse(href)
            if "appgallery.huawei.com" not in parsed.netloc:
                continue
            if "/app/" in parsed.path or "/#/app/" in href or re.search(r"/C\d+", parsed.path):
                app_links.append((href.split("?")[0], label))

        for match in re.finditer(r"https?://appgallery\.huawei\.com/(?:app/)?(C\d+)", markup, flags=re.I):
            app_links.append((f"https://appgallery.huawei.com/app/{match.group(1)}", ""))

        if not app_links:
            page_text = html_to_text(markup)
            candidates.append(
                SourceCandidate(
                    source="AppGallery",
                    query=query,
                    name=f"AppGallery search: {query}",
                    source_url=search_url,
                    market_url=search_url,
                    description=normalize_whitespace(page_text)[:600],
                    page_text=page_text,
                    risk=["AppGallery 搜索页为动态渲染页面，需人工或浏览器复核"],
                    decision="needs_browser_review",
                )
            )
            continue

        for app_url, label in dedupe_link_pairs(app_links):
            if len([item for item in candidates if item.query == query]) >= max_results:
                break
            key = normalize_url(app_url).lower()
            if key in seen:
                continue
            seen.add(key)
            page_text = ""
            title = label or infer_name_from_url(app_url)
            try:
                app_markup = web.fetch_text(app_url)
                page_text = html_to_text(app_markup)
                title = html_title(app_markup) or title
            except RadarError as exc:
                errors.append(f"AppGallery app {app_url}: {exc}")

            repo_urls = extract_repo_urls("\n".join([title, label, page_text]))
            repo_url = repo_urls[0] if repo_urls else ""
            candidates.append(
                SourceCandidate(
                    source="AppGallery",
                    query=query,
                    name=normalize_whitespace(title)[:180],
                    source_url=app_url,
                    repo_url=repo_url,
                    market_url=app_url,
                    description=normalize_whitespace(page_text)[:600],
                    page_text=page_text,
                    license=detect_license_from_text(page_text),
                )
            )
    return candidates


def dedupe_link_pairs(links: Sequence[Tuple[str, str]]) -> List[Tuple[str, str]]:
    seen: set[str] = set()
    output: List[Tuple[str, str]] = []
    for href, label in links:
        href = normalize_url(href)
        if not href:
            continue
        key = href.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append((href, label))
    return output


def analyze_source_candidate(
    candidate: SourceCandidate,
    now: dt.datetime,
) -> Tuple[Optional[ProjectRecord], CandidateAudit]:
    repo_url = find_first_repo_url(candidate)
    combined_text = compact_text(
        [
            candidate.name,
            candidate.description,
            candidate.page_text,
            candidate.source_url,
            repo_url,
        ]
    )
    license_name = candidate.license or detect_license_from_text(combined_text)
    tech_stack = detect_tech_stack(combined_text, [], "")
    build_methods = detect_build_methods(combined_text, [])
    install_methods = detect_install_methods(combined_text, [])
    open_source_evidence: List[str] = list(candidate.open_source_evidence)
    harmony_evidence: List[str] = list(candidate.harmony_pc_evidence)
    risks: List[str] = list(candidate.risk)

    if repo_url:
        open_source_evidence.append(f"公开源码仓库: {repo_url}")
    if license_name:
        open_source_evidence.append(f"License 线索: {license_name}")
    if candidate.source_url:
        open_source_evidence.append(f"{candidate.source} 来源页面可访问: {candidate.source_url}")

    has_harmony_pc, detected_harmony_evidence = has_harmony_pc_signal(combined_text, [], [])
    harmony_evidence.extend(detected_harmony_evidence)
    if candidate.demo_url and has_harmony_pc:
        harmony_evidence.append(f"B站/视频运行或移植线索: {candidate.demo_url}")
    if candidate.market_url and has_harmony_pc:
        harmony_evidence.append(f"应用市场可安装线索: {candidate.market_url}")

    explicit_pc = contains_any(combined_text, PC_TERMS)
    has_demo = bool(candidate.demo_url)
    has_market = bool(candidate.market_url)
    has_hap = ".hap" in combined_text.lower() or re.search(r"\bhap\b", combined_text.lower()) is not None
    category = classify_category(combined_text, tech_stack)
    is_library, library_reason = is_library_or_package(
        candidate.name,
        candidate.description,
        [],
        has_release=False,
        has_hap=has_hap,
        has_market=has_market,
        install_methods=install_methods,
        category=category,
    )
    library_borderline = library_reason == "borderline-library"

    score = 0
    if explicit_pc:
        score += 25
    if repo_url:
        score += 20
    if license_name:
        score += 10
    if has_hap or has_market:
        score += 15
    if build_methods:
        score += 10
    if has_demo:
        score += 10
    if set(tech_stack) & {"ArkTS", "Qt", "Electron", "C++", "Rust", "Go", "Flutter", "HAP"}:
        score += 5

    if not license_name:
        score -= 10
        risks.append("License 不明确")
    if not explicit_pc:
        score -= 10
        risks.append("缺少明确 PC 运行证据")
    if not build_methods and not has_market and not has_demo and not has_hap:
        score -= 10
        risks.append("构建或运行步骤不完整")
    if candidate.source == "AppGallery" and not repo_url:
        risks.append("应用市场页面缺少源码仓库线索")
    if candidate.source == "Bilibili" and not repo_url:
        risks.append("B站视频缺少源码仓库线索")

    score += popularity_bonus(candidate.stars)
    score += harmony_port_bonus(combined_text, category)
    if library_borderline:
        score -= 8
        risks.append("疑似库/SDK但含可执行产物,保留并降分")

    score = max(0, min(100, score))
    if not harmony_evidence:
        score = min(score, 39)

    kept = True
    decision = "kept"
    if not repo_url:
        kept = False
        decision = "filtered: missing source repository link"
    elif not harmony_evidence:
        kept = False
        decision = "filtered: missing HarmonyOS PC executable/build evidence"
    elif is_library:
        kept = False
        decision = library_reason
    elif score < 40:
        kept = False
        decision = "filtered: score below 40"

    status = ""
    if kept:
        if candidate.source == "Bilibili":
            status = "ported-demo"
        elif has_market or explicit_pc and (has_hap or has_demo):
            status = "confirmed"
        else:
            status = "buildable"

    audit = CandidateAudit(
        name=candidate.name or infer_name_from_url(repo_url or candidate.source_url),
        source=candidate.source,
        discovery_query=candidate.query,
        repo_url=repo_url,
        kept=kept,
        decision=decision,
        status=status,
        score=score,
        license=license_name or "License 不明确",
        description=normalize_whitespace(candidate.description)[:500],
        tech_stack=", ".join(tech_stack),
        build_method=", ".join(build_methods),
        install_method=", ".join(install_methods),
        harmony_pc_evidence=dedupe_preserve_order(harmony_evidence),
        open_source_evidence=dedupe_preserve_order(open_source_evidence),
        risk=dedupe_preserve_order(risks),
        last_checked=now.date().isoformat(),
    )
    candidate.repo_url = repo_url
    candidate.license = license_name or candidate.license
    candidate.harmony_pc_evidence = audit.harmony_pc_evidence
    candidate.open_source_evidence = audit.open_source_evidence
    candidate.risk = audit.risk
    candidate.decision = decision

    if not kept:
        return None, audit

    record = ProjectRecord(
        name=candidate.name or infer_name_from_url(repo_url),
        category=category,
        status=status,
        score=score,
        source=candidate.source,
        repo_url=repo_url,
        market_url=candidate.market_url,
        demo_url=candidate.demo_url,
        article_url=candidate.article_url,
        license=license_name or "License 不明确",
        description=normalize_whitespace(candidate.description)[:500],
        tech_stack=", ".join(tech_stack),
        build_method=", ".join(build_methods),
        install_method=", ".join(install_methods),
        harmony_pc_evidence=audit.harmony_pc_evidence,
        open_source_evidence=audit.open_source_evidence,
        risk=audit.risk,
        recommendation=recommendation_for_score(score),
        last_checked=now.date().isoformat(),
    )
    return record, audit


def enrich_record_with_candidate(record: ProjectRecord, candidate: SourceCandidate) -> ProjectRecord:
    if candidate.market_url and not record.market_url:
        record.market_url = candidate.market_url
    if candidate.demo_url and not record.demo_url:
        record.demo_url = candidate.demo_url
    if candidate.article_url and not record.article_url:
        record.article_url = candidate.article_url
    record.harmony_pc_evidence = dedupe_preserve_order(
        record.harmony_pc_evidence + candidate.harmony_pc_evidence
    )
    record.open_source_evidence = dedupe_preserve_order(
        record.open_source_evidence + candidate.open_source_evidence
    )
    record.risk = dedupe_preserve_order(record.risk + candidate.risk)
    return record


def maybe_enrich_candidate_from_github(
    candidate: SourceCandidate,
    github: GitHubClient,
    bundle_by_repo: Dict[str, RepoBundle],
    errors: List[str],
) -> None:
    repo_url = find_first_repo_url(candidate)
    if "github.com" not in repo_url.lower():
        return
    key = normalize_repo_key(repo_url)
    try:
        if key in bundle_by_repo:
            bundle = bundle_by_repo[key]
        else:
            full_name = "/".join(urlparse(repo_url).path.strip("/").split("/")[:2])
            if not full_name or "/" not in full_name:
                return
            item = github.get_json(f"{GITHUB_API}/repos/{full_name}")
            if not item:
                return
            bundle = github.fetch_bundle(item)
            bundle_by_repo[key] = bundle
    except RadarError as exc:
        errors.append(f"external GitHub enrichment {repo_url}: {exc}")
        return

    candidate.repo_url = repo_url
    candidate.stars = int(bundle.item.get("stargazers_count") or 0)
    if bundle.license_name and not candidate.license:
        candidate.license = bundle.license_name
    if not candidate.description:
        candidate.description = normalize_whitespace(bundle.item.get("description") or "")
    github_text = compact_text(
        [
            bundle.item.get("description") or "",
            " ".join(bundle.item.get("topics") or []),
            bundle.readme,
            "\n".join(bundle.paths[:1000]),
            "\n".join(release_asset_names(bundle.releases)),
        ]
    )
    candidate.page_text = compact_text([candidate.page_text, github_text])
    candidate.open_source_evidence = dedupe_preserve_order(
        candidate.open_source_evidence
        + [
            f"GitHub 仓库可访问: {repo_url}",
            f"GitHub License: {bundle.license_name}" if bundle.license_name else "",
            "GitHub README 可访问" if bundle.readme else "",
            "GitHub 源码目录结构可访问" if bundle.paths else "",
        ]
    )


def run(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    sources = args.sources
    queries = build_query_plan(args.query, args.search_profile)
    code_queries = (
        build_code_search_plan(queries, args.search_profile)
        if args.include_code_search and "github" in sources
        else []
    )
    token = resolve_github_token(args.github_token, Path(args.env_file))
    now = dt.datetime.now(dt.timezone.utc)
    needs_github_client = (
        ("github" in sources and args.max_results > 0)
        or (args.include_code_search and args.max_results > 0)
        or (args.enrich_external_github and args.web_max_results > 0)
    )
    github: Optional[GitHubClient] = GitHubClient(token=token) if needs_github_client else None
    web: Optional[WebClient] = (
        WebClient(timeout=args.web_timeout)
        if any(source in sources for source in ["gitcode", "bilibili", "appgallery"]) and args.web_max_results > 0
        else None
    )
    records_by_repo: Dict[str, ProjectRecord] = {}
    bundle_by_repo: Dict[str, RepoBundle] = {}
    raw_candidates: List[SourceCandidate] = []
    audits: List[CandidateAudit] = []
    errors: List[str] = []

    def handle_repo_item(item: Dict[str, Any], source: str, discovery_query: str) -> None:
        repo_url = (item.get("html_url") or "").rstrip("/")
        if not repo_url:
            return
        key = normalize_repo_key(repo_url)
        try:
            if key in bundle_by_repo:
                bundle = bundle_by_repo[key]
            else:
                if github is None:
                    return
                bundle = github.fetch_bundle(item)
                bundle_by_repo[key] = bundle
        except RadarError as exc:
            errors.append(f"{repo_url}: {exc}")
            return

        record, audit = analyze_bundle_with_audit(bundle, now, source, discovery_query)
        if record and record.score < args.min_score:
            audit.kept = False
            audit.decision = f"filtered: score below --min-score ({args.min_score})"
            record = None
        audits.append(audit)
        if not record:
            return
        record_key = normalize_repo_key(record.repo_url)
        if record_key in records_by_repo:
            records_by_repo[record_key] = merge_records(records_by_repo[record_key], record)
        else:
            records_by_repo[record_key] = record

    for query in queries if "github" in sources else []:
        if github is None:
            continue
        print(f"[radar] GitHub search: {query}", file=sys.stderr)
        try:
            items = github.search_repositories(query, args.max_results, since=args.since)
        except RadarError as exc:
            errors.append(f"{query}: {exc}")
            continue

        for item in items:
            handle_repo_item(item, "GitHub repo search", query)

    for query in code_queries:
        if github is None:
            continue
        print(f"[radar] GitHub code search: {query}", file=sys.stderr)
        try:
            code_items = github.search_code(query, args.code_max_results)
        except RadarError as exc:
            errors.append(f"code search {query}: {exc}")
            continue

        for code_item in code_items:
            repo_item = code_item.get("repository") or {}
            handle_repo_item(repo_item, "GitHub code search", query)

    if web is not None and "gitcode" in sources:
        raw_candidates.extend(scrape_gitcode_candidates(web, queries, args.web_max_results, errors))
    if web is not None and "bilibili" in sources:
        raw_candidates.extend(scrape_bilibili_candidates(web, queries, args.web_max_results, errors))
    if web is not None and "appgallery" in sources:
        raw_candidates.extend(scrape_appgallery_candidates(web, queries, args.web_max_results, errors))

    for candidate in raw_candidates:
        if args.enrich_external_github and github is not None:
            maybe_enrich_candidate_from_github(candidate, github, bundle_by_repo, errors)
        record, audit = analyze_source_candidate(candidate, now)
        if record and record.score < args.min_score:
            audit.kept = False
            audit.decision = f"filtered: score below --min-score ({args.min_score})"
            candidate.decision = audit.decision
            record = None
        audits.append(audit)
        if not record:
            continue
        key = normalize_repo_key(record.repo_url)
        if key in records_by_repo:
            records_by_repo[key] = merge_records(records_by_repo[key], record)
        else:
            records_by_repo[key] = record

    records = sorted(records_by_repo.values(), key=lambda item: item.score, reverse=True)

    if args.include_manual_links:
        write_manual_review_links(queries, out_dir / "manual_review_links.csv")
    if args.include_audit:
        write_audit_csv(audits, out_dir / "candidate_audit.csv")
    if raw_candidates:
        write_source_candidates_jsonl(raw_candidates, out_dir / "source_candidates_raw.jsonl")
        for source_name, filename in [
            ("GitCode", "gitcode_candidates.csv"),
            ("Bilibili", "bilibili_candidates.csv"),
            ("AppGallery", "appgallery_candidates.csv"),
        ]:
            source_candidates = [item for item in raw_candidates if item.source == source_name]
            if source_candidates:
                write_source_candidates_csv(source_candidates, out_dir / filename)

    selected_format = args.format
    if selected_format in {"csv", "all"}:
        write_csv(records, out_dir / "harmony_pc_oss_list.csv")
    if selected_format in {"jsonl", "all"}:
        write_jsonl(records, out_dir / "harmony_pc_oss_list.jsonl")
    if selected_format in {"md", "all"}:
        write_markdown(records, out_dir / "harmony_pc_oss_report.md")

    if errors:
        print("[radar] Completed with warnings:", file=sys.stderr)
        for error in errors[:20]:
            print(f"  - {error}", file=sys.stderr)
        if len(errors) > 20:
            print(f"  - ... {len(errors) - 20} more warnings", file=sys.stderr)

    print(f"[radar] kept {len(records)} project(s). Output directory: {out_dir}", file=sys.stderr)
    if not records:
        print(
            "[radar] No project passed the conservative filter. Review manual_review_links.csv "
            "or try broader queries / GITHUB_TOKEN in .env.",
            file=sys.stderr,
        )
    return 0


def normalize_repo_key(repo_url: str) -> str:
    return repo_url.rstrip("/").lower().replace("https://www.", "https://")


def validate_since(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    try:
        dt.date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--since must use YYYY-MM-DD format") from exc
    return value


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search, filter, score, and report open-source software candidates for HarmonyOS PC.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            Examples:
              python scripts/harmony_pc_oss_radar.py --query "鸿蒙 PC 开源软件" --query "HarmonyOS PC open source app" --out-dir outputs --max-results 30 --include-manual-links --format all
              python scripts/harmony_pc_oss_radar.py --query "HarmonyOS Computer app" --out-dir outputs --format all
              python scripts/harmony_pc_oss_radar.py --sources all --search-profile expanded --include-code-search --include-audit --out-dir outputs --max-results 50 --web-max-results 20 --include-manual-links --format all
            """
        ),
    )
    parser.add_argument("--query", action="append", help="Search keyword. Can be provided multiple times.")
    parser.add_argument("--out-dir", default="outputs", help="Output directory.")
    parser.add_argument(
        "--sources",
        type=parse_sources,
        default=list(ALL_SOURCES),
        help="Comma-separated sources: github,gitcode,bilibili,appgallery, or all. Default: all.",
    )
    parser.add_argument(
        "--search-profile",
        choices=["focused", "expanded"],
        default="focused",
        help="focused keeps provided/default queries; expanded adds built-in broad recall queries.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=30,
        help="Maximum GitHub search results per query. Use 0 to only generate manual-review links.",
    )
    parser.add_argument(
        "--web-max-results",
        type=int,
        default=10,
        help="Maximum GitCode/Bilibili/AppGallery candidates per query per source. Default: 10.",
    )
    parser.add_argument(
        "--web-timeout",
        type=int,
        default=20,
        help="HTTP timeout in seconds for GitCode/Bilibili/AppGallery pages. Default: 20.",
    )
    parser.add_argument(
        "--github-token",
        default="",
        help="Optional GitHub token. Overrides GITHUB_TOKEN from environment or .env.",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to a .env file. Defaults to .env in the current invocation directory.",
    )
    parser.add_argument(
        "--include-manual-links",
        action="store_true",
        help="Generate GitCode, Bilibili, and AppGallery manual-review search links.",
    )
    parser.add_argument(
        "--include-code-search",
        action="store_true",
        help="Also use GitHub code search for exact HarmonyOS PC phrases and project files.",
    )
    parser.add_argument(
        "--code-max-results",
        type=int,
        default=20,
        help="Maximum GitHub code search results per code query. Default: 20.",
    )
    parser.add_argument(
        "--include-audit",
        action="store_true",
        help="Write outputs/candidate_audit.csv with kept and filtered candidate reasons.",
    )
    parser.add_argument(
        "--enrich-external-github",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Fetch GitHub metadata for GitHub links found in GitCode/Bilibili/AppGallery candidates. Default: true.",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "jsonl", "md", "all"],
        default="all",
        help="Output format.",
    )
    parser.add_argument("--since", type=validate_since, help="Only search repositories pushed after YYYY-MM-DD.")
    parser.add_argument(
        "--min-score",
        type=int,
        default=40,
        help="Minimum score to keep. Default: 40.",
    )
    args = parser.parse_args(argv)
    if args.max_results < 0:
        parser.error("--max-results must be >= 0")
    if args.web_max_results < 0:
        parser.error("--web-max-results must be >= 0")
    if args.web_timeout <= 0:
        parser.error("--web-timeout must be > 0")
    if args.code_max_results < 0:
        parser.error("--code-max-results must be >= 0")
    if not (0 <= args.min_score <= 100):
        parser.error("--min-score must be between 0 and 100")
    return args


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
