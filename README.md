# Technical Report Formatter

一个用于整理和核验 Word 技术报告的 Agent Skill，支持 Codex、DeepSeek Harness（DSH）及其他兼容 `SKILL.md` 的智能体环境。

## 功能

- 按用户提供的 Word 模板整理技术报告；
- 标题层级可配置，例如只到标题2，或保留 `2.1.1` 三级标题；
- 目录层级可与正文标题层级分别设置；
- 检查图片段落行距，包括表格单元格中的图片；
- 按任务要求保留或删除页眉图片，并检查指定页脚文字；
- 检查 A4 页面、页边距、图表编号和媒体文件；
- 强制要求最终逐页渲染核验。

> 本项目不包含任何单位专用 Word 模板。使用者需要自行提供有权使用的模板文件。

## 安装

### Codex

```bash
git clone https://github.com/edwardchentiandong-lgtm/technical-report-formatter.git \
  ~/.agents/skills/technical-report-formatter
```

也可以放入 Codex 当前配置支持的个人或项目 Skill 目录。

### DeepSeek Harness（DSH）

```bash
git clone https://github.com/edwardchentiandong-lgtm/technical-report-formatter.git \
  ~/.agents/skills/technical-report-formatter
```

刷新 DSH 后使用：

```text
/technical-report-formatter
```

## 使用示例

```text
使用 technical-report-formatter 整理这份报告：
- 参考附件中的模板；
- 正文标题保留到标题3，2.1.1 使用标题3；
- 目录只列到标题2；
- 图片段落使用单倍行距；
- 删除页眉图片；
- 页脚必须保留“示例单位”；
- 不覆盖原文件。
```

## DOCX 审计

审计脚本仅使用 Python 标准库：

```bash
python3 scripts/audit_report.py output.docx \
  --max-heading-level 3 \
  --company "示例单位"
```

如果允许保留页眉图片：

```bash
python3 scripts/audit_report.py output.docx \
  --max-heading-level 3 \
  --allow-header-images
```

脚本负责结构审计，不替代 Word、Pages 或其他可靠环境中的逐页视觉检查。

## 测试

```bash
python3 -m unittest discover -s tests -v
```

## 许可证

[MIT](LICENSE)
