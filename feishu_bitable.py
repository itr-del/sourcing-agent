#!/usr/bin/env python3
"""
把 BOM 任务 + 搜索进度写入飞书多维表格。
首次运行：自动创建 bitable + 字段 + 写入29条记录，返回 app_token + url
后续运行：用已有 app_token + table_id 增量更新（status / 匹配商品数 / 备注）
"""
from __future__ import annotations
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

SKILL_DIR = Path(__file__).parent
OUTPUT_DIR = SKILL_DIR.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ENV_PATH = Path.home() / ".hermes" / ".env"

# 持久化保存 base 标识（避免重复创建）
META_PATH = OUTPUT_DIR / "bitable_meta.json"

BASE_NAME = "桨板跟拍船 BOM 采购进度 (xianyu-bom-hunter)"
TABLE_NAME = "BOM任务"

# 字段定义（飞书 bitable API 格式：type 数字枚举，property 是对象）
FIELDS_DEF = [
    {"field_name": "任务ID", "type": 1, "property": None},                         # 1=文本
    {"field_name": "物品名称", "type": 1, "property": None},                       # 1=文本
    {"field_name": "方案", "type": 3, "property": {"options": [                    # 3=单选
        {"name": "A", "color": 0},
        {"name": "B", "color": 1},
        {"name": "共用", "color": 2},
    ]}},
    {"field_name": "是否必备", "type": 3, "property": {"options": [
        {"name": "必备", "color": 1},
        {"name": "可选", "color": 7},
    ]}},
    {"field_name": "类别", "type": 3, "property": {"options": [
        {"name": "船体结构", "color": 0},
        {"name": "动力推进", "color": 1},
        {"name": "控制电子", "color": 2},
        {"name": "拍摄与云台", "color": 3},
        {"name": "电池与电源", "color": 4},
        {"name": "防水与密封", "color": 5},
        {"name": "工具与耗材", "color": 6},
    ]}},
    {"field_name": "价格下限", "type": 2, "property": {"formatter": "0"}},          # 2=数字
    {"field_name": "价格上限", "type": 2, "property": {"formatter": "0"}},
    {"field_name": "关键词", "type": 1, "property": None},                          # 1=文本
    {"field_name": "规格要求", "type": 1, "property": None},
    {"field_name": "闲鱼链接", "type": 15, "property": None},                       # 15=超链接（实际上 type 1 + style 即可）
    {"field_name": "状态", "type": 3, "property": {"options": [
        {"name": "建议清单", "color": 7},
        {"name": "已匹配", "color": 2},
        {"name": "已登录墙", "color": 5},
        {"name": "异常", "color": 6},
    ]}},
    {"field_name": "匹配商品数", "type": 2, "property": {"formatter": "0"}},
    {"field_name": "Top商品标题", "type": 1, "property": None},
    {"field_name": "Top商品价格", "type": 2, "property": {"formatter": "0"}},
    {"field_name": "Top商品链接", "type": 1, "property": None},
    {"field_name": "备注", "type": 1, "property": None},
]


def load_env() -> dict:
    cfg = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg


def _api(method: str, url: str, token: str, body: dict = None) -> dict:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        return {"code": e.code, "error_body": body_text}


def get_token(cfg: dict) -> str:
    r = _api("POST", "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal", "",
             {"app_id": cfg["FEISHU_APP_ID"], "app_secret": cfg["FEISHU_APP_SECRET"]})
    if r.get("code") != 0:
        raise RuntimeError(f"token error: {r}")
    return r["tenant_access_token"]


def create_app(token: str) -> dict:
    r = _api("POST", "https://open.feishu.cn/open-apis/bitable/v1/apps", token,
             {"name": BASE_NAME, "folder_token": ""})
    if r.get("code") != 0:
        raise RuntimeError(f"create app failed: {r}")
    return r["data"]["app"]


def list_tables(token: str, app_token: str) -> list:
    r = _api("GET", f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables", token)
    if r.get("code") != 0:
        return []
    return r["data"].get("items", [])


def create_table(token: str, app_token: str, name: str) -> dict:
    r = _api("POST", f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables", token,
             {"table": {"name": name, "default_view_name": "总览"}})
    if r.get("code") != 0:
        raise RuntimeError(f"create table failed: {r}")
    return r["data"]


def list_fields(token: str, app_token: str, table_id: str) -> list:
    r = _api("GET", f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields", token)
    if r.get("code") != 0:
        return []
    return r["data"].get("items", [])


def create_fields(token: str, app_token: str, table_id: str, fields: list) -> list:
    """逐个创建字段（飞书接口只接受单字段）"""
    out = []
    for f in fields:
        body = {"field_name": f["field_name"], "type": f["type"]}
        if f["property"]:
            body["property"] = f["property"]
        r = _api("POST", f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields", token, body)
        if r.get("code") != 0:
            print(f"  ⚠️ field '{f['field_name']}' create failed: {r}")
        else:
            out.append(r["data"].get("field", {}))
    return out


def batch_create_records(token: str, app_token: str, table_id: str, records: list) -> list:
    out = []
    for i in range(0, len(records), 200):
        chunk = records[i:i+200]
        r = _api("POST",
                 f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
                 token, {"records": [{"fields": rec} for rec in chunk]})
        if r.get("code") != 0:
            print(f"  ⚠️ batch_create chunk {i} failed: {r}")
        else:
            out.extend(r["data"].get("records", []))
    return out


def batch_update_records(token: str, app_token: str, table_id: str, records: list) -> list:
    """records: [{record_id, fields}]"""
    out = []
    for i in range(0, len(records), 200):
        chunk = records[i:i+200]
        r = _api("POST",
                 f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update",
                 token, {"records": chunk})
        if r.get("code") != 0:
            print(f"  ⚠️ batch_update chunk {i} failed: {r}")
        else:
            out.extend(r["data"].get("records", []))
    return out


def list_records(token: str, app_token: str, table_id: str) -> list:
    """拉所有已有记录（用于增量更新）"""
    out = []
    page_token = ""
    while True:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records?page_size=500"
        if page_token:
            url += f"&page_token={page_token}"
        r = _api("GET", url, token)
        if r.get("code") != 0:
            break
        data = r["data"]
        out.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token", "")
        if not page_token:
            break
    return out


def load_meta() -> dict | None:
    if META_PATH.exists():
        return json.loads(META_PATH.read_text(encoding="utf-8"))
    return None


def save_meta(meta: dict):
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def status_map(r: dict) -> str:
    s = r.get("status", "")
    if s == "login_required":
        return "已登录墙"
    if s == "exception":
        return "异常"
    if s == "no_match":
        return "已登录墙"  # 页面加载但没匹配也归到登录墙
    if r.get("items"):
        return "已匹配"
    return "建议清单"


def build_records(bom_tasks: list, search_results: list) -> list:
    """把 BOM 任务 + 搜索结果合并成待写入的 records"""
    results_by_id = {r["id"]: r for r in search_results}
    records = []
    for t in bom_tasks:
        r = results_by_id.get(t["id"], {})
        items = r.get("items", [])
        top = items[0] if items else {}
        plan_text = {"A": "A", "B": "B", "both": "共用"}.get(t.get("plan", ""), "共用")
        rec = {
            "任务ID": t["id"],
            "物品名称": t.get("name", ""),
            "方案": plan_text,
            "是否必备": "必备" if t.get("essential") else "可选",
            "类别": t.get("category", ""),
            "价格下限": t.get("price_range", [0, 0])[0],
            "价格上限": t.get("price_range", [0, 0])[1],
            "关键词": " / ".join(t.get("keywords", [])[:6]),
            "规格要求": " / ".join(t.get("spec_filters", [])[:6]),
            "闲鱼链接": {"link": r.get("search_url") or
                                  f"https://www.goofish.com/search?q={t.get('keywords', [''])[0]}",
                         "text": "🔗 闲鱼搜索"},
            "状态": status_map(r),
            "匹配商品数": len(items),
            "Top商品标题": (top.get("title", "") or "")[:80] if top else "",
            "Top商品价格": top.get("price") if top else 0,
            "Top商品链接": (top.get("href", "") or "")[:200] if top else "",
            "备注": t.get("notes", ""),
        }
        records.append(rec)
    return records


def push_to_bitable(records: list, force_recreate: bool = False):
    cfg = load_env()
    token = get_token(cfg)
    print(f"[bitable] got token")

    meta = None if force_recreate else load_meta()
    if meta and not force_recreate:
        app_token = meta["app_token"]
        table_id = meta["table_id"]
        url = meta.get("url", "")
        # 验证 app_token 是否还有效
        tables = list_tables(token, app_token)
        if not tables:
            print(f"[bitable] meta 已失效，重新创建")
            meta = None

    if not meta:
        print(f"[bitable] 创建新多维表格：{BASE_NAME}")
        app = create_app(token)
        app_token = app["app_token"]
        url = app["url"]
        print(f"[bitable] app_token={app_token}, url={url}")
        tables = list_tables(token, app_token)
        if not tables:
            t = create_table(token, app_token, TABLE_NAME)
            table_id = t["table_id"]
        else:
            table_id = tables[0]["table_id"]
        print(f"[bitable] table_id={table_id}")
        # 创建字段
        existing_fields = {f["field_name"] for f in list_fields(token, app_token, table_id)}
        to_create = [f for f in FIELDS_DEF if f["field_name"] not in existing_fields]
        if to_create:
            print(f"[bitable] 创建 {len(to_create)} 个字段")
            create_fields(token, app_token, table_id, to_create)
        meta = {"app_token": app_token, "table_id": table_id, "url": url}
        save_meta(meta)
        print(f"[bitable] meta saved to {META_PATH}")

    # 拉取现有记录做 upsert
    print(f"[bitable] 拉取现有记录用于 upsert...")
    existing = list_records(token, app_token, table_id)
    by_id = {}
    for rec in existing:
        fid = rec.get("fields", {}).get("任务ID", "")
        if fid:
            by_id[fid] = rec["record_id"]
    print(f"[bitable] 已有 {len(by_id)} 条记录")

    to_create = []
    to_update = []
    for rec in records:
        fid = rec["任务ID"]
        if fid in by_id:
            to_update.append({"record_id": by_id[fid], "fields": rec})
        else:
            to_create.append(rec)

    if to_create:
        print(f"[bitable] 写入 {len(to_create)} 条新记录...")
        batch_create_records(token, app_token, table_id, to_create)
    if to_update:
        print(f"[bitable] 更新 {len(to_update)} 条记录...")
        batch_update_records(token, app_token, table_id, to_update)

    return meta


def main():
    # 读取 BOM + 搜索结果
    bom_path = SKILL_DIR / "bom_tasks.json"
    results_path = OUTPUT_DIR / "search_results.json"
    if not results_path.exists():
        print(f"[bitable] 缺少 {results_path}，请先跑 run_pipeline.py")
        sys.exit(1)
    bom = json.loads(bom_path.read_text(encoding="utf-8"))
    results = json.loads(results_path.read_text(encoding="utf-8"))
    records = build_records(bom["tasks"], results)
    print(f"[bitable] 准备写入 {len(records)} 条记录")
    meta = push_to_bitable(records)
    print(f"\n✅ 完成！")
    print(f"   Base URL: {meta['url']}")
    print(f"   app_token: {meta['app_token']}")
    print(f"   table_id:  {meta['table_id']}")

    # 把 URL 写入推送队列 / 直接推送给大王
    print(f"\n[bitable] 推送给大王...")
    from feishu_push import send_text, get_token, DEFAULT_CHAT_ID, load_env
    cfg = load_env()
    token = get_token(cfg)
    msg = (f"📊 BOM 进度已同步到飞书多维表格\n\n"
           f"🔗 {meta['url']}\n\n"
           f"共 {len(records)} 条任务记录\n"
           f"字段：任务ID / 物品名称 / 方案 / 是否必备 / 类别 / 价格区间 / 关键词 / 规格要求 / 闲鱼链接 / 状态 / 匹配商品数 / Top商品 / 备注\n\n"
           f"💡 每天 cron 跑完后会自动增量更新状态和 Top 商品")
    r = send_text(token, DEFAULT_CHAT_ID, msg)
    print(f"[bitable] push result: {r.get('code')}")


if __name__ == "__main__":
    main()