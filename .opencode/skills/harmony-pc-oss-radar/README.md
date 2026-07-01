# Harmony PC OSS Radar

`harmony-pc-oss-radar` 用于流程化搜索、发现、验证和整理现有的、可以在鸿蒙 PC / HarmonyOS PC / HarmonyOS Computer / OpenHarmony PC / HarmonyOS NEXT PC 上执行的开源软件。

它的默认策略是保守过滤：最终清单只保留同时具备开源证据和鸿蒙 PC 可执行/可构建证据的项目，不统计闭源软件、纯商业软件、普通手机应用、只有概念规划的项目，或无法证明可运行的项目。

## 作为 Codex Skill 使用

这个项目现在也是一个可复用的 Codex Skill。核心 skill 文件和资源包括：

```text
harmony-pc-oss-radar/
├── assets/
│   └── harmony-pc-oss-radar.svg
├── agents/
│   └── openai.yaml
├── examples/
│   ├── sample_output.csv
│   ├── sample_output.jsonl
│   └── sample_report.md
├── references/
│   └── research/
│       ├── search_system_technical_design.md
│       └── source_strategy.md
├── scripts/
│   └── harmony_pc_oss_radar.py
├── LICENSE
├── README.md
├── SKILL.md
└── requirements.txt
```

其中 `SKILL.md` 定义 Agent 工作流，`scripts/harmony_pc_oss_radar.py` 是自动化搜索、抓取、过滤、评分和输出工具，`references/research/` 存放技术框架和来源复核策略，`assets/` 存放 Skill 资产，`agents/openai.yaml` 提供 Skill 列表中的显示名称和默认提示。

### 安装到 Codex Skill 目录

在 PowerShell 中执行：

```powershell
$skillHome = "$env:USERPROFILE\.codex\skills\harmony-pc-oss-radar"
New-Item -ItemType Directory -Force -Path $skillHome | Out-Null
robocopy . $skillHome /E /XD .git .venv outputs .opencode __pycache__ /XF .env *.pyc
```

安装后可以在 Codex 中这样调用：

```text
Use $harmony-pc-oss-radar to search for HarmonyOS PC open-source software, run the radar script, review evidence, and produce final CSV, JSONL, and Markdown reports.
```

### OpenCode 使用方式

项目里已经保留 OpenCode skill 副本，并同步为可独立读取的标准结构：

```text
.opencode/skills/harmony-pc-oss-radar/
```

在项目根目录运行 `opencode` 后，可以输入：

```text
Use harmony-pc-oss-radar to search for existing open-source software that can run on HarmonyOS PC. Run the Python radar script, review outputs, and summarize candidates with evidence and risks.
```

## 适合场景

- 整理鸿蒙 PC 可执行开源软件清单。
- 定期扫描 HarmonyOS PC / OpenHarmony PC 相关项目。
- 为 OpenClaw 或其他迁移工作寻找参考项目。
- 初步验证某个项目是否具备鸿蒙 PC 运行或构建线索。
- 生成 CSV、JSONL、Markdown 报告，供人工二次复核。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 快速运行

默认即最大召回：合并全部内置中英文关键词（expanded）、启用 GitHub code search、覆盖 GitHub / GitCode / B站 / AppGallery，并生成审计与人工复核链接。不限制搜索时间，会大量消耗 GitHub API 限额，务必先在 `.env` 中配置 `GITHUB_TOKEN`。

```bash
python scripts/harmony_pc_oss_radar.py \
  --sources all \
  --search-profile expanded \
  --include-code-search \
  --include-audit \
  --out-dir outputs \
  --max-results 200 \
  --code-max-results 100 \
  --web-max-results 50 \
  --include-manual-links \
  --format all
```

`--include-audit` 会额外生成 `outputs/candidate_audit.csv`，里面包含已保留和被过滤的候选仓库，以及过滤原因（含纯库/SDK/包/框架剔除）。这个文件用于调参和人工复核，不等同于最终清单。

如果不提供 `--query`，expanded 模式会使用全部内置中英文关键词；想补充自定义关键词时可追加 `--query "xxx"`，它会与内置关键词合并。

## 为什么结果可能很少

结果少通常不是因为生态里只有十几个项目，而是多个保守条件叠加导致：

- GitHub 仓库搜索默认是关键词 AND 逻辑，长查询会漏掉很多只写了部分关键词的仓库。
- 传入 `--query` 后，默认关键词不会自动参与；如果只传 3-6 个关键词，召回面会很窄。
- GitCode、B站、AppGallery 会抓取候选，但最终仍必须通过“开源证据 + 鸿蒙 PC 证据”过滤；动态页、验证码页会进入 raw/audit 等待复核。
- 最终清单必须同时具备开源证据和鸿蒙 PC 可执行/可构建证据，普通 HarmonyOS 手机应用会被过滤。
- 脚本为了避免伪造结果，会过滤没有明确证据的项目；一些真实项目可能需要人工从文章、视频简介、评论或应用市场反查源码后再合并。

建议流程是：先用扩展搜索生成 `candidate_audit.csv`、`source_candidates_raw.jsonl` 和 `manual_review_links.csv`，再人工复核弱证据项目，把满足条件的项目合并回最终清单。

## 使用 GitHub Token

GitHub 未认证 API 有较低限额。推荐把 token 写入当前运行目录的 `.env` 文件。仓库里已经提供 `.env` 模板：

```dotenv
GITHUB_TOKEN=
```

把 `GITHUB_TOKEN=` 后面改成你的 GitHub Personal Access Token：

```dotenv
GITHUB_TOKEN=github_pat_xxx
```

然后直接运行：

```bash
python scripts/harmony_pc_oss_radar.py \
  --query "HarmonyOS Computer app" \
  --out-dir outputs \
  --format all
```

默认读取顺序是：

1. `--github-token` 命令行参数。
2. 系统环境变量 `GITHUB_TOKEN`。
3. 当前运行目录下的 `.env` 文件。

如果 `.env` 不在当前运行目录，可以显式指定：

```bash
python scripts/harmony_pc_oss_radar.py \
  --query "HarmonyOS Computer app" \
  --out-dir outputs \
  --env-file "D:/project/Process_oriented_search/.env" \
  --format all
```

也仍然可以直接设置环境变量：

```bash
export GITHUB_TOKEN="your_token"
```

Windows PowerShell：

```powershell
$env:GITHUB_TOKEN="your_token"
```

## 参数说明

- `--query`：添加搜索关键词，可以多次使用。
- `--out-dir`：指定输出目录，默认 `outputs`。
- `--sources`：搜索来源，默认 `all`，可写 `github`、`gitcode`、`bilibili`、`appgallery` 或逗号组合，例如 `github,gitcode`。
- `--search-profile`：搜索策略，`focused` 为默认策略，`expanded` 会追加默认关键词和扩展召回关键词。
- `--max-results`：每个关键词最多返回的 GitHub 仓库数，默认 30；设为 0 时只生成复核链接。
- `--web-max-results`：每个关键词每个非 GitHub 来源最多抓取的候选数，默认 10。
- `--web-timeout`：GitCode、B站、AppGallery 请求超时时间，默认 20 秒。
- `--github-token`：可选 GitHub token；优先级高于环境变量和 `.env`。
- `--env-file`：指定 `.env` 文件路径，默认读取当前运行目录下的 `.env`。
- `--include-manual-links`：生成 GitCode、B站、AppGallery 人工复核链接。
- `--include-code-search`：启用 GitHub code search，查找 README、配置文件、构建文件中的鸿蒙 PC 短语。
- `--code-max-results`：每个 code search 查询最多返回的结果数，默认 20。
- `--include-audit`：生成 `candidate_audit.csv`，记录候选项目保留或过滤原因。
- `--enrich-external-github` / `--no-enrich-external-github`：对 GitCode/B站/AppGallery 中发现的 GitHub 链接补抓 GitHub README、LICENSE、Release 和目录结构，默认启用。
- `--format`：输出格式，可选 `csv`、`jsonl`、`md`、`all`。
- `--since`：只关注某日期之后更新的仓库，格式 `YYYY-MM-DD`。
- `--min-score`：过滤低分结果，默认 40。

## 输出文件

- `outputs/harmony_pc_oss_list.csv`：适合表格查看、排序和人工筛选。
- `outputs/harmony_pc_oss_list.jsonl`：结构化结果，适合 Agent 或后续程序继续读取、合并、复核。
- `outputs/harmony_pc_oss_report.md`：直接阅读和汇报用的 Markdown 报告。
- `outputs/manual_review_links.csv`：GitCode、B站、鸿蒙应用市场的搜索链接和复核入口。
- `outputs/candidate_audit.csv`：可选审计文件，记录 GitHub 候选仓库、分数、证据、风险和过滤原因。
- `outputs/source_candidates_raw.jsonl`：GitCode、B站、AppGallery 抓到的原始候选，包含被过滤项目和动态页/验证码提示。
- `outputs/gitcode_candidates.csv`：GitCode 搜索候选，优先来自 GitCode 公开搜索 API。
- `outputs/bilibili_candidates.csv`：B站搜索候选，视频只能作为运行证据，必须反查源码仓库。
- `outputs/appgallery_candidates.csv`：应用市场候选，只能作为可安装线索，必须反查源码仓库。

输出字段包括：

`name, category, status, score, source, repo_url, market_url, demo_url, article_url, license, description, tech_stack, build_method, install_method, harmony_pc_evidence, open_source_evidence, risk, recommendation, last_checked`

## 状态含义

- `confirmed`：已有明确鸿蒙 PC / HarmonyOS Computer / OpenHarmony PC 运行、安装或构建证据。
- `buildable`：源码和构建方式较完整，看起来可以构建或迁移到鸿蒙 PC，但还缺少强运行证据。
- `ported-demo`：内部候选状态，表示已有移植或运行演示，并能找到源码或上游源码线索；Markdown 报告不再单列这个章节。

最终结果不会输出 `closed-source`、`blocked`、`unrelated`。

## 人工复核 GitCode / B站 / 应用市场

程序会抓取 GitCode、B站和 AppGallery 候选，但最终清单仍保守过滤。GitCode 优先使用公开搜索 API；B站和 AppGallery 页面可能触发验证码或动态渲染，脚本会把这种情况写入 raw/audit 文件，不会伪造成有效项目。

推荐复核流程：

1. 打开 `outputs/manual_review_links.csv`。
2. 打开 `outputs/source_candidates_raw.jsonl` 和各来源 candidates CSV。
3. 对 GitCode 结果确认仓库、LICENSE、README、构建方式和鸿蒙 PC 证据。
4. 对 B站结果只把视频作为运行证据，继续反查简介、评论、项目名和源码仓库。
5. 对 AppGallery 结果只把应用市场作为可安装线索，必须反查 GitHub / GitCode / Gitee 等源码仓库。
6. 只有同时具备开源证据和鸿蒙 PC 可执行证据的项目，才合并进最终清单。

## 扩展新的搜索来源

当前脚本集中在单文件中，方便 MVP 使用。后续可以拆分：

- `sources/github.py`：GitHub 搜索和仓库抓取。
- `sources/gitcode.py`：GitCode 搜索和页面解析。
- `sources/bilibili.py`：B站搜索、视频简介、项目线索抽取。
- `sources/appgallery.py`：应用市场搜索和应用元数据。
- `analyzer/evidence_extractor.py`：证据抽取。
- `analyzer/classifier.py`：状态分类。
- `analyzer/scorer.py`：评分。
- `output/`：CSV、JSONL、Markdown、SQLite 或其他输出。

增加新来源时请保持同一原则：不能自动确认的内容只生成复核链接或标注 `needs_manual_review`，不要伪造结果。

## 当前限制

- GitHub 和 GitCode 自动化程度较高。
- B站和 AppGallery 容易出现验证码、动态渲染或反爬；脚本会记录候选和复核入口，但不会伪造详情。
- 自动判断偏保守，可能漏掉真实项目。
- 仅凭 ArkTS、DevEco、hvigor 结构无法证明 PC 可执行；仍需结合 README、Release、演示或文章复核。
- GitHub/GitCode 搜索结果受 API 限额、网络质量和关键词质量影响。

## 常见问题

**GitHub API 限额不足怎么办？**

在 `.env` 中填写 `GITHUB_TOKEN`，减少关键词数量，或降低 `--max-results`。

**为什么没有输出项目？**

脚本只保留同时具备开源证据和鸿蒙 PC 证据的结果。可以扩大关键词、降低 `--min-score`，或从 `manual_review_links.csv` 人工复核后手动合并。

**只有应用市场页面的项目能进入清单吗？**

不能。应用市场可安装不等于开源，必须找到公开源码仓库。

**只有 B站演示的项目能进入清单吗？**

不能直接进入。B站只能作为运行证据，还必须找到源码或上游仓库线索。

**没有明确 License 的项目怎么办？**

可以保留，但必须标注 `License 不明确`，评分扣分，不作为最高优先级推荐。

## 示例文件

`examples/` 目录提供结构示例：

- `examples/sample_output.csv`
- `examples/sample_output.jsonl`
- `examples/sample_report.md`

这些示例记录均为 `example only`，用于展示字段结构，不代表已验证真实项目。
