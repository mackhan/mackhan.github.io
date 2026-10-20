#!/usr/bin/env python3
"""从 MovieBox 的对外门面清单同步产品数据，保证首页与 MovieBox 站点用**同一份数据**。

MovieBox 发布时会在自己的 GitHub Pages 上生成 manifest.json（SSOT 来自
MovieBox 仓库的 package.json + pages/changelog.html）：

    https://mackhan.github.io/MovieBox/manifest.json

本脚本拉取它，然后：
1. 更新 site.json 里 moviebox 的 platforms / downloads / links（不再两边手写）
2. 若出现了 site.json 里没有的新版本，把它的更新日志条目插到
   content/changelog/moviebox.md 顶部（版本号与日期也一并来自 manifest）

版本号/日期从此只有 MovieBox 一个源头，首页不再手工维护 —— 这就是"打通用一份数据"。

用法：
    python3 tools/sync_moviebox.py            # 拉取并同步
    python3 tools/sync_moviebox.py --check    # 只对比，不写文件（CI 用）
    python3 tools/sync_moviebox.py --local ~/Documents/Git/MovieBox/pages/manifest.json
"""
import argparse
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_URL = "https://mackhan.github.io/MovieBox/manifest.json"
PID = "moviebox"
TIMEOUT = 15


def load_manifest(local=None):
    if local:
        with open(os.path.expanduser(local), encoding="utf-8") as f:
            return json.load(f)
    req = urllib.request.Request(MANIFEST_URL, headers={"User-Agent": "mackhan-site-sync"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def sync_site_json(m, dry=False):
    path = os.path.join(ROOT, "site.json")
    with open(path, encoding="utf-8") as f:
        site = json.load(f)
    prod = next((p for p in site["products"] if p["id"] == PID), None)
    if prod is None:
        sys.exit("site.json 里没有 id=%s 的产品" % PID)

    before = json.dumps(prod, ensure_ascii=False, sort_keys=True)
    # 平台：macOS 只有一个平台名，架构差异体现在下载标签里
    prod["platforms"] = m.get("platforms", prod.get("platforms", []))
    if m.get("downloads"):
        # label_en 必须一起带过来：英文页若回落到中文标签，i18n 测试会直接失败
        prod["downloads"] = [
            {"label": d.get("label"), "label_en": d.get("label_en"), "url": d["url"]}
            if d.get("label_en") else {"label": d.get("label"), "url": d["url"]}
            for d in m["downloads"]
        ]
    if m.get("links"):
        prod["links"] = [
            {"label": l.get("label"), "url": l["url"], "label_en": l.get("label_en")}
            for l in m["links"]
        ]
    prod["manifest"] = MANIFEST_URL
    # 产品名点击后去产品自己的站点（build.py 会用 site 字段把标题变成链接）
    if m.get("site"):
        prod["site"] = m["site"]
    after = json.dumps(prod, ensure_ascii=False, sort_keys=True)

    if before == after:
        print("site.json：无变化")
        return False
    if dry:
        print("site.json：有变化（--check 不写入）")
        return True
    with open(path, "w", encoding="utf-8") as f:
        json.dump(site, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("site.json：已更新 platforms / downloads / links")
    return True


def render_entry(e):
    """把一个版本条目渲染成 changelog md 片段"""
    out = ["## v%s · %s" % (e["version"], e["date"] or "待定"), ""]
    for g in e.get("groups", []):
        out.append("### %s" % g["title"])
        out.append("")
        for it in g.get("items", []):
            out.append("- %s" % it)
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def sync_changelog(m, dry=False):
    path = os.path.join(ROOT, "content", "changelog", "%s.md" % PID)
    with open(path, encoding="utf-8") as f:
        text = f.read()

    have = set(re.findall(r"^##\s*v?([\d.]+)", text, re.M))
    news = [e for e in m.get("changelog", []) if e["version"] not in have]
    if not news:
        print("changelog：已是最新（v%s）" % m.get("version"))
        return False

    news.sort(key=lambda e: [int(x) for x in e["version"].split(".")])
    block = "\n".join(render_entry(e) for e in news).rstrip() + "\n"
    if dry:
        print("changelog：待新增 %s（--check 不写入）" % ", ".join("v" + e["version"] for e in news))
        return True
    with open(path, "w", encoding="utf-8") as f:
        f.write(block + "\n" + text.lstrip("\n"))
    print("changelog：已新增 %s" % ", ".join("v" + e["version"] for e in news))
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只对比不写文件")
    ap.add_argument("--local", help="使用本地 manifest.json（离线调试）")
    args = ap.parse_args()

    m = load_manifest(args.local)
    print("manifest：v%s · %s" % (m.get("version"), m.get("released") or "无日期"))
    changed = sync_site_json(m, args.check)
    changed |= sync_changelog(m, args.check)
    if args.check and changed:
        sys.exit(2)
    print("✅ 同步完成" if not args.check else "✅ 无待同步项")


if __name__ == "__main__":
    main()
