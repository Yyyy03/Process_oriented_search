# 鸿蒙 PC 开源软件搜索整理系统技术文档

## 1. 目标

本系统用于流程化搜索、发现、验证和整理现有的、可以在鸿蒙 PC / HarmonyOS PC / HarmonyOS Computer / OpenHarmony PC / HarmonyOS NEXT PC 上执行的开源软件。

系统的核心原则是保守筛选：最终清单必须同时具备开源证据和鸿蒙 PC 可执行、可构建或可运行证据。只有应用市场页面、只有视频演示、只有手机端适配、只有概念说明或没有源码线索的结果，不进入最终清单。

## 2. 总体架构

```text
搜索关键词
  ↓
多来源抓取
  ├─ GitHub 仓库搜索
  ├─ GitHub Code Search
  ├─ GitCode 搜索 API
  ├─ B站搜索候选
  └─ AppGallery / 鸿蒙应用市场候选
  ↓
候选归一化
  ↓
证据抽取
  ├─ 开源证据
  └─ 鸿蒙 PC 证据
  ↓
过滤、分类、评分
  ↓
去重与多来源合并
  ↓
CSV / JSONL / Markdown 报告
```

## 3. 主要模块

### 3.1 命令行入口

主程序为：

```text
scripts/harmony_pc_oss_radar.py
```

它负责解析参数、组织搜索计划、调用各来源抓取器、合并候选、执行过滤评分并生成输出文件。

常用参数包括：

- `--sources`：选择搜索来源，默认 `all`，支持 `github,gitcode,bilibili,appgallery`。
- `--search-profile`：选择搜索策略，`focused` 为基础搜索，`expanded` 会追加扩展关键词。
- `--include-code-search`：启用 GitHub Code Search。
- `--include-audit`：生成候选审计文件。
- `--max-results`：控制 GitHub 每个关键词的结果数量。
- `--web-max-results`：控制 GitCode、B站、AppGallery 每个关键词的候选数量。
- `--min-score`：过滤低分项目。

### 3.2 GitHub 抓取

GitHub 是自动化程度最高的数据源。系统会调用 GitHub API 搜索仓库，并抓取：

- 仓库描述
- README
- LICENSE
- Release
- Release 资产名
- 源码目录树
- 最近更新时间
- 语言和 topics

GitHub Code Search 用于补充普通仓库搜索漏掉的项目，重点查找：

- `HarmonyOS PC`
- `HarmonyOS Computer`
- `OpenHarmony PC`
- `Qt for HarmonyOS`
- `Electron for HarmonyOS`
- `oh-package.json5`
- `hvigorfile.ts`
- `module.json5`
- `build-profile.json5`

### 3.3 GitCode 抓取

GitCode 优先使用公开搜索 API：

```text
https://gitcode.com/api/v1/search/nauth/query
```

系统会抽取：

- GitCode 仓库 URL
- 项目名和命名空间
- 项目描述
- 主语言
- tags / topic_names
- License 线索
- 上游或导入的 GitHub 仓库链接

GitCode 结果仍需经过同一套过滤规则。普通 OpenHarmony 示例、没有 PC 证据、没有源码证据或 License 不明确的项目会被降权或过滤。

### 3.4 B站抓取

B站用于发现运行演示、移植教程和项目线索。系统会尝试抓取搜索候选和视频链接，并从标题、页面文本和链接中抽取：

- 视频 URL
- 项目名线索
- GitHub / GitCode / Gitee 仓库链接
- HAP、移植、HarmonyOS PC、鸿蒙 PC 等运行证据

B站视频不能单独证明开源。只有能关联到源码仓库，并具备鸿蒙 PC 运行或移植证据时，才可能进入最终清单。

B站经常返回 `412` 或验证码页面。系统遇到这种情况会写入候选和审计文件，标注需要浏览器或人工复核，不会伪造详情。

### 3.5 AppGallery / 鸿蒙应用市场抓取

AppGallery 用于发现“可能可安装”的应用线索。系统会尝试抓取搜索页和应用页候选，并记录：

- 应用市场链接
- 应用名线索
- 页面描述
- 可能出现的源码仓库链接

应用市场可安装不等于开源。没有 GitHub、GitCode、Gitee 或其他公开源码仓库的应用，不进入最终清单。

## 4. 搜索关键词策略

系统内置中英文关键词，覆盖：

- 鸿蒙 PC 开源软件
- HarmonyOS PC open source app
- HarmonyOS Computer app
- OpenHarmony PC app
- HarmonyOS PC Qt
- HarmonyOS PC Electron
- HarmonyOS PC DevEco
- HarmonyOS PC hvigor
- HarmonyOS HAP PC
- ohos qt
- ohos electron
- oh-package.json5 HarmonyOS
- hvigorfile HarmonyOS
- entry/src/main/ets HarmonyOS

`--search-profile expanded` 会在用户关键词基础上追加默认关键词和扩展关键词，提高召回率。

## 5. 证据模型

### 5.1 开源证据

项目必须至少具备一种开源证据：

- GitHub / GitCode / Gitee 仓库 URL
- LICENSE 文件或 License 字段
- README 可访问
- Release 页面可访问
- 源码目录结构可访问

没有明确 License 的项目可以保留，但会标注 `License 不明确` 并扣分。

### 5.2 鸿蒙 PC 证据

项目必须至少具备一种鸿蒙 PC 证据：

- 明确出现 `HarmonyOS PC`、`HarmonyOS Computer`、`OpenHarmony PC`、`鸿蒙 PC`、`鸿蒙电脑`
- 提供 HAP 安装包或 HAP 线索
- 提供 DevEco、hvigor、ArkTS、Stage Model 工程结构
- 提供 Qt for HarmonyOS / Qt for OpenHarmony 构建说明
- 提供 Electron for HarmonyOS / Electron for OpenHarmony 构建说明
- B站、文章或论坛中有运行演示，并能反查源码
- AppGallery 有安装线索，并能反查源码

## 6. 过滤逻辑

候选项目会被过滤的典型原因包括：

- 没有源码仓库链接
- 没有鸿蒙 PC 可执行或可构建证据
- 只有 B站演示但找不到源码
- 只有应用市场页面但找不到源码
- 只有普通 HarmonyOS 手机端证据
- README 信息过少
- 构建步骤不完整
- License 不明确且其他证据较弱
- 分数低于 `--min-score`

过滤原因会写入：

```text
outputs/candidate_audit.csv
```

## 7. 分类与评分

当前报告只展示两个主要分类：

- `confirmed`：证据较强，已明确支持鸿蒙 PC，或具备 HAP / Release / 应用市场 / 演示 / 构建说明等强证据。
- `buildable`：有源码和构建方式，看起来可以在鸿蒙 PC 上构建或迁移，但还需要进一步验证。

评分采用 100 分制，主要加分项包括：

- 明确写支持 HarmonyOS PC / 鸿蒙 PC / HarmonyOS Computer
- 有公开源码仓库
- 有明确 License
- 有 HAP / Release / 安装包
- 有 DevEco / hvigor / qmake / cmake 构建说明
- 有 B站或文章运行演示
- 最近仍在维护
- 技术栈适合鸿蒙 PC 迁移

主要扣分项包括：

- License 不明确
- 缺少明确 PC 运行证据
- 构建步骤不完整
- 依赖高权限或系统能力
- README 信息较少
- 长期未维护

## 8. 去重与合并

系统按仓库 URL 做主去重依据。来自多个来源的同一项目会合并：

- GitHub 仓库作为 `repo_url`
- AppGallery 链接作为 `market_url`
- B站链接作为 `demo_url`
- 文章或论坛链接作为 `article_url`
- 多来源证据合并到 `harmony_pc_evidence` 和 `open_source_evidence`

如果 B站或 AppGallery 中发现 GitHub 仓库链接，系统会补抓 GitHub README、LICENSE、Release 和目录结构，提高判断质量。

## 9. 输出文件

当前建议保留的输出文件：

- `harmony_pc_oss_list.csv`：最终结构化清单，适合表格筛选。
- `harmony_pc_oss_list.jsonl`：最终结构化清单，适合程序和 Agent 继续处理。
- `harmony_pc_oss_report.md`：最终可读报告。
- `candidate_audit.csv`：候选审计表，记录保留和过滤原因。
- `search_system_technical_design.md`：本技术文档。

中间候选文件如 `source_candidates_raw.jsonl`、`gitcode_candidates.csv`、`bilibili_candidates.csv`、`appgallery_candidates.csv`、`manual_review_links.csv` 适合调试和人工复核。完成一次整理后，如果只保留最终交付结果，可以删除这些中间文件。

## 10. 当前限制

- B站容易触发 `412`、验证码或风控，视频详情需要浏览器复核。
- AppGallery 多为动态渲染页面，自动抓取不一定能拿到完整应用详情。
- GitCode API 可用性比页面解析好，但仍可能受网络、风控和字段变化影响。
- 自动证据抽取偏保守，可能漏掉真实项目。
- 自动结果中仍可能有误判，需要人工复核高分项目和关键来源。

## 11. 推荐使用流程

1. 配置 `.env` 中的 `GITHUB_TOKEN`。
2. 执行扩展多来源搜索。
3. 查看 `harmony_pc_oss_report.md` 的高分项目。
4. 用 `candidate_audit.csv` 检查被过滤但可能有价值的项目。
5. 对 B站和 AppGallery 结果做人工或浏览器复核。
6. 将确认具备源码和鸿蒙 PC 证据的项目合并回最终清单。
7. 删除中间候选文件，只保留最终清单、报告、审计和技术文档。
