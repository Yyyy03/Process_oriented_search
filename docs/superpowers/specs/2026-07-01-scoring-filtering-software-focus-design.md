# 评分与筛选机制改造设计：聚焦鸿蒙 PC 开源软件

- 日期: 2026-07-01
- 范围: `scripts/harmony_pc_oss_radar.py`、`SKILL.md`（根目录 + `.opencode/skills/harmony-pc-oss-radar/` 双副本）
- 状态: 已通过设计评审，待实现

## 1. 目标

让最终清单更聚焦于：

1. 适配鸿蒙 PC 的开源**软件/应用**（终端用户可运行）。
2. 已有知名开源软件的鸿蒙化移植项目。

剔除纯库 / SDK / 包 / 框架。知名度（GitHub star）作为评分加成提升排名，但不硬性剔除小项目，也不在输出中暴露 star 数值。

## 2. 用户决策（已确认）

| 议题 | 决策 |
|---|---|
| Star 用法 | 仅评分加成，不硬过滤，不输出 star 字段 |
| 输出 stars 字段 | 不新增；OUTPUT_FIELDS / AUDIT_FIELDS / SOURCE_CANDIDATE_FIELDS 保持不变 |
| 库/SDK/包/框架 | 保守硬过滤 + 写入审计可追溯；边界模糊的保留并降分 |

## 3. 不变量（保持不变）

- 最终清单只允许 `confirmed` / `buildable` / `ported-demo`，不输出 `closed-source` / `blocked` / `unrelated`。
- 必须同时具备 `open_source_evidence` 与 `harmony_pc_evidence`。
- 无鸿蒙 PC 证据时 score cap 39。
- score < `--min-score`（默认 40）剔除。
- 不伪造不可访问页面证据；不可访问的 GitCode/B站/AppGallery 候选写 raw/audit 并标 `needs_manual_review`。
- 输出 schema（`OUTPUT_FIELDS`）不变。
- 评分 clamp 0..100 不变。

## 4. 新增过滤：库 / SDK / 包 / 框架（保守硬过滤）

### 4.1 新增检测函数

`is_library_or_package(name, description, topics, combined_text, has_release, has_hap, has_market, install_methods, category) -> Tuple[bool, str]`

返回 `(is_library: bool, reason: str)`。

### 4.2 库信号（命中任一即 `is_library=True`）

- **topics 命中**（强信号，作者自标）：`library` / `sdk` / `framework` / `package` / `component` / `crate` / `npm-package`。
- **名称/描述正则**：`\b(library|sdk|framework|component|crate|plugin)\b`。
- **中文短语**：`组件库` / `工具包` / `依赖库` / `SDK for` / `a library` / `an sdk`。
- **不使用**裸 `package` / `库` / `module` 作子串匹配（避免误杀含 `oh-package.json5`、`package.json`、`library manager` 的真实应用）。

### 4.3 可执行反证（有任一则不剔，改降分）

- 有 HAP 安装包 / Release 可安装产物 / 应用市场链接 / `install_methods` 非空 / 归入 GUI 应用类目（非"未分类"）。

### 4.4 决策矩阵

| 库信号 | 可执行反证 | 处理 | 审计 decision |
|---|---|---|---|
| 是 | 否 | 硬过滤，不进最终清单 | `filtered: library/SDK/package/framework (no runnable artifact)` |
| 是 | 是 | 保留，score −8，risk 追加 `疑似库/SDK但含可执行产物,保留并降分` | `kept` |
| 否 | — | 正常流程 | （由既有逻辑决定） |

### 4.5 调用点

在 `analyze_bundle_with_audit` 与 `analyze_source_candidate` 中，于"开源证据 + 鸿蒙PC证据"检查**之后**、评分**之前**调用。库过滤优先于 score<40 判定，使被剔库项目在审计中显示明确原因。

## 5. 评分新增项

### 5.1 知名度加成（仅评分，任何输出都不出现 star 数）

读 `bundle.item.get("stargazers_count")`（GitHub 路径）或 `candidate.stars`（候选路径）。

| stars | 加成 |
|---|---|
| ≥ 10000 | +12 |
| ≥ 1000 | +8 |
| ≥ 100 | +4 |
| ≥ 10 | +1 |
| <10 或无数据 | 0（中性，不扣分） |

无 star 数据（GitCode/B站/AppGallery 未 enriched 的候选）按 0 处理，不影响跨来源公平性。

### 5.2 已有开源软件鸿蒙化加成

命中 `移植` / `port` / `适配` / `adaptation` / `for harmonyos` / `for openharmony` / `鸿蒙版` / `harmonyos port`，且归入桌面应用类目（终端/开发工具/桌面软件移植/原生鸿蒙PC应用/普通桌面应用）→ **+8**。

### 5.3 库类边界降分

见 §4.4 第二行：库信号 + 有可执行反证 → score −8。

### 5.4 平衡保证

- 库过滤先于评分；star/移植加成只在"已合格的开源鸿蒙 PC 软件"上叠加。
- 无鸿蒙证据仍 cap 39（不变）。
- clamp 0..100（不变）。
- 知名度最高 +12、移植 +8，合计上限 +20，不会让弱证据项目越过证据门控。

## 6. 数据流改动（最小改动）

- `SourceCandidate` dataclass 新增内部字段 `stars: int = 0`（**不进** `SOURCE_CANDIDATE_FIELDS` 输出）。
- `maybe_enrich_candidate_from_github` 中设 `candidate.stars = bundle.item.get("stargazers_count") or 0`。
- `score_record` 读 `bundle.item.get("stargazers_count")`。
- 候选内联评分（`analyze_source_candidate`）读 `candidate.stars`。
- `OUTPUT_FIELDS` / `AUDIT_FIELDS` / `SOURCE_CANDIDATE_FIELDS` **不变**。

## 7. SKILL.md 改动范围（双副本同步）

根目录 `SKILL.md` 与 `.opencode/skills/harmony-pc-oss-radar/SKILL.md` 改动一致：

- **§8 项目保留条件**：新增"必须是终端用户可运行的软件/应用，而非库/SDK/包/框架"。
- **§9 项目过滤条件**：新增"纯库/SDK/包/框架，且无可执行产物（HAP/Release/应用市场/GUI 应用）"。
- **§13 评分规则**：新增三档——知名度加成、鸿蒙化移植加成、库类边界降分；重申证据门控与 clamp 不变。

## 8. 验证方式

仓库无测试/lint/typecheck。验证 = 运行脚本并检查输出：

```bash
python scripts/harmony_pc_oss_radar.py --sources all --search-profile expanded --include-code-search --include-audit --out-dir outputs --max-results 50 --web-max-results 20 --include-manual-links --format all
```

检查项：

1. `outputs/candidate_audit.csv` 出现 `filtered: library/SDK/package/framework (no runnable artifact)` 决策行。
2. `outputs/harmony_pc_oss_list.jsonl` 不再含纯库（抽查 name/description/tech_stack）。
3. `outputs/harmony_pc_oss_report.md` 中高 star 知名项目排序靠前。
4. 无 star 数据的 GitCode/B站/AppGallery 候选不被误杀（仍在 raw/candidates 文件中）。
5. `OUTPUT_FIELDS` 输出列无 `stars` 列。

## 9. 非目标 / 不做

- 不新增 `--min-stars` 硬过滤参数（用户选仅评分加成）。
- 不向输出 schema 添加 star / popularity 列。
- 不引入"知名项目白名单"（依赖 star 数即可）。
- 不重构单文件脚本为多包结构（超出本次范围）。
- 不改 `OUTPUT_FIELDS` / `AUDIT_FIELDS`。
