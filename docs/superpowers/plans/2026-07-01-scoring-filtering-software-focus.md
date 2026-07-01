# 评分与筛选机制改造 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让最终清单只保留"适配鸿蒙 PC 的开源软件"和"已有知名开源软件的鸿蒙化移植"，剔除纯库/SDK/包/框架，并用 GitHub star 知名度加成提升排名。

**Architecture:** 在单文件脚本 `scripts/harmony_pc_oss_radar.py` 中新增库检测器 `is_library_or_package`、知名度加成 `popularity_bonus`、鸿蒙化移植加成 `harmony_port_bonus`；把它们接入 GitHub 路径（`score_record` + `analyze_bundle_with_audit`）与候选路径（`analyze_source_candidate`）；同步更新 `SKILL.md` §8/§9/§13。所有输出 schema 不变，star 数不进任何输出。

**Tech Stack:** Python 3，requests/beautifulsoup4（可选），argparse；无测试框架。

---

## 重要约定（来自 AGENTS.md，优先级高于本 plan 的默认做法）

1. **无测试套件 / lint / typecheck**：本仓库没有 pytest/ruff/mypy。**不要写 pytest 测试文件，不要运行 pytest**。验证方式 = `python -c` 内联断言 + `python scripts/harmony_pc_oss_radar.py --help` + 端到端跑脚本看输出。
2. **双副本同步**：`scripts/harmony_pc_oss_radar.py` 与 `SKILL.md` 在根目录和 `.opencode/skills/harmony-pc-oss-radar/` 各有一份，必须**字节一致**。Task 1–4 只改根目录脚本（中间态允许 .opencode 副本短暂过期，因为脚本执行不走 .opencode 副本）；Task 5 统一同步脚本副本，Task 6 同步 SKILL.md 副本。
3. **outputs/ 已纳入 git**：端到端跑会改 outputs，但**不要提交 outputs**（用户未要求）；Task 7 仅作验证。
4. **Windows / PowerShell**：命令用 PowerShell 语法。

## File Structure

| 文件 | 责任 | 本 plan 改动 |
|---|---|---|
| `scripts/harmony_pc_oss_radar.py`（根） | 搜索/过滤/评分/输出单文件脚本 | 新增常量、3 个 helper、改 `score_record`/`analyze_bundle_with_audit`/`analyze_source_candidate`/`SourceCandidate`/`maybe_enrich_candidate_from_github` |
| `.opencode/skills/harmony-pc-oss-radar/scripts/harmony_pc_oss_radar.py` | OpenCode 加载的脚本副本 | Task 5 从根复制，保持字节一致 |
| `SKILL.md`（根） | Skill 工作流与规则 | §8/§9/§13 增补 |
| `.opencode/skills/harmony-pc-oss-radar/SKILL.md` | OpenCode 加载的 SKILL 副本 | Task 6 从根复制，保持字节一致 |

---

## Task 1: 新增常量与 3 个 helper（根脚本）

**Files:**
- Modify: `scripts/harmony_pc_oss_radar.py`（在 `README_LOW_INFO_THRESHOLD = 291` 之后、`class RadarError` 之前插入常量；在 `status_for_record` 与 `score_record` 之间插入 helper）

- [ ] **Step 1: 插入常量块**

打开 `scripts/harmony_pc_oss_radar.py`，定位到第 291 行 `README_LOW_INFO_THRESHOLD = 240`（注意：行号 291 是 `README_LOW_INFO_THRESHOLD = 240` 这一行的位置；以实际文本为准）。在该行之后、空行 + `class RadarError(RuntimeError):` 之前，插入：

```python
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
```

- [ ] **Step 2: 插入 3 个 helper 函数**

定位到 `def status_for_record(...)` 结束（`return "buildable"` 那一行）之后、`def score_record(...)` 之前，插入：

```python
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
```

设计要点：text pattern 只扫 name+description 一行摘要（不扫整篇 README），避免真实应用 README 里提到 "HarmonyOS SDK" 被误判；`\bport\b` 用词边界，避免命中 support/export/import。

- [ ] **Step 3: 语法/导入冒烟**

Run:
```powershell
python -c "import ast; ast.parse(open('scripts/harmony_pc_oss_radar.py',encoding='utf-8').read()); print('syntax OK')"
```
Expected: `syntax OK`

- [ ] **Step 4: helper 行为断言**

Run:
```powershell
python -c "import sys; sys.path.insert(0,'scripts'); import harmony_pc_oss_radar as r; assert r.popularity_bonus(1500)==8 and r.popularity_bonus(50)==1 and r.popularity_bonus(0)==0 and r.popularity_bonus(99999)==12; assert r.harmony_port_bonus('we port this for HarmonyOS','桌面软件移植项目')==8; assert r.harmony_port_bonus('no signal here','桌面软件移植项目')==0; a=r.is_library_or_package('my-sdk','an sdk for x',[],False,False,False,[],'未分类桌面应用'); assert a==(True,'filtered: library/SDK/package/framework (no runnable artifact)'), a; b=r.is_library_or_package('my-sdk','an sdk for x',[],True,False,False,['HAP'],'原生鸿蒙 PC 应用'); assert b==(False,'borderline-library'), b; c=r.is_library_or_package('term-app','a terminal for HarmonyOS PC',[],False,False,False,[],'终端与运行环境'); assert c==(False,''), c; print('helpers OK')"
```
Expected: `helpers OK`

- [ ] **Step 5: --help 仍可用**

Run:
```powershell
python scripts/harmony_pc_oss_radar.py --help
```
Expected: 打印 usage，无异常退出。

- [ ] **Step 6: Commit**

```powershell
git add scripts/harmony_pc_oss_radar.py
git commit -m "feat(radar):新增库检测与知名度/移植加成 helper"
```

---

## Task 2: `SourceCandidate.stars` 字段 + enrichment 注入（根脚本）

**Files:**
- Modify: `scripts/harmony_pc_oss_radar.py`（`SourceCandidate` dataclass ~行 343；`maybe_enrich_candidate_from_github` ~行 1885）

- [ ] **Step 1: 给 SourceCandidate 加内部字段 stars**

定位 `class SourceCandidate:`（约行 343）。在 `page_text: str = ""` 行之后新增一行（**不要**把 `stars` 加进 `SOURCE_CANDIDATE_FIELDS`，保持输出不暴露 star）：

```python
    stars: int = 0
```

改后该段应为：
```python
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
```

- [ ] **Step 2: enrichment 时写入 stars**

定位 `def maybe_enrich_candidate_from_github(...)` 内的 `candidate.repo_url = repo_url`（约行 1885）。在该行之后新增：

```python
    candidate.stars = int(bundle.item.get("stargazers_count") or 0)
```

- [ ] **Step 3: 语法 + 导入冒烟**

Run:
```powershell
python -c "import sys; sys.path.insert(0,'scripts'); import harmony_pc_oss_radar as r; c=r.SourceCandidate(source='GitCode',query='q',name='n',source_url='u'); assert c.stars==0; c.stars=1500; assert c.stars==1500; print('stars field OK')"
```
Expected: `stars field OK`

- [ ] **Step 4: --help 仍可用**

Run:
```powershell
python scripts/harmony_pc_oss_radar.py --help
```
Expected: 打印 usage。

- [ ] **Step 5: Commit**

```powershell
git add scripts/harmony_pc_oss_radar.py
git commit -m "feat(radar):SourceCandidate 增加 stars 内部字段并经 enrichment 注入"
```

---

## Task 3: 接入 GitHub 路径（`score_record` + `analyze_bundle_with_audit`）

**Files:**
- Modify: `scripts/harmony_pc_oss_radar.py`（`score_record` ~行 933；`analyze_bundle_with_audit` ~行 1127–1154）

- [ ] **Step 1: 扩展 score_record 签名与加成**

定位 `def score_record(...)`。把签名改为新增两个默认参数 `category` 与 `library_borderline`：

```python
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
```

然后在函数体末尾、`if not harmony_evidence:` 之前插入知名度/移植/库边界三段。改后函数尾部应为：

```python
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
```

要点：加成在 `harmony_evidence` cap 之前加，保证无鸿蒙证据项目仍被 cap 39。

- [ ] **Step 2: analyze_bundle_with_audit 提前算 category + 库检测 + 接线**

定位 `analyze_bundle_with_audit` 内这段（约 1127–1154）：

```python
    has_harmony_pc, harmony_evidence = has_harmony_pc_signal(combined_text, paths, releases)
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
    category = classify_category(combined_text, tech_stack)
    status = status_for_record(combined_text, harmony_evidence, releases) if has_harmony_pc else ""

    decision = "kept"
    kept = True
    if not repo_url or not open_source_evidence:
        kept = False
        decision = "filtered: missing open-source evidence"
    elif not has_harmony_pc:
        kept = False
        decision = "filtered: missing HarmonyOS PC executable/build evidence"
    elif score < 40:
        kept = False
        decision = "filtered: score below 40"
```

替换为：

```python
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
```

要点：库过滤分支放在 `has_harmony_pc` 之后、`score<40` 之前，使被剔库项目得到明确 decision。

- [ ] **Step 3: 语法冒烟**

Run:
```powershell
python -c "import ast; ast.parse(open('scripts/harmony_pc_oss_radar.py',encoding='utf-8').read()); print('syntax OK')"
```
Expected: `syntax OK`

- [ ] **Step 4: 库过滤行为断言（GitHub 路径）**

Run:
```powershell
python -c "import sys; sys.path.insert(0,'scripts'); import harmony_pc_oss_radar as r, datetime as d; b=r.RepoBundle(item={'html_url':'https://github.com/x/y','full_name':'x/y','name':'y','description':'an sdk for HarmonyOS PC','stargazers_count':1500,'updated_at':'2099-01-01T00:00:00Z','topics':['sdk']},readme='HarmonyOS PC tool '*30,license_name='MIT',releases=[],paths=[]); rec,aud=r.analyze_bundle_with_audit(b,d.datetime.now(d.timezone.utc),'test','q'); assert rec is None and 'library/SDK' in aud.decision, (rec,aud.decision); print('OK lib-filter', aud.decision)"
```
Expected: `OK lib-filter filtered: library/SDK/package/framework (no runnable artifact)`

- [ ] **Step 5: 正常应用 + star/移植加成断言（GitHub 路径）**

Run:
```powershell
python -c "import sys; sys.path.insert(0,'scripts'); import harmony_pc_oss_radar as r, datetime as d; b=r.RepoBundle(item={'html_url':'https://github.com/x/y','full_name':'x/y','name':'y','description':'A terminal app for HarmonyOS PC','stargazers_count':1500,'updated_at':'2099-01-01T00:00:00Z','topics':[]},readme='HarmonyOS PC terminal '*30,license_name='MIT',releases=[],paths=[]); rec,aud=r.analyze_bundle_with_audit(b,d.datetime.now(d.timezone.utc),'test','q'); assert rec is not None and rec.score>0, (rec,aud.decision); assert 'stars' not in r.OUTPUT_FIELDS; print('OK app score',rec.score)"
```
Expected: `OK app score <N>`（N 为正数；且断言 OUTPUT_FIELDS 不含 stars）

- [ ] **Step 6: --help 仍可用**

Run:
```powershell
python scripts/harmony_pc_oss_radar.py --help
```
Expected: 打印 usage。

- [ ] **Step 7: Commit**

```powershell
git add scripts/harmony_pc_oss_radar.py
git commit -m "feat(radar):GitHub 路径接入库过滤与 star/移植加成"
```

---

## Task 4: 接入候选路径（`analyze_source_candidate`）

**Files:**
- Modify: `scripts/harmony_pc_oss_radar.py`（`analyze_source_candidate` ~行 1729–1838）

- [ ] **Step 1: 候选评分前置 category + 库检测 + 加成**

定位 `analyze_source_candidate` 内这段（约 1729–1768）：

```python
    explicit_pc = contains_any(combined_text, PC_TERMS)
    has_demo = bool(candidate.demo_url)
    has_market = bool(candidate.market_url)
    has_hap = ".hap" in combined_text.lower() or re.search(r"\bhap\b", combined_text.lower()) is not None

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
    elif score < 40:
        kept = False
        decision = "filtered: score below 40"
```

替换为：

```python
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
```

- [ ] **Step 2: 复用已算的 category 构造 ProjectRecord**

定位 `analyze_source_candidate` 末尾构造 `ProjectRecord(...)` 处（约行 1818–1838），其中 `category=classify_category(combined_text, tech_stack),` 改为复用上面已算的变量：

```python
        category=category,
```

（避免重复计算；其余字段不动。）

- [ ] **Step 3: 语法冒烟**

Run:
```powershell
python -c "import ast; ast.parse(open('scripts/harmony_pc_oss_radar.py',encoding='utf-8').read()); print('syntax OK')"
```
Expected: `syntax OK`

- [ ] **Step 4: 库过滤行为断言（候选路径）**

Run:
```powershell
python -c "import sys; sys.path.insert(0,'scripts'); import harmony_pc_oss_radar as r, datetime as d; c=r.SourceCandidate(source='GitCode',query='q',name='my-sdk',source_url='https://gitcode.com/x/y',repo_url='https://github.com/x/y',description='an sdk for HarmonyOS PC',page_text='HarmonyOS PC tool '*20,stars=1500); rec,aud=r.analyze_source_candidate(c,d.datetime.now(d.timezone.utc)); assert rec is None and 'library/SDK' in aud.decision, (rec,aud.decision); print('OK',aud.decision)"
```
Expected: `OK filtered: library/SDK/package/framework (no runnable artifact)`

- [ ] **Step 5: --help 仍可用**

Run:
```powershell
python scripts/harmony_pc_oss_radar.py --help
```
Expected: 打印 usage。

- [ ] **Step 6: Commit**

```powershell
git add scripts/harmony_pc_oss_radar.py
git commit -m "feat(radar):候选路径接入库过滤与 star/移植加成"
```

---

## Task 5: 同步脚本副本到 .opencode（保持字节一致）

**Files:**
- Modify: `.opencode/skills/harmony-pc-oss-radar/scripts/harmony_pc_oss_radar.py`

- [ ] **Step 1: 复制根脚本到 .opencode 副本**

Run:
```powershell
Copy-Item scripts\harmony_pc_oss_radar.py .opencode\skills\harmony-pc-oss-radar\scripts\harmony_pc_oss_radar.py -Force
```

- [ ] **Step 2: 校验字节一致**

Run:
```powershell
$a=(Get-FileHash scripts\harmony_pc_oss_radar.py -Algorithm MD5).Hash; $b=(Get-FileHash .opencode\skills\harmony-pc-oss-radar\scripts\harmony_pc_oss_radar.py -Algorithm MD5).Hash; Write-Output "root=$a skill=$b"; if($a -eq $b){Write-Output 'SAME'}else{Write-Output 'DIFF'}
```
Expected: 两 hash 相同，输出 `SAME`

- [ ] **Step 3: Commit**

```powershell
git add .opencode\skills\harmony-pc-oss-radar\scripts\harmony_pc_oss_radar.py
git commit -m "chore(skill):同步 radar 脚本到 .opencode 副本"
```

---

## Task 6: 更新 SKILL.md §8/§9/§13（根 + .opencode 副本）

**Files:**
- Modify: `SKILL.md`（根）
- Modify: `.opencode/skills/harmony-pc-oss-radar/SKILL.md`

- [ ] **Step 1: §8 项目保留条件 增补**

在 `SKILL.md` §8 的"`项目必须同时满足：`"列表末尾（`harmony_pc_evidence` 非空那条之后）追加一条：

```markdown
- 必须是终端用户可运行的软件/应用，而非纯库 / SDK / 包 / 框架；纯库类项目即使有开源证据也不进入最终清单。
```

- [ ] **Step 2: §9 项目过滤条件 增补**

在 §9 "满足以下任意条件时过滤" 列表末尾追加一条：

```markdown
- 纯库 / SDK / 包 / 框架，且无可执行产物（无 HAP、无 Release、无应用市场、非 GUI 应用类目）。
```

- [ ] **Step 3: §13 评分规则 增补三档**

在 §13 的"扣分项"列表之后、"推荐解释："之前，插入：

```markdown
知名度加成（仅参与评分，不在输出中展示 star 数）：

- stars ≥ 10000：+12
- stars ≥ 1000：+8
- stars ≥ 100：+4
- stars ≥ 10：+1
- 不足 10 或无数据（GitCode/B站/AppGallery 未 enriched 候选）：0，不扣分。

已有开源软件鸿蒙化加成：

- 命中"移植 / port / 适配 / adaptation / for HarmonyOS / for OpenHarmony / 鸿蒙版 / HarmonyOS port"，且属桌面应用类目：+8。

库类边界降分：

- 命中库 / SDK / 包 / 框架信号，但同时具备可执行产物（HAP / Release / 应用市场 / GUI 应用）：保留，−8，并在 `risk` 标注"疑似库/SDK但含可执行产物,保留并降分"。

证据门控不变：无鸿蒙 PC 证据仍 cap 39，评分 clamp 0..100；知名度与移植加成只在已合格的开源鸿蒙 PC 软件上叠加。
```

- [ ] **Step 4: 同步到 .opencode 副本并校验**

Run:
```powershell
Copy-Item SKILL.md .opencode\skills\harmony-pc-oss-radar\SKILL.md -Force; $a=(Get-FileHash SKILL.md -Algorithm MD5).Hash; $b=(Get-FileHash .opencode\skills\harmony-pc-oss-radar\SKILL.md -Algorithm MD5).Hash; Write-Output "root=$a skill=$b"; if($a -eq $b){Write-Output 'SAME'}else{Write-Output 'DIFF'}
```
Expected: 输出 `SAME`

- [ ] **Step 5: Commit**

```powershell
git add SKILL.md .opencode\skills\harmony-pc-oss-radar\SKILL.md
git commit -m "docs(skill):SKILL.md §8/§9/§13 增补库过滤与知名度/移植加成规则"
```

---

## Task 7: 端到端冒烟（需要 GITHUB_TOKEN；无 token 则跳过 Step 1 改用既有 outputs 复核）

**Files:**
- 无文件改动；仅验证 `outputs/`（不要提交 outputs）

- [ ] **Step 1（有 token）：小规模实跑**

前置：`.env` 已含 `GITHUB_TOKEN`。Run：
```powershell
python scripts/harmony_pc_oss_radar.py --sources github,gitcode --search-profile expanded --include-audit --out-dir outputs --max-results 15 --web-max-results 5 --include-manual-links --format all
```
Expected: 退出码 0；stderr 末行 `[radar] kept N project(s).`

- [ ] **Step 2: 复核审计出现新库过滤决策**

在 `outputs/candidate_audit.csv` 中搜索：
```powershell
Select-String -Path outputs\candidate_audit.csv -Pattern "library/SDK/package/framework"
```
Expected: 至少能搜到被剔库项目行（若本次抓取命中库类）；或无命中也算通过（取决于本次数据）。

- [ ] **Step 3: 复核最终清单无纯库**

检查 `outputs/harmony_pc_oss_list.jsonl` 中每条 `description`/`tech_stack`，确认无纯库/SDK（抽查即可）。同时确认输出列不含 `stars`：
```powershell
Get-Content outputs\harmony_pc_oss_list.csv -TotalCount 1
```
Expected: 表头行无 `stars` 列。

- [ ] **Step 4: 不要提交 outputs**

明确：本任务不 `git add outputs`。如需保留新结果，由用户决定是否提交。

---

## Self-Review（plan 作者自查，已完成）

1. **Spec 覆盖**：spec §4 库过滤 → Task 1 helper + Task 3/4 接线 + Task 6 §9；spec §5 star/移植/库边界 → Task 1 helper + Task 3/4 评分 + Task 6 §13；spec §6 数据流（SourceCandidate.stars + enrichment）→ Task 2；spec §7 SKILL.md 双副本 → Task 5/6；spec §3 不变量（cap 39、clamp、schema 不变）→ Task 3 评分位置 + Task 3 Step 5 断言 `stars not in OUTPUT_FIELDS`。无遗漏。
2. **占位符扫描**：无 TBD/TODO；每个代码步骤都给了完整代码。
3. **类型/命名一致**：`is_library_or_package` 在 Task 1 定义、Task 3/4 调用，签名一致（name, description, topics, has_release, has_hap, has_market, install_methods, category）；`popularity_bonus`/`harmony_port_bonus`/`has_porting_signal` 定义与调用一致；`candidate.stars`/`SourceCandidate.stars` 一致；`category` 变量在 Task 3/4 提前计算并传入 score_record/复用构造 record，一致。
4. **对 spec 的一处细化**：spec §4.1 helper 签名写的是 `combined_text`，本 plan 细化为 `name`+`description`（只扫一行摘要，不扫整篇 README），更符合 spec §4.2"名称/描述正则"本意并显著降低误杀。此细化已写入 Task 1 Step 2 注释。

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-01-scoring-filtering-software-focus.md`. Two execution options:

**1. Subagent-Driven (recommended)** - 每个 Task 派一个新 subagent，任务间复核，迭代快
**2. Inline Execution** - 在当前会话用 executing-plans 批量执行，带检查点

Which approach?
