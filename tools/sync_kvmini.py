#!/usr/bin/env python3
"""从 KVMini 的对外门面清单同步产品数据，保证首页与 KVMini 用**同一份数据**。

KVMini 发布时（scripts/release-mac.sh）会生成 pages/manifest.json，
SSOT 来自 KVMini 仓库的 Cargo.toml（版本）+ src-tauri/src/main.rs 的 get_changelog()
（日期与中英文更新内容）。清单作为 Release 资产分发（KVMini 的 github 远端只用于分发，
代码不推，所以不走 raw.githubusercontent）：

    https://github.com/mackhan/KVMini/releases/latest/download/manifest.json

本脚本拉取它，然后：
1. 更新 site.json 里 kvmini 的 platforms / downloads / links（不再两边手写）
2. 把清单里有、首页更新日志里没有的版本插到
   content/changelog/kvmini.md（中文）与 content/changelog/en/kvmini.md（英文）里，
   按版本号从新到旧插到正确位置

与 MovieBox（tools/sync_moviebox.py）不同的两点：
- KVMini 没有自己的 GitHub Pages 站点（首页上的 /KVMini/ 就是它的门面页），
  清单从 Release 资产读，不从 mackhan.github.io/KVMini/manifest.json 读
- 首页构建要求中英更新日志的版本与日期一一对应，所以两个文件一起写，
  中英文都来自清单（英文不是人工补，是应用内日志自带的 changes_en）

默认只补「比首页已有最新版本还新」的版本，避免一次性灌进一堆历史版本；
要补齐历史用 --all。

用法：
    python3 tools/sync_kvmini.py                     # 拉取并同步
    python3 tools/sync_kvmini.py --check             # 只对比，不写文件
    python3 tools/sync_kvmini.py --all               # 连历史缺失版本一起补
    python3 tools/sync_kvmini.py --local ~/Documents/Git/KVMini/pages/manifest.json
"""
import argparse
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_URL = "https://github.com/mackhan/KVMini/releases/latest/download/manifest.json"
PID = "kvmini"
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


def vkey(v):
    return tuple(int(x) for x in re.findall(r"\d+", v))


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


def split_releases(text):
    """拆成 (头部注释, [(version, 片段)])；片段保留原文（去掉尾部空行）"""
    lines = text.split("\n")
    idx = next((i for i, l in enumerate(lines) if l.startswith("## ")), None)
    if idx is None:
        return text.rstrip() + "\n", []
    head = "\n".join(lines[:idx]).rstrip()
    segs, cur = [], None
    for l in lines[idx:]:
        if l.startswith("## "):
            if cur:
                segs.append(cur)
            cur = [l]
        elif cur is not None:
            cur.append(l)
    if cur:
        segs.append(cur)
    return head, [(re.match(r"^##\s*v?([\d.]+)", s[0]).group(1), "\n".join(s).rstrip())
                  for s in segs]


def sync_changelog(m, key, lang, dry=False, backfill=False):
    """把清单里缺失的版本按版本号插到 content/changelog[/en]/kvmini.md 的正确位置"""
    name = "kvmini.md" if lang == "zh" else "en/kvmini.md"
    path = os.path.join(ROOT, "content", "changelog", name)
    with open(path, encoding="utf-8") as f:
        text = f.read()

    head, segs = split_releases(text)
    have = {v for v, _ in segs}
    top = max((vkey(v) for v in have), default=(0,))

    news = []
    for e in m.get(key, []):
        v = e["version"]
        if v in have or not e.get("groups"):
            continue
        # 默认只补比首页已有最新版本还新的版本，历史缺口用 --all 补
        if not backfill and vkey(v) < top:
            continue
        news.append((v, render_entry(e).rstrip()))

    if not news:
        print("changelog(%s)：已是最新（v%s）" % (lang, m.get("version")))
        return False

    news.sort(key=lambda x: vkey(x[0]), reverse=True)
    merged = segs + news
    merged.sort(key=lambda x: vkey(x[0]), reverse=True)
    body = "\n\n".join(s for _, s in merged)
    out = (head + "\n\n" if head else "") + body + "\n"

    if dry:
        print("changelog(%s)：待新增 %s（--check 不写入）"
              % (lang, "、".join("v" + v for v, _ in news)))
        return True
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    print("changelog(%s)：已新增 %s" % (lang, "、".join("v" + v for v, _ in news)))
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只对比不写文件")
    ap.add_argument("--all", action="store_true", help="连历史缺失版本一起补（默认只补比首页最新还新的）")
    ap.add_argument("--local", help="使用本地 manifest.json（发布脚本用，不依赖 push）")
    args = ap.parse_args()

    m = load_manifest(args.local)
    print("manifest：v%s · %s" % (m.get("version"), m.get("released") or "无日期"))
    changed = sync_site_json(m, args.check)
    changed |= sync_changelog(m, "changelog", "zh", args.check, args.all)
    changed |= sync_changelog(m, "changelog_en", "en", args.check, args.all)
    if args.check:
        if changed:
            sys.exit(2)
        print("✅ 无待同步项")
        return
    if changed:
        print("提示：条目来自应用内更新日志（机器同步），发布前建议按 tools/import_changelog.py 的"
              "口径改写成用户语言；改完跑 python3 build.py 确认中英文一致。")
    print("✅ 同步完成")


if __name__ == "__main__":
    main()
