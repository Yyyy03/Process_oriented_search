---
name: harmony-pc-oss-radar
description: Search, verify, classify, score, and report existing open-source software that can run on HarmonyOS PC / HarmonyOS Computer / OpenHarmony PC / HarmonyOS NEXT PC. Use when Codex needs to discover HarmonyOS PC apps across GitHub, GitCode, Bilibili, and AppGallery, filter non-open-source or non-PC results, run scripts/harmony_pc_oss_radar.py, review evidence, merge sources, and produce CSV, JSONL, or Markdown reports.
---

# Harmony PC OSS Radar

## 1. Skill 名称

`harmony-pc-oss-radar`

## 2. Skill 目标

流程化搜索、发现、验证和整理现有的、可以在鸿蒙 PC / HarmonyOS PC / HarmonyOS Computer / OpenHarmony PC / HarmonyOS NEXT PC 上执行的开源软件。

最终只保留同时满足以下条件的项目：

- 有开源证据：公开源码仓库、明确 LICENSE、README 开源说明、Release 页面或可访问源码目录。
- 有鸿蒙 PC 可执行证据：README、Release、文档、应用市场、B站视频、技术文章或构建说明明确指向 HarmonyOS PC / 鸿蒙 PC / HarmonyOS Computer / OpenHarmony PC / HarmonyOS NEXT PC，或提供 HAP、DevEco、hvigor、ArkTS / Stage Model、Qt for HarmonyOS、Electron for HarmonyOS 等可执行/可构建证据。

没有明确 LICENSE 的项目可以保留，但必须标注 `License 不明确`，降低评分和推荐优先级。

## 3. 适用场景

当用户需要执行以下任务时使用本 Skill：

- 搜索可以在鸿蒙 PC 上运行的开源软件。
- 整理 HarmonyOS PC / HarmonyOS Computer / OpenHarmony PC 可执行开源软件清单。
- 查找可用于 OpenClaw 或其他迁移参考的鸿蒙 PC 项目。
- 周期性更新鸿蒙 PC 开源软件雷达。
- 验证某个项目是否可以在鸿蒙 PC 上执行。
- 对 GitHub、GitCode、B站、应用市场中的鸿蒙 PC 项目进行筛选和评分。

## 4. 不适用场景

不要把以下结果纳入最终清单：

- 闭源软件、纯商业软件、没有源码仓库的软件。
- 只有应用市场页面但没有源码的软件。
- 只有 B站演示但完全找不到源码线索的软件。
- 只支持鸿蒙手机或平板但没有 PC 证据的软件。
- 只支持 Android、Windows、Linux、macOS 但没有鸿蒙 PC 适配证据的软件。
- 只有 issue、讨论、愿景、规划，没有实际代码的软件。
- 仓库为空、README 极少、无法判断的软件。
- 与鸿蒙 PC 无关的普通 OpenHarmony 示例项目。
- 只有一句宣传，没有代码、安装包、构建方式或演示的软件。

最终清单只允许 `confirmed`、`buildable`、`ported-demo` 三种状态；不要输出 `blocked`、`closed-source` 或 `unrelated` 类。

## 5. 输入要求

接受以下输入：

- 搜索主题或搜索关键词。
- 需要覆盖的来源。
- 最大结果数量。
- 是否启用 GitHub token。
- 输出目录。
- 是否生成 GitCode、B站、应用市场人工复核链接。
- 是否生成 CSV / JSONL / Markdown 报告。

如果用户没有指定关键词，自动生成中英文关键词。

## 6. 搜索来源

默认覆盖四类来源：

- GitHub：自动搜索仓库，抓取 README、LICENSE、Release、构建说明、HAP 信息、最近更新时间、描述、语言和技术栈。
- GitCode：生成搜索和复核链接，人工确认项目是否真的面向鸿蒙 PC。
- 鸿蒙 PC 应用市场 / AppGallery：用于验证可安装性；应用市场不等于开源，必须反查源码。
- B站：用于发现运行演示、移植教程和项目线索；视频不能单独证明开源。

可额外扩展 Gitee、CSDN、开发者论坛、OpenHarmony SIG、项目官网等来源。

## 7. 搜索关键词生成规则

自动生成中英文关键词，并结合用户关键词去重。

中文关键词包括：

- 鸿蒙 PC 开源软件
- 鸿蒙 PC 应用 开源
- 鸿蒙 PC HAP
- 鸿蒙 PC DevEco
- 鸿蒙 PC ArkTS
- 鸿蒙 PC Qt
- 鸿蒙 PC Electron
- 鸿蒙 PC 终端
- 鸿蒙 PC Linux
- 鸿蒙 PC 移植
- 鸿蒙电脑 开源软件
- 鸿蒙电脑 应用
- 鸿蒙 PC Markdown
- 鸿蒙 PC 笔记
- 鸿蒙 PC 编辑器
- 鸿蒙 PC 开发工具
- 鸿蒙 PC Shell
- 鸿蒙 PC 包管理器
- 鸿蒙 PC 网络调试
- 鸿蒙 PC SSH
- 鸿蒙 PC Git
- 鸿蒙 PC Rust
- 鸿蒙 PC Go
- 鸿蒙 PC C++
- 鸿蒙 PC Flutter

英文关键词包括：

- HarmonyOS PC open source app
- HarmonyOS Computer open source
- HarmonyOS Computer app
- HarmonyOS NEXT PC app
- OpenHarmony PC app
- OpenHarmony desktop app
- OpenHarmony PC software
- HarmonyOS HAP PC
- ArkTS desktop app
- ohos qt
- ohos electron
- ohos markdown
- ohos terminal
- HarmonyOS PC terminal
- HarmonyOS PC Qt
- HarmonyOS PC Electron
- HarmonyOS PC DevEco
- HarmonyOS PC hvigor
- HarmonyOS PC HAP
- HarmonyOS Computer terminal
- OpenHarmony PC Qt
- OpenHarmony PC Electron

## 8. 项目保留条件

项目必须同时满足：

- `open_source_evidence` 非空：仓库 URL、LICENSE、README 开源说明、Release、源码目录结构等。
- `harmony_pc_evidence` 非空：明确 PC 文案、HAP、DevEco / hvigor / ArkTS / Stage Model、Qt / Electron for HarmonyOS 构建方式、B站运行演示、文章截图或步骤等。

优先寻找的软件类型：

- 原生鸿蒙 PC 应用：ArkTS、Stage Model、HAP、DevEco、hvigor。
- 桌面软件移植项目：Qt、Electron、WebView、C/C++、Rust、Go、Flutter。
- 终端与运行环境：终端模拟器、Shell、Linux binary 运行环境、类 Termux 环境、包管理器、命令行工具。
- 开发工具：IDE、编辑器、Markdown、Git、SSH、网络调试、语言工具链。
- 普通桌面应用：笔记、音乐、视频、文件管理、办公、效率工具、剪贴板、截图。

## 9. 项目过滤条件

满足以下任意条件时过滤，不进入最终清单：

- 缺少源码仓库或源码不可访问。
- 缺少鸿蒙 PC 可执行/可构建/可运行证据。
- 只有应用市场页面，没有源码。
- 只有视频演示，找不到源码或上游仓库线索。
- 只有普通 OpenHarmony 手机/平板证据，没有 PC、desktop、computer 或移植证据。
- 仅概念、路线图、issue、讨论帖，无实际代码。
- 仓库空、README 极少、无法判断。

## 10. 项目分类规则

- `confirmed`：明确可以在鸿蒙 PC 上执行。证据包括 README 明确写 HarmonyOS PC / 鸿蒙 PC / HarmonyOS Computer / OpenHarmony PC、有 HAP / Release / 应用市场入口、有 DevEco / hvigor / qmake / cmake 构建说明、有 B站或文章演示。
- `buildable`：有源码和构建方式，看起来可以在鸿蒙 PC 上构建或运行，但缺少强运行证据。证据包括完整 DevEco 工程、`oh-package.json5`、`hvigor`、`entry/src/main/ets`、Qt / Electron / ArkTS for HarmonyOS 构建说明。
- `ported-demo`：已有移植或运行展示，但鸿蒙适配源码、安装包或构建流程可能不完整。证据包括 B站、文章、论坛、截图或视频，并且能找到项目源码或上游源码线索。

## 11. 证据抽取规则

每个保留项目必须抽取两类证据：

- `open_source_evidence`：GitHub / GitCode / Gitee 仓库 URL、LICENSE 文件、README 开源说明、Release 页面、源码目录结构。
- `harmony_pc_evidence`：HarmonyOS PC / 鸿蒙 PC / HarmonyOS Computer / OpenHarmony PC 文案、HAP、DevEco / hvigor、ArkTS / Stage Model、Qt for HarmonyOS、Electron for HarmonyOS、B站运行演示、文章运行截图或步骤。

缺少任意一类证据时原则上删除。不要伪造无法抓取或无法确认的证据。

## 12. 去重与多来源合并规则

按以下依据合并重复项目：

- 仓库 URL 相同。
- 项目名称高度相似。
- README 指向同一个上游项目。
- B站视频指向同一个仓库。
- 应用市场名称与仓库名称明显对应。
- GitCode 项目与 GitHub 上游项目明显对应。

合并时保留所有来源字段和证据：`repo_url`、`market_url`、`demo_url`、`article_url`、`source`、`harmony_pc_evidence`、`open_source_evidence`。如果 GitHub 和 B站证明同一项目，把 B站作为 `demo_url` 或运行证据，不要创建重复记录。

## 13. 评分规则

使用 100 分制，低于 40 分的结果一般不进入最终清单，除非证据特殊重要。

加分项：

- 明确写支持 HarmonyOS PC / 鸿蒙 PC / HarmonyOS Computer：+25
- 有公开源码仓库：+20
- 有明确开源 License：+10
- 有 HAP / Release / 安装包：+15
- 有 DevEco / hvigor / qmake / cmake 构建说明：+10
- 有 B站或其他运行演示：+10
- 最近 12 个月仍有维护：+5
- 技术栈适合鸿蒙 PC 迁移：+5

扣分项：

- License 不明确：-10
- 只有视频演示，缺少鸿蒙适配源码：-15
- 只有源码，但没有明确 PC 运行证据：-10
- 构建步骤不完整：-10
- 依赖高权限或系统能力：-15
- 长期不维护：-10
- README 信息较少：-10

推荐解释：

- 80-100：优先验证
- 60-79：值得关注
- 40-59：候选观察
- 低于 40：一般过滤

## Bundled resources

Use the bundled files as follows:

- Run `scripts/harmony_pc_oss_radar.py` for deterministic search, evidence extraction, scoring, and CSV / JSONL / Markdown generation.
- Read `references/research/search_system_technical_design.md` when the user asks about the system architecture, pipeline, evidence model, or how to extend the project.
- Read `references/research/source_strategy.md` when tuning GitHub, GitCode, B站, AppGallery searches or reviewing source-specific evidence quality.
- Use `examples/` only as output shape examples; example rows are not verified real projects.
- Use `assets/harmony-pc-oss-radar.svg` as the bundled visual asset for documentation, cards, or marketplace-style presentation.

## 14. Python 程序使用方式

`scripts/harmony_pc_oss_radar.py` 是本 Skill 的自动化执行工具。

Python 程序负责：

- 批量搜索 GitHub。
- 批量抓取 README、LICENSE、Release、目录结构。
- 初步过滤、分类和评分。
- 生成 CSV、JSONL、Markdown 报告。
- 生成 GitCode、B站、鸿蒙应用市场人工复核链接。

Agent / Skill 负责：

- 生成更好的搜索关键词。
- 判断模糊证据。
- 人工复核 GitCode、B站、应用市场结果。
- 修正 Python 程序误判。
- 合并多来源证据。
- 删除证据不足项目。
- 生成最终优先级建议和报告。

Agent 应优先运行 Python 程序获得基础结果，再读取 JSONL 进行人工或 LLM 复核。

## 15. Python 程序命令示例

```bash
python scripts/harmony_pc_oss_radar.py \
  --sources all \
  --query "鸿蒙 PC 开源软件" \
  --query "HarmonyOS PC open source app" \
  --query "OpenHarmony PC app" \
  --out-dir outputs \
  --max-results 30 \
  --include-manual-links \
  --format all
```

扩大召回并生成候选审计：

```bash
python scripts/harmony_pc_oss_radar.py \
  --sources all \
  --search-profile expanded \
  --include-code-search \
  --include-audit \
  --out-dir outputs \
  --max-results 50 \
  --code-max-results 30 \
  --web-max-results 20 \
  --include-manual-links \
  --format all
```

使用 GitHub token：在当前运行目录的 `.env` 中填写 `GITHUB_TOKEN`，再直接运行脚本。命令行参数 `--github-token` 仍可作为临时覆盖方式。

`.env` 示例：

```dotenv
GITHUB_TOKEN=github_pat_xxx
```

```bash
python scripts/harmony_pc_oss_radar.py \
  --sources all \
  --query "HarmonyOS Computer app" \
  --out-dir outputs \
  --format all
```

如果 `.env` 不在当前运行目录，使用：

```bash
python scripts/harmony_pc_oss_radar.py \
  --sources all \
  --query "HarmonyOS Computer app" \
  --out-dir outputs \
  --env-file /path/to/.env \
  --format all
```

## 16. Python 输出文件说明

- `outputs/harmony_pc_oss_list.csv`：表格查看、排序和人工筛选。
- `outputs/harmony_pc_oss_list.jsonl`：结构化数据，Agent 应优先读取它继续合并和复核。
- `outputs/harmony_pc_oss_report.md`：可直接阅读和汇报的 Markdown 报告。
- `outputs/manual_review_links.csv`：GitCode、B站、鸿蒙应用市场搜索链接和复核入口。
- `outputs/candidate_audit.csv`：启用 `--include-audit` 时生成，记录 GitHub 候选仓库、保留/过滤原因、证据、风险和分数。它是调参和人工复核文件，不是最终清单。
- `outputs/source_candidates_raw.jsonl`：GitCode、B站、AppGallery 抓到的原始候选，包含被过滤项目和动态页/验证码提示。
- `outputs/gitcode_candidates.csv`：GitCode 搜索候选，优先来自 GitCode 公开搜索 API。
- `outputs/bilibili_candidates.csv`：B站搜索候选，视频只能作为运行证据，必须反查源码仓库。
- `outputs/appgallery_candidates.csv`：应用市场候选，只能作为可安装线索，必须反查源码仓库。

## 17. Skill 与 Python 程序的分工

Python 程序做可自动验证的工作：GitHub API 搜索、GitCode 搜索 API 抓取、B站/AppGallery 候选页面抓取、仓库元数据抓取、保守证据抽取、初步评分和输出。

Skill/Agent 做需要判断的工作：浏览器复核动态页/验证码页、跨来源合并、确认 AppGallery 是否对应开源项目、确认 B站视频是否能关联源码、处理中文文章和论坛证据、给出最终建议。

## 18. Agent 如何读取和复核 Python 输出

执行后优先读取 `outputs/harmony_pc_oss_list.jsonl`，逐行检查：

- `open_source_evidence` 是否足够。
- `harmony_pc_evidence` 是否真实指向 PC，而不是手机或平板。
- `status` 是否只为 `confirmed`、`buildable`、`ported-demo`。
- `risk` 是否覆盖 License、构建步骤、权限、维护状态、README 稀少等风险。
- `score` 与证据强弱是否匹配。

再读取 `outputs/source_candidates_raw.jsonl`、各来源 candidates CSV 和 `outputs/manual_review_links.csv`，对 GitCode、B站、应用市场结果进行复核。只有复核后同时满足开源证据和鸿蒙 PC 证据的项目，才能合并进最终清单。

## 19. 异常处理方式

- GitHub API 限额不足：提示在 `.env` 中设置 `GITHUB_TOKEN`，减少关键词数量，或降低 `--max-results`。
- GitCode、B站、应用市场无法自动抓取：写入 raw/audit 文件并生成人工复核链接，标注动态页、验证码或 `needs_manual_review`，不得伪造结果。
- License 不明确：可保留，`risk` 标注 `License 不明确`，评分扣分，不作为最高优先级推荐。
- 只有应用市场页面但没有源码：不进入最终清单。
- 只有 B站演示但找不到源码：不进入 `confirmed`；只有能找到源码或上游仓库线索时才可进入 `ported-demo`。
- 程序无法访问网络：清楚提示错误，不生成伪造结果；可以只生成 `manual_review_links.csv`。

## 20. 最终输出格式

CSV 字段：

`name, category, status, score, source, repo_url, market_url, demo_url, article_url, license, description, tech_stack, build_method, install_method, harmony_pc_evidence, open_source_evidence, risk, recommendation, last_checked`

JSONL 每行一个项目，字段同上。

Markdown 报告结构：

```markdown
# 鸿蒙 PC 可执行开源软件清单

## 一、confirmed：已确认可执行
## 二、buildable：源码可构建，需进一步验证
## 三、优先验证建议
```

Markdown 报告不单列 `ported-demo` 空章节。每个项目写明项目名称、简介、源码地址、运行证据、开源证据、技术栈、安装/构建方式、风险、推荐程度。

## 21. 执行步骤

1. 理解用户目标：只寻找现有的、可以在鸿蒙 PC 上执行的开源软件。
2. 生成中英文搜索关键词。
3. 先运行 `scripts/harmony_pc_oss_radar.py --sources all`；如果结果过少，使用 `--search-profile expanded --include-code-search --include-audit --web-max-results 20` 扩大召回。
4. 读取 `outputs/harmony_pc_oss_list.jsonl`。
5. 检查每个项目是否同时具备开源证据和鸿蒙 PC 可执行证据。
6. 删除证据不足的项目。
7. 如果存在 `outputs/candidate_audit.csv`，检查被过滤项目的 `decision`，找出可人工补证据的项目。
8. 读取 `outputs/source_candidates_raw.jsonl`、`outputs/gitcode_candidates.csv`、`outputs/bilibili_candidates.csv`、`outputs/appgallery_candidates.csv` 和 `outputs/manual_review_links.csv`。
9. 人工或浏览器复核 GitCode、B站、应用市场结果，尤其是验证码、动态渲染和缺少源码链接的候选。
10. 将人工复核结果合并回项目清单。
11. 对重复项目进行合并。
12. 修正 `status`、`score`、`risk`、`recommendation`。
13. 输出最终 CSV、JSONL 和 Markdown 报告。
14. 给出优先验证建议。

## 22. 复核注意事项

- 不要把鸿蒙手机应用直接等同于鸿蒙 PC 应用。
- 不要把应用市场可安装直接等同于开源。
- 不要把 B站演示直接等同于源码可用。
- 每个保留项目必须至少有一种开源证据和一种鸿蒙 PC 可执行证据。
- 所有判断都要保守；证据不足的项目直接过滤。
- 不确定但有价值的项目只能在证据足够时放入 `buildable` 或 `ported-demo`。
- 人工复核时保留 URL、截图/页面标题、关键词命中位置和检查日期。

## 23. 验收标准

交付必须包含：

- `SKILL.md`
- `agents/openai.yaml`
- `README.md`
- `LICENSE`
- `requirements.txt`
- `scripts/harmony_pc_oss_radar.py`
- `references/research/search_system_technical_design.md`
- `references/research/source_strategy.md`
- `assets/harmony-pc-oss-radar.svg`
- `examples/sample_output.csv`
- `examples/sample_output.jsonl`
- `examples/sample_report.md`

验收时确认：

- `SKILL.md` 明确说明如何使用 Python 程序。
- Python 程序可以运行。
- README 包含安装和运行命令。
- 输出字段完整。
- 最终清单只保留 `confirmed`、`buildable`、`ported-demo`。
- 不包含 `closed-source`、`blocked`、`unrelated` 项目。
- 每个保留项目都有开源证据和鸿蒙 PC 可执行证据。
- 不伪造无法访问的 GitCode、B站、应用市场结果。
- 示例输出结构完整。
- 代码便于后续扩展 Playwright、LLM 分析、SQLite 存储和 GitHub Actions 周期运行。
