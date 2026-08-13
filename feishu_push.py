#!/usr/bin/env python3
"""
飞书推送：BOM 闲鱼日报推送给大王
- 步骤1：发摘要 text 消息（含链接 + 关键商品）
- 步骤2：发完整报告作为 file 附件（HTML版本，渲染友好）
"""
from __future__ import annotations
import json
import os
import re
import sys
import urllib.request
import urllib.error
import uuid
import mimetypes
from pathlib import Path

ENV_PATH = Path.home() / ".hermes" / ".env"
DEFAULT_CHAT_ID = "oc_fb62e95ca78fb4d9336c1a42982ada5b"


def load_env() -> dict:
    cfg = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg


def get_token(cfg: dict) -> str:
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    body = json.dumps({"app_id": cfg["FEISHU_APP_ID"], "app_secret": cfg["FEISHU_APP_SECRET"]}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    if result.get("code") != 0:
        raise RuntimeError(f"feishu token error: {result}")
    return result["tenant_access_token"]


def detect_chat_type(oid: str) -> str:
    if oid.startswith(("oc_", "oh_")):
        return "chat_id"
    if oid.startswith("ou_"):
        return "open_id"
    return "chat_id"


def send_text(token: str, chat_id: str, text: str) -> dict:
    url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type={detect_chat_type(chat_id)}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = json.dumps({
        "receive_id": chat_id,
        "msg_type": "text",
        "content": json.dumps({"text": text}),
    }).encode()
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def send_post(token: str, chat_id: str, title: str, lines: list) -> dict:
    """post 富文本消息（每个 line 是一条文本行或 link）"""
    url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type={detect_chat_type(chat_id)}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    content = [[{"tag": "text", "text": l}] if isinstance(l, str) else l for l in lines]
    body = json.dumps({
        "receive_id": chat_id,
        "msg_type": "post",
        "content": json.dumps({"zh_cn": {"title": title, "content": content}}, ensure_ascii=False),
    }).encode()
    req = urllib.request.Request(url, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"post error: {e.read().decode()[:500]}")


def upload_file(token: str, file_path: Path) -> str:
    boundary = f"----FormBoundary{uuid.uuid4().hex[:16]}"
    file_name = file_path.name
    parts = [
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="file_type"\r\n\r\nstream\r\n',
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="file_name"\r\n\r\n{file_name}\r\n'.encode(),
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n'.encode(),
        f"Content-Type: {mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'}\r\n\r\n".encode(),
        file_path.read_bytes(),
        f"\r\n--{boundary}--\r\n".encode(),
    ]
    url = "https://open.feishu.cn/open-apis/im/v1/files"
    req = urllib.request.Request(url, data=b"".join(parts), headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    })
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    if result.get("code") != 0:
        raise RuntimeError(f"upload error: {result}")
    return result["data"]["file_key"]


def send_file(token: str, chat_id: str, file_key: str) -> dict:
    url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type={detect_chat_type(chat_id)}"
    body = json.dumps({
        "receive_id": chat_id,
        "msg_type": "file",
        "content": json.dumps({"file_key": file_key}),
    }).encode()
    req = urllib.request.Request(url, data=body, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def make_summary(md: str) -> tuple[str, list]:
    """从 Markdown 报告抽取 6 行摘要 + post 富文本内容"""
    lines = md.splitlines()
    title = next((l for l in lines if l.startswith("# ")), "BOM 闲鱼日报")
    stats_idx = next((i for i, l in enumerate(lines) if "## 📊 搜索概览" in l), -1)
    stats_block = []
    if stats_idx >= 0:
        for l in lines[stats_idx + 1: stats_idx + 12]:
            if l.startswith("##"):
                break
            stats_block.append(l)
    stats_text = "\n".join(stats_block)

    has_match = "🟢" in stats_text or "Cookie已注入" in stats_text
    has_blocked = "被登录墙挡住" in md
    mode = "🟢 Cookie模式" if has_match else "🟡 建议清单模式（无cookie）"

    summary_text = f"{title}\n{mode}\n\n{stats_text}\n\n完整报告见下方附件 ⬇️"
    post_lines = [
        [{"tag": "text", "text": title}],
        [{"tag": "text", "text": mode}],
        [{"tag": "text", "text": "\n"}],
        [{"tag": "text", "text": stats_text[:500]}],
        [{"tag": "text", "text": "\n\n"}],
        [{"tag": "text", "text": "📎 完整报告见下方附件"}],
    ]
    if has_blocked:
        post_lines.insert(3, [{"tag": "text", "text": "\n⚠️ 部分任务被登录墙挡住，请参考报告说明提供 cookie 升级到全自动模式\n"}])
    return summary_text, post_lines


def push_report(md: str, html_path: Path, chat_id: str = DEFAULT_CHAT_ID):
    cfg = load_env()
    token = get_token(cfg)
    print(f"[push] got token, chat_id={chat_id}")

    # 1) 文本摘要
    summary, _ = make_summary(md)
    r1 = send_text(token, chat_id, summary)
    if r1.get("code") != 0:
        print(f"[push] text failed: {r1}")
    else:
        print(f"[push] ✅ summary sent")

    # 2) HTML 附件
    if html_path.exists():
        fk = upload_file(token, html_path)
        r2 = send_file(token, chat_id, fk)
        if r2.get("code") != 0:
            print(f"[push] file failed: {r2}")
        else:
            print(f"[push] ✅ HTML 附件已发送: {fk}")
    return r1


if __name__ == "__main__":
    md_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent / "output" / "bom_hunt_report.md"
    html_path = md_path.with_suffix(".html")
    md = md_path.read_text(encoding="utf-8")
    push_report(md, html_path)