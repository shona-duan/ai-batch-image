# AI 批量生图系统

电商平台（拼多多/抖音）商品主图、详情页、投流素材的自动化批量生成系统。

## 工作原理

Codex 作为组长，协调多个 AI 模型分工协作：

| 角色 | 模型 | 职责 |
|------|------|------|
| 组长 + 生图 | Codex（ChatGPT Plus） | 读表格、拆任务、写prompt、生图、返工 |
| 审核 | DeepSeek Harness | 审查图片质量和合规性 |
| 中文专家 | 豆包（火山引擎API） | OCR识别外包装文字、写中文文案 |

## 快速开始

1. 把本仓库所有文件放到工作目录（如 `D:\AI做图\`）
2. 把 `batch-image/` 文件夹复制到 Codex 的 skill 目录
3. 对 Codex 说"开始做图"→ 首次会引导你配置 API 密钥
4. 详细操作见 [AI做图-使用说明.md](AI做图-使用说明.md)

## 文件说明

```
AI做图-架构文档.md     ← Codex 的完整操作手册
AI做图-使用说明.md     ← 给运营同学看的用户手册
AI做图-规则库.xlsx     ← prompt模板、平台规则、审核标准、风格标签池、敏感词
AI做图-产品库.xlsx     ← 产品信息（商品ID、外包装文字、注意事项）
AI做图-任务队列.xlsx   ← 每天的做图任务
batch-image/           ← Codex Skill（安装到 Codex 的 skill 目录）
  ├── SKILL.md         ← 主入口
  ├── setup.md         ← 首次配置引导
  ├── rules/           ← 平台规则、审核清单、敏感词替换表
  ├── workflows/       ← 内容规划、生图、审核、返工、豆包调用
  ├── templates/       ← content_plan模板、汇报模板
  └── config/          ← API密钥配置页面
```

## 支持的产品类别

- 医疗器械（严格合规：卖点必须来自外包装，抖音需替换医疗术语）
- 餐具、日用百货、美妆个护、食品等（通用规则）

## 核心流程

```
填任务 → 内容规划（1次对话） → 分批生图（每5张一批） → dsh审核 → 验收
```

## 环境要求

- Windows 系统
- Codex CLI（ChatGPT Plus 订阅）
- 火山引擎 API Key（豆包）
- DeepSeek API Key（dsh审核）
