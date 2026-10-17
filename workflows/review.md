# 审核流程

## 触发条件

一批图（5张）生成完毕后，派 dsh 审核。

## 执行步骤

1. 状态更新为「审核中」
2. 准备审核材料：
   - 生成的图片（待审核/目录下）
   - 产品实拍图（作为对比参照）
   - 审核清单（见 rules/review-checklist.md）
   - 平台规则 + 产品注意事项
   - 产品类别（决定C-03/C-04的严格程度）
3. 发给 dsh，附上完整审核指令
4. dsh 返回逐张结果

## 处理审核结果

```
全部通过
  → 图片移入 生成图/待验收/
  → 状态更新为「待验收」

有不合格
  → 看返工次数
    ├── < 2次 → 读 workflows/rework.md → 进入返工
    └── ≥ 2次 → 状态「人工处理」
                → 写人工处理报告到 汇报/人工处理/{任务ID}.md
```

## 调用 dsh 的方式

使用仓库自带的审图脚本 `scripts/review-image.py`，它封装了 DeepSeek 视觉模型的 API 调用。

### 基本调用

```bash
python scripts/review-image.py \
  --config config.json \
  --checklist rules/review-checklist.md \
  --images "素材库/{商品ID}/生成图/待审核/img1.png" "素材库/{商品ID}/生成图/待审核/img2.png" \
  --product-photos "素材库/{商品ID}/产品实拍/photo1.jpg" \
  --category {产品类别} \
  --platform {平台} \
  --output "素材库/{商品ID}/生成图/review-result.json"
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--config` | 是 | config.json 路径 |
| `--checklist` | 是 | 审核清单文件（rules/review-checklist.md） |
| `--images` | 是 | 待审核图片路径（可多张） |
| `--product-photos` | 否 | 产品实拍照（作为对比参照） |
| `--category` | 是 | 产品类别（医疗器械/餐具/…） |
| `--platform` | 是 | 平台（拼多多/抖音） |
| `--output` | 否 | 输出 JSON 路径，不指定则打印到 stdout |

### 输出格式

```json
{
  "total": 5,
  "passed": 3,
  "failed": 2,
  "results": [
    {"file": "img1.png", "pass": true, "issues": []},
    {"file": "img2.png", "pass": false, "issues": [
      {"code": "C-04", "desc": "出现'医疗器械'字样"}
    ]}
  ]
}
```

### 退出码

- `0` = 全部通过
- `1` = 有不通过项

### 处理结果的逻辑

脚本跑完后，你（Codex）读 JSON 结果：
- `pass: true` 的图 → 移入 `生成图/待验收/`
- `pass: false` 的图 → 读 issues 里的 code 和 desc → 作为返工指令

### config.json 中的 DeepSeek 配置

```json
{
  "api_keys": {
    "deepseek": {
      "api_key": "你的DeepSeek API Key",
      "base_url": "https://api.deepseek.com/v1",
      "model": "deepseek-chat"
    }
  }
}
```

如果用户的 DeepSeek 支持视觉模型（如 deepseek-vl），改 model 字段即可。

## 注意

- dsh 只负责审核，不负责生图
- 审核结果写入任务队列的「dsh反馈」列
- dsh审核可以和下一批生图并行（不用等审核完再开始下一批）
- 脚本只依赖 Python 标准库（可选装 httpx 提升性能），无需额外安装
