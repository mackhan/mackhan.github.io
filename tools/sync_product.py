#!/usr/bin/env python3
"""把某个产品的「对外门面清单」同步到本仓库（site.json + 中英更新日志）。

所有产品走同一套规则，规则全文见 docs/版本与更新日志规则.md。要点：

- 版本号与更新内容的**唯一真相在产品自己的仓库**，本仓库不再手抄
- 产品发布时生成 manifest.json（版本 + 日期 + 中英更新内容），本脚本拉它写回：
  site.json 的 platforms / downloads / links / manifest / site
  content/changelog/<产品>.md（中文）与 content/changelog/en/<产品>.md（英文）
- 首页构建要求中英更新日志的版本与日期一一对应（build.py 会拦），
  所以清单有 changelog_en 时中英一起写；没有就只写中文并提醒人工补英文
- 默认只补「比本仓库已有最新版本还新」的版本，历史缺口用 --all

manifest 地址的优先级：--local 文件 > --url > site.json 里该产品的 manifest 字段。

用法：
    python3 tools/sync_product.py kvmini                 # 用 site.json 里登记的地址
    python3 tools/sync_product.py moviebox --check       # 只对比，不写文件
    python3 tools/sync_product.py kvmini --local ~/Documents/Git/KVMini/pages/manifest.json
    python3 tools/sync_product.py lifetree --url https://example.com/manifest.json --all
"""
import argparse
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMEOUT = 15


def load_manifest(local=None, url=None):
    if local:
        with open(os.path.expanduser(local), encoding="utf-8") as f:
            return json.load(f)
    req = urllib.request.Request(url, headers={"User-Agent": "mackhan-site-sync"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def manifest_url(pid, site):
    prod = next((p for p in site["products"] if p["id"] == pid), None)
    if prod is None:
        sys.exit("site.json 里没有 id=%s 的产品" % pid)
    if not prod.get("manifest"):
        sys.exit("site.json 里 %s 没有 manifest 字段，用 --url 或 --local 指定清单地址" % pid)
    return prod["manifest"]


def sync_site_json(pid, m, url, dry=False, local=False):
    path = os.path.join(ROOT, "site.json")
    with open(path, encoding="utf-8") as f:
        site = json.load(f)
    prod = next((p for p in site["products"] if p["id"] == pid), None)
    if prod is None:
        sys.exit("site.json 里没有 id=%s 的产品" % pid)

    before = json.dumps(prod, ensure_ascii=False, sort_keys=True)
    if m.get("platforms"):
        prod["platforms"] = m["platforms"]
    # label_en 必须一起带过来：英文页若回落到中文标签，i18n 测试会直接失败。
    # 清单某项没有 label_en 时宁可不带这个键，也不写 null（tr() 会把 null 当假去回落中文）
    def item(d):
        out = {"url": d["url"]}
        if d.get("label"):
            out["label"] = d["label"]
        if d.get("label_en"):
            out["label_en"] = d["label_en"]
        return out

    if m.get("downloads"):
        prod["downloads"] = [item(d) for d in m["downloads"]]
    if m.get("links"):
        prod["links"] = [item(l) for l in m["links"]]
    # --local 时 url 是本机路径，不能写进 site.json（那是给外人看的地址）
    if not local:
        prod["manifest"] = url
    elif not prod.get("manifest"):
        print("site.json：--local 模式下不登记清单地址，请手动填 manifest 字段")
    # 有自己站点的产品：产品名点击后去它自己的站点（build.py 用 site 字段把标题变成链接）
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


def vkey(v):
    """版本号比较键：与 build.py 的 vkey 口径一致（忽略预发布后缀），
    并补零到至少 3 段，避免 "1.0" 与 "1.0.0" 被当成两个版本（元组长度不同时比较会失真）。
    """
    parts = [int(x) for x in re.findall(r"\d+", v.split("-")[0].split("+")[0])]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def render_entry(e):
    """把一个版本条目渲染成 changelog md 片段（日期缺失的条目由调用方先剔除：
    build.py 只认 YYYY-MM-DD，写「待定」会让整站构建失败）"""
    out = ["## v%s · %s" % (e["version"], e["date"]), ""]
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
    # 只有「## v1.2.3」这样的行才算版本边界；其它二级标题（说明、备注）并进上一段，
    # 不因为一行标题就让整次同步中断
    out = []
    for s in segs:
        m = re.match(r"^##\s*v?([\d.]+)", s[0])
        if m:
            out.append((m.group(1), "\n".join(s).rstrip()))
        elif out:
            out[-1] = (out[-1][0], out[-1][1] + "\n" + "\n".join(s).rstrip())
        else:
            head = (head + "\n" + "\n".join(s).rstrip()).strip()
    return head, out


def sync_changelog(pid, m, key, lang, dry=False, backfill=False):
    """把清单里缺失的版本按版本号插到 content/changelog[/en]/<产品>.md 的正确位置"""
    name = "%s.md" % pid if lang == "zh" else "en/%s.md" % pid
    path = os.path.join(ROOT, "content", "changelog", name)
    entries = m.get(key)
    if not entries:
        print("changelog(%s)：清单里没有 %s，跳过（英文需人工补）" % (lang, key))
        return False
    if not os.path.exists(path):
        sys.exit("缺少更新日志文件：%s（新增产品要先建中英两个文件）" % name)
    with open(path, encoding="utf-8") as f:
        text = f.read()

    head, segs = split_releases(text)
    have = {vkey(v) for v, _ in segs}
    top = max(have, default=(0,))

    news = []
    for e in entries:
        v = e["version"]
        if not e.get("groups"):
            continue
        if not e.get("date"):
            print("changelog(%s)：v%s 没有发布日期，跳过（写进去会让首页构建失败）" % (lang, v))
            continue
        if vkey(v) in have:
            continue
        # 默认只补比本仓库已有最新版本还新的版本，历史缺口用 --all
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


def main(argv=None, default_pid=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("product", nargs="?", default=default_pid, help="产品 id，如 kvmini / moviebox")
    ap.add_argument("--check", action="store_true", help="只对比不写文件")
    ap.add_argument("--all", action="store_true", help="连历史缺失版本一起补（默认只补更新的）")
    ap.add_argument("--url", help="清单地址，覆盖 site.json 里的 manifest 字段")
    ap.add_argument("--local", help="本地 manifest.json（发布脚本用，不依赖网络）")
    args = ap.parse_args(argv)
    if not args.product:
        ap.error("必须给出产品 id")

    pid = args.product
    with open(os.path.join(ROOT, "site.json"), encoding="utf-8") as f:
        site = json.load(f)
    url = args.local or args.url or manifest_url(pid, site)

    m = load_manifest(args.local, url)
    print("manifest：v%s · %s" % (m.get("version"), m.get("released") or "无日期"))
    changed = sync_site_json(pid, m, url, args.check, local=bool(args.local))
    changed |= sync_changelog(pid, m, "changelog", "zh", args.check, args.all)
    changed |= sync_changelog(pid, m, "changelog_en", "en", args.check, args.all)

    if args.check:
        if changed:
            sys.exit(2)
        print("✅ 无待同步项")
        return 0
    if changed:
        print("提示：条目来自产品自己的更新日志（机器同步），发布前建议按 tools/import_changelog.py 的"
              "口径改写成用户语言；改完跑 python3 build.py 确认中英文一致。")
    print("✅ 同步完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
