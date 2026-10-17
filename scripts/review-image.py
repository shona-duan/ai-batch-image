"""
dsh 审图脚本 — 调用 DeepSeek 视觉模型审核生成的电商图片

用法：
  python scripts/review-image.py --config config.json --checklist rules/review-checklist.md \
    --images "待审核/img1.png" "待审核/img2.png" \
    --product-photos "产品实拍/photo1.jpg" \
    --category 医疗器械 --platform 抖音 \
    [--output review-result.json]

输出：JSON 格式，每张图一个条目：
  { "file": "img1.png", "pass": true/false, "issues": [ {"code": "C-04", "desc": "..."} ] }
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

try:
    import httpx
    HTTP_CLIENT = "httpx"
except ImportError:
    import urllib.request
    import urllib.error
    import ssl
    HTTP_CLIENT = "urllib"


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def encode_image(image_path: str) -> str:
    """把图片编码为 base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def guess_mime(path: str) -> str:
    ext = Path(path).suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(ext, "image/png")


def build_review_prompt(checklist_path: str, category: str, platform: str) -> str:
    """从审核清单文件构建审核 prompt"""
    with open(checklist_path, "r", encoding="utf-8") as f:
        checklist_raw = f.read()

    # 提取 ``` 之间的清单内容
    lines = checklist_raw.split("\n")
    in_block = False
    checklist_lines = []
    for line in lines:
        if line.strip().startswith("```") and not in_block:
            in_block = True
            continue
        elif line.strip().startswith("```") and in_block:
            in_block = False
            continue
        if in_block:
            checklist_lines.append(line)

    checklist_text = "\n".join(checklist_lines)
    # 填入变量
    checklist_text = checklist_text.replace("{产品类别}", category).replace("{平台}", platform)

    return checklist_text


def call_deepseek_vision(
    api_key: str,
    base_url: str,
    model: str,
    system_prompt: str,
    images: list[dict],
    reference_images: list[dict] | None = None,
) -> str:
    """
    调用 DeepSeek 视觉模型。
    images: [{"path": ..., "base64": ..., "mime": ...}, ...]
    """
    # 构建 messages
    content_parts = []

    # 先放产品实拍参考
    if reference_images:
        content_parts.append({"type": "text", "text": "以下是产品实拍照片（作为真实产品的参考）："})
        for ref in reference_images:
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{ref['mime']};base64,{ref['base64']}"
                }
            })

    # 再放待审核图
    content_parts.append({"type": "text", "text": "以下是需要审核的生成图片，请逐张按清单审核："})
    for img in images:
        content_parts.append({"type": "text", "text": f"【{Path(img['path']).name}】"})
        content_parts.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{img['mime']};base64,{img['base64']}"
            }
        })

    content_parts.append({
        "type": "text",
        "text": (
            "请按以下 JSON 格式返回审核结果，只返回 JSON，不要其他文字：\n"
            '[\n  {"file": "文件名", "pass": true或false, "issues": [{"code": "C-XX", "desc": "具体问题"}]}\n]\n'
            "如果某张图全部通过，issues 为空数组。"
        )
    })

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": content_parts},
    ]

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 4096,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    url = f"{base_url.rstrip('/')}/chat/completions"

    if HTTP_CLIENT == "httpx":
        resp = httpx.post(url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()
    else:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))

    return data["choices"][0]["message"]["content"]


def parse_review_response(raw: str) -> list[dict]:
    """从模型返回中提取 JSON 审核结果"""
    # 尝试直接解析
    raw = raw.strip()
    if raw.startswith("```"):
        # 去掉 markdown 代码块
        lines = raw.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw = "\n".join(lines)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # 尝试找 [ ... ] 部分
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1:
            return json.loads(raw[start:end + 1])
        raise ValueError(f"无法解析审核结果：{raw[:200]}")


def main():
    parser = argparse.ArgumentParser(description="DeepSeek 审图脚本")
    parser.add_argument("--config", required=True, help="config.json 路径")
    parser.add_argument("--checklist", required=True, help="审核清单 markdown 路径")
    parser.add_argument("--images", nargs="+", required=True, help="待审核图片路径")
    parser.add_argument("--product-photos", nargs="*", default=[], help="产品实拍照片（参考）")
    parser.add_argument("--category", required=True, help="产品类别（医疗器械/餐具/...）")
    parser.add_argument("--platform", required=True, help="平台（拼多多/抖音）")
    parser.add_argument("--output", default=None, help="输出 JSON 文件路径（不指定则打印到 stdout）")
    args = parser.parse_args()

    # 读配置
    config = load_config(args.config)
    ds_config = config.get("api_keys", {}).get("deepseek", {})
    api_key = ds_config.get("api_key", "")
    base_url = ds_config.get("base_url", "https://api.deepseek.com/v1")
    model = ds_config.get("model", "deepseek-chat")

    if not api_key:
        print("错误：config.json 中缺少 deepseek.api_key", file=sys.stderr)
        sys.exit(1)

    # 构建审核 prompt
    system_prompt = build_review_prompt(args.checklist, args.category, args.platform)

    # 编码图片
    images = []
    for p in args.images:
        if not os.path.exists(p):
            print(f"警告：图片不存在，跳过：{p}", file=sys.stderr)
            continue
        images.append({
            "path": p,
            "base64": encode_image(p),
            "mime": guess_mime(p),
        })

    if not images:
        print("错误：没有有效的待审核图片", file=sys.stderr)
        sys.exit(1)

    reference_images = []
    for p in args.product_photos:
        if os.path.exists(p):
            reference_images.append({
                "path": p,
                "base64": encode_image(p),
                "mime": guess_mime(p),
            })

    # 调用 DeepSeek
    print(f"正在审核 {len(images)} 张图片...", file=sys.stderr)
    raw_response = call_deepseek_vision(
        api_key=api_key,
        base_url=base_url,
        model=model,
        system_prompt=system_prompt,
        images=images,
        reference_images=reference_images or None,
    )

    # 解析结果
    results = parse_review_response(raw_response)

    # 汇总
    passed = sum(1 for r in results if r.get("pass"))
    failed = len(results) - passed
    summary = {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "results": results,
    }

    output_json = json.dumps(summary, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"审核完成：{passed}/{len(results)} 通过，结果写入 {args.output}", file=sys.stderr)
    else:
        print(output_json)

    # 退出码：有不通过的返回 1
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
