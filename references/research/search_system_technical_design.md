# 鸿蒙 PC 开源软件搜索整理系统技术框架

## 目标

本系统用于流程化搜索、发现、验证和整理现有的、可以在鸿蒙 PC / HarmonyOS PC / HarmonyOS Computer / OpenHarmony PC / HarmonyOS NEXT PC 上执行的开源软件。

核心原则是保守筛选：最终清单必须同时具备开源证据和鸿蒙 PC 可执行、可构建或可运行证据。只有应用市场页面、只有视频演示、只有手机端适配、只有概念说明或没有源码线索的结果，不进入最终清单。

## 总体流程

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

## 模块边界

- `scripts/harmony_pc_oss_radar.py`：命令行入口、搜索计划、来源抓取、候选归一化、证据抽取、评分和输出。
- `SKILL.md`：Agent 工作流、保守筛选原则、复核步骤和输出规范。
- `references/research/source_strategy.md`：各来源的抓取价值、可信度、常见失败方式和复核策略。
- `examples/`：输出字段结构示例，不代表真实已验证项目。
- `outputs/`：本地运行产物，不应作为 Skill 内置知识长期依赖。

## 证据模型

项目进入最终清单前必须同时具备两类证据。

开源证据包括：

- GitHub / GitCode / Gitee 仓库 URL。
- LICENSE 文件或 License 字段。
- README、Release、源码目录结构可访问。
- 项目明确声明开源。

鸿蒙 PC 证据包括：

- 明确出现 `HarmonyOS PC`、`HarmonyOS Computer`、`OpenHarmony PC`、`鸿蒙 PC`、`鸿蒙电脑`。
- 提供 HAP、Release、安装包或应用市场入口，并且能反查源码。
- 提供 DevEco、hvigor、ArkTS、Stage Model 工程结构。
- 提供 Qt for HarmonyOS / Electron for HarmonyOS 构建说明。
- B站、文章、论坛有运行演示，并能关联源码或上游仓库。

## 分类与评分

报告主要展示：

- `confirmed`：证据较强，已明确支持鸿蒙 PC，或具备 HAP / Release / 应用市场 / 演示 / 构建说明等强证据。
- `buildable`：有源码和构建方式，看起来可以在鸿蒙 PC 上构建或迁移，但仍需要进一步验证。

内部候选可出现 `ported-demo`，用于记录已有移植或运行演示、但源码或构建链路仍需补证据的项目。Markdown 报告不单列空的 `ported-demo` 章节。

低于 `--min-score` 的结果默认过滤。过滤原因写入 `outputs/candidate_audit.csv`，用于调参和人工复核。

## 推荐使用流程

1. 在 `.env` 中配置 `GITHUB_TOKEN`。
2. 运行扩展多来源搜索。
3. 先看 `outputs/harmony_pc_oss_report.md` 的高分结果。
4. 再用 `outputs/candidate_audit.csv` 找被过滤但可能值得补证据的项目。
5. 对 B站、AppGallery 和 GitCode 弱证据候选做人工或浏览器复核。
6. 只把同时具备开源证据和鸿蒙 PC 证据的项目合并回最终清单。
