# 首次配置

config.json 不存在时执行本流程。

## Step 1：问用户

依次询问以下信息：

| 问题 | 默认值 | 说明 |
|------|--------|------|
| 工作目录在哪？ | `D:\AI做图` | 所有表格和素材的根目录 |
| 火山引擎 API Key？ | 无，必填 | 豆包 OCR + 文案用 |
| 豆包 Endpoint ID？ | 无，必填 | 视觉模型的推理接入点 |
| DeepSeek API Key？ | 无，必填 | dsh 审核用 |
| 每天几点自动扫描？ | 18:00 | 留空或说"不要"则关闭定时 |

## Step 2：生成 config.json

写入工作目录根下：

```json
{
  "workspace": "用户指定的路径",
  "api_keys": {
    "volcengine": {
      "api_key": "用户填的key",
      "endpoint_id": "用户填的endpoint"
    },
    "deepseek": {
      "api_key": "用户填的key",
      "base_url": "https://api.deepseek.com/v1",
      "model": "deepseek-chat"
    }
  },
  "schedule": {
    "auto_scan_time": "18:00",
    "enabled": true
  },
  "paths": {
    "rules": "%WORKSPACE%\\规则库.xlsx",
    "products": "%WORKSPACE%\\产品库.xlsx",
    "tasks": "%WORKSPACE%\\任务队列.xlsx",
    "assets": "%WORKSPACE%\\素材库",
    "reports": "%WORKSPACE%\\汇报"
  }
}
```

密钥安全：config.json 只存在本地，不上传不同步。

## Step 3：检查工作目录

```
检查三张表是否存在：
  ├── 规则库.xlsx  → 没有 → 提示用户放进来
  ├── 产品库.xlsx  → 没有 → 提示用户放进来
  └── 任务队列.xlsx → 没有 → 提示用户放进来
```

## Step 4：创建文件夹

如果不存在，自动创建：

```
%WORKSPACE%\素材库\
%WORKSPACE%\汇报\每日总结\
%WORKSPACE%\汇报\人工处理\
```

## Step 5：确认就绪

告诉用户：
```
配置完成！接下来你需要：
1. 把产品的素材照片放到 素材库/{商品ID}/ 对应文件夹下
2. 在任务队列里填你要做的任务（日期、平台、商品ID、图片类型、数量）
3. 对我说"开始做图"就行了
```

## 备选：配置页面

如果用户不想逐个回答问题，可以打开 config/ 目录下的 config-page.html，在网页上填写后复制生成的 JSON，保存为 config.json。
