# 鸿蒙 PC 可执行开源软件清单

> 本文件是 example only，用于展示 Markdown 报告结构，不代表已验证真实项目。

## 一、confirmed：已确认可执行

### example-only/arkts-note-pc

- 项目简介：example only: ArkTS note app sample record for output schema.
- 源码地址：https://example.invalid/repos/arkts-note-pc
- 运行证据：example only: README states HarmonyOS PC support; example only: Release contains HAP
- 开源证据：example only: public source repo; example only: LICENSE MIT
- 技术栈：ArkTS; HAP
- 安装 / 构建方式：HAP; Release; DevEco; hvigor
- 风险：example only: not a verified real project
- 推荐程度：优先验证（88 分）

## 二、buildable：源码可构建，需进一步验证

### example-only/qt-terminal-ohos

- 项目简介：example only: Qt terminal porting sample record for output schema.
- 源码地址：https://example.invalid/repos/qt-terminal-ohos
- 构建方式：qmake; cmake
- 技术栈：Qt; C++
- 证据：example only: Qt for OpenHarmony PC build notes; example only: CMake desktop target
- 风险：example only: runtime demo still needs manual verification
- 推荐程度：值得关注（72 分）

## 三、优先验证建议

1. **example-only/arkts-note-pc**（88 分，优先验证）：结构完整，示例中同时具备开源证据、HAP 线索和 HarmonyOS PC 文案。
2. **example-only/qt-terminal-ohos**（72 分，值得关注）：示例中具备 Qt for OpenHarmony PC 构建线索，适合作为桌面软件移植参考。
3. **example-only/electron-markdown-harmony**（64 分，值得关注）：示例中有运行演示和源码线索，但 License 与适配源码完整度需要复核。
