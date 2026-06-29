# 多来源搜索与复核策略

## GitHub

GitHub 是自动化程度最高的数据源。优先用于发现源码、License、README、Release、目录结构和最近维护状态。

推荐策略：

- 使用仓库搜索发现名称、描述、README 命中的项目。
- 使用 code search 补充 `oh-package.json5`、`hvigorfile.ts`、`module.json5`、`build-profile.json5` 等构建文件线索。
- 使用 `.env` 中的 `GITHUB_TOKEN` 提高 API 限额。
- 对长关键词保持警惕，GitHub 搜索容易因 AND 逻辑漏掉只命中部分词的项目。

保留条件：

- 至少能访问源码仓库。
- 至少有一种鸿蒙 PC / Computer / OpenHarmony PC / 桌面移植证据。

## GitCode

GitCode 可补充中文生态项目和 GitHub 镜像。脚本优先使用公开搜索 API，并尝试抽取项目名、命名空间、描述、语言、tags、license 和上游链接。

复核重点：

- 区分真实 GitCode 原生仓库和 GitHub 镜像。
- 检查 README 是否说明鸿蒙 PC，而不是普通 OpenHarmony 示例。
- 检查 License 是否明确。
- 如果 GitCode 页面指向 GitHub 上游，优先补抓 GitHub 证据并合并为同一项目。

## B站

B站用于发现运行演示、移植教程和项目线索，但视频不能单独证明开源。

复核重点：

- 检查视频标题、简介、评论或置顶链接中是否有源码仓库。
- 只把视频作为 `demo_url` 或运行证据。
- 没有源码线索的视频不进入最终清单。
- 遇到 `412`、验证码或动态页时，只记录候选和人工复核链接，不伪造详情。

## AppGallery / 鸿蒙应用市场

应用市场用于发现可能可安装的软件，但可安装不等于开源。

复核重点：

- 应用市场页面只能作为 `market_url` 或安装线索。
- 必须反查 GitHub / GitCode / Gitee / 官网源码仓库。
- 只有市场页面、没有源码的软件必须过滤。
- 应用名与仓库名相似时也要检查 README、Release 或官网是否明确关联。

## 合并规则

跨来源候选按以下信号合并：

- 仓库 URL 相同。
- 项目名称高度相似。
- B站视频、文章或应用市场页面指向同一个仓库。
- GitCode 项目说明其上游来自同一个 GitHub 仓库。
- README、官网或 Release 指向同一项目。

合并后保留所有来源证据：`repo_url`、`market_url`、`demo_url`、`article_url`、`source`、`harmony_pc_evidence`、`open_source_evidence`、`risk`。

## 过滤原则

宁可漏掉弱证据项目，也不要把闭源、非 PC、不可验证或普通手机应用误放进最终清单。证据不足但有潜力的项目应进入审计文件或人工复核列表，而不是最终报告。
