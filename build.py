#!/usr/bin/env python3
"""发布站构建脚本：content/changelog/<产品>.md + site.json → dist/

    python3 build.py            # 构建到 dist/
    python3 build.py --serve    # 构建后在 http://127.0.0.1:8000 预览

产出：
    dist/index.html                    产品列表（最新版本 + 下载）
    dist/changelog/index.html          全部产品的更新日志，可按产品筛选，每个版本都有锚点
    dist/updates/<产品>/changelog.json 应用内「有新版本」弹窗读这个（与网页同源）
    dist/updates/all.json
    dist/<路径>                        content/static/<路径> 原样复制（如 KVMini/privacy-policy/）

只用标准库，兼容 Python 3.9。
"""
import datetime
import html
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
HEAD_RX = re.compile(r"^##\s+v?(\d+(?:\.\d+){1,3}(?:[-+][\w.]+)?)\s*[·|]\s*(\S+)(?:\s*[·|]\s*(.+?))?\s*$")
DATE_RX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SAFE_URL = re.compile(r"^(https?://|mailto:|/|#)")


class ChangelogError(ValueError):
    pass


# ---------- 解析 ----------

def inline(text):
    """极小的行内 Markdown：**粗体**、`代码`、[文字](链接)。先转义，杜绝 HTML 注入。"""
    s = html.escape(text, quote=True)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)

    def link(m):
        url = html.unescape(m.group(2))
        if not SAFE_URL.match(url):
            return m.group(1)
        return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (html.escape(url, quote=True), m.group(1))
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)


def parse_changelog(text, pid):
    text = re.sub(r"<!--[\s\S]*?-->", lambda m: "\n" * m.group(0).count("\n"), text)
    releases, cur, group, seen = [], None, None, set()
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        where = "%s.md:%d" % (pid, no)
        if not line.strip():
            continue
        if line.startswith("## "):
            m = HEAD_RX.match(line)
            if not m:
                raise ChangelogError("%s 版本标题格式应为「## v1.2.3 · 2026-10-06」，实际：%s" % (where, line))
            ver, date, flag = m.group(1), m.group(2), (m.group(3) or "").strip()
            if not DATE_RX.match(date):
                raise ChangelogError("%s 日期应为 YYYY-MM-DD，实际：%s" % (where, date))
            datetime.date.fromisoformat(date)
            if ver in seen:
                raise ChangelogError("%s 版本 %s 重复" % (where, ver))
            seen.add(ver)
            cur = {"product": pid, "version": ver, "date": date, "flag": flag, "groups": [], "note": ""}
            releases.append(cur)
            group = None
        elif line.startswith("### "):
            if cur is None:
                raise ChangelogError("%s 分类标题前缺少版本标题" % where)
            group = {"title": line[4:].strip(), "items": [], "items_html": []}
            cur["groups"].append(group)
        elif re.match(r"^\s*[-*]\s+", line):
            if group is None:
                raise ChangelogError("%s 列表项前缺少「### 分类」（新功能 / 改进 / 修复）" % where)
            item = re.sub(r"^\s*[-*]\s+", "", line)
            group["items"].append(item)
            group["items_html"].append(inline(item))
        elif line.startswith(">"):
            if cur is None:
                raise ChangelogError("%s 备注前缺少版本标题" % where)
            note = re.sub(r"^>\s*(注[:：]\s*)?", "", line)
            cur["note"] = (cur["note"] + " " + note).strip()
        else:
            raise ChangelogError("%s 无法识别的行：%s" % (where, line))
    for r in releases:
        if not any(g["items"] for g in r["groups"]):
            raise ChangelogError("%s.md 版本 %s 没有任何条目" % (pid, r["version"]))
    return releases


def cn_date(iso):
    d = datetime.date.fromisoformat(iso)
    return "%d年%d月%d日" % (d.year, d.month, d.day)


def vkey(v):
    return tuple(int(x) for x in re.findall(r"\d+", v.split("-")[0].split("+")[0]))


# ---------- 渲染 ----------

def page(site, title, body, active, depth):
    up = "../" * depth
    e = html.escape
    nav = "".join('<a class="%s" href="%s%s">%s</a>' % ("on" if k == active else "", up, href, name)
                  for k, href, name in (("home", "", "产品"), ("changelog", "changelog/", "更新日志")))
    return """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s · %(brand)s</title>
<meta name="description" content="%(lead)s">
<link rel="stylesheet" href="%(up)sassets/site.css?v=%(ver)s">
<link rel="preload" href="%(up)sassets/fonts/instrument-serif-italic-latin.woff2" as="font" type="font/woff2" crossorigin>
</head>
<body>
<div class="wrap">
<header>
  <a class="logo" href="%(up)s"><i></i>%(brand)s</a>
  <nav>%(nav)s<a class="btn" href="%(up)s#products">下载</a></nav>
</header>
%(body)s
<footer>
  <span>站点 v%(ver)s · 构建于 %(built)s</span>
  <span><a href="%(repo)s" target="_blank" rel="noopener">GitHub</a></span>
</footer>
</div>
<script src="%(up)sassets/site.js?v=%(ver)s"></script>
</body>
</html>
""" % {"title": e(title), "brand": e(site["brand"]), "lead": e(site["lead"]), "up": up, "nav": nav,
       "body": body, "ver": e(site["site_version"]), "built": site["_built"], "repo": e(site["repo_url"])}


def product_cards(site, latest, up):
    out = []
    for p in site["products"]:
        r = latest.get(p["id"])
        ver = ('<a href="%schangelog/#%s-v%s">v%s</a> · %s' % (up, p["id"], r["version"], r["version"], cn_date(r["date"]))
               if r else "尚未发布")
        dls = []
        for d in p.get("downloads", []):
            if d.get("url"):
                dls.append('<a href="%s">%s</a>' % (html.escape(d["url"], quote=True), html.escape(d["label"])))
            else:
                dls.append('<span class="soon" title="即将提供">%s · 即将提供</span>' % html.escape(d["label"]))
        links = "".join('<a href="%s">%s</a>' % (html.escape(l["url"], quote=True), html.escape(l["label"]))
                        for l in p.get("links", []) if l.get("url") and SAFE_URL.match(l["url"]))
        note = '<p class="pnote">%s</p>' % inline(p["note"]) if p.get("note") else ""
        out.append("""<div class="prod" style="--c:%s" data-k="%s">
  <b>%s</b><small>%s</small><p>%s</p>%s<div class="dl">%s</div>%s</div>""" % (
            html.escape(p["color"]), p["id"], html.escape(p["name"]), ver,
            html.escape(p["desc"]), note, "".join(dls),
            '<div class="links">%s</div>' % links if links else ""))
    return '<section class="products" id="products">%s</section>' % "".join(out)


def entry(r, p):
    rid = "%s-v%s" % (r["product"], r["version"])
    plats = "".join('<span class="plat">%s</span>' % html.escape(x) for x in p.get("platforms", []))
    flag = '<span class="flag">%s</span>' % html.escape(r["flag"]) if r["flag"] else ""
    groups = "".join("<h3>%s</h3><ul>%s</ul>" % (html.escape(g["title"]), "".join("<li>%s</li>" % i for i in g["items_html"]))
                     for g in r["groups"] if g["items"])
    note = '<p class="note">注：%s</p>' % inline(r["note"]) if r["note"] else ""
    return """<article class="entry" id="%s" data-p="%s">
  <div class="meta"><a class="ver" href="#%s">v%s</a><span class="tag" style="--c:%s">%s</span>
  <span class="date">%s</span>%s%s</div>%s%s</article>""" % (
        rid, r["product"], rid, html.escape(r["version"]), html.escape(p["color"]), html.escape(p["name"]),
        cn_date(r["date"]), plats, flag, groups, note)


def build(root=ROOT, out=None):
    out = out or os.path.join(root, "dist")
    with open(os.path.join(root, "site.json"), encoding="utf-8") as f:
        site = json.load(f)
    site["_built"] = datetime.date.today().isoformat()
    prods = {p["id"]: p for p in site["products"]}

    cdir = os.path.join(root, "content", "changelog")
    by_p = {pid: [] for pid in prods}
    for fn in sorted(os.listdir(cdir)):
        if not fn.endswith(".md"):
            continue
        pid = fn[:-3]
        if pid not in prods:
            raise ChangelogError("%s 没有在 site.json 的 products 里登记" % fn)
        with open(os.path.join(cdir, fn), encoding="utf-8") as f:
            by_p[pid] = parse_changelog(f.read(), pid)

    for pid, rs in by_p.items():
        rs.sort(key=lambda r: vkey(r["version"]), reverse=True)
    latest = {pid: rs[0] for pid, rs in by_p.items() if rs}
    allrs = sorted((r for rs in by_p.values() for r in rs), key=lambda r: (r["date"], vkey(r["version"])), reverse=True)

    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, "changelog"))
    shutil.copytree(os.path.join(root, "assets"), os.path.join(out, "assets"))
    if os.path.isdir(os.path.join(root, "pa")):   # Prompt Archive 手机端（纯静态，原样发布到 /pa/）
        shutil.copytree(os.path.join(root, "pa"), os.path.join(out, "pa"))
    open(os.path.join(out, ".nojekyll"), "w").close()
    static = os.path.join(root, "content", "static")
    if os.path.isdir(static):   # 原样发布的静态页（隐私政策等），不得覆盖生成的页面
        reserved = {"index.html", "404.html", "changelog", "updates", "assets", "pa"}
        for name in os.listdir(static):
            if name in reserved:
                raise ChangelogError("content/static/%s 与生成的页面重名" % name)
            src, dst = os.path.join(static, name), os.path.join(out, name)
            (shutil.copytree if os.path.isdir(src) else shutil.copy2)(src, dst)

    e = html.escape
    home = """<main>
  <div class="eyebrow">Apps</div>
  <h1>小而稳的工具</h1>
  <p class="lead">%s</p>
  %s
  <p class="more"><a href="changelog/">查看全部更新日志 →</a></p>
</main>""" % (e(site["lead"]), product_cards(site, latest, ""))
    write(os.path.join(out, "index.html"), page(site, "产品", home, "home", 0))

    filt = '<button class="on" data-k="all">全部</button>' + "".join(
        '<button data-k="%s">%s</button>' % (p["id"], e(p["name"])) for p in site["products"])
    entries = "".join(entry(r, prods[r["product"]]) for r in allrs) or \
        '<p class="empty">还没有发布记录。</p>'
    cl = """<main>
  <div class="eyebrow">Updates</div>
  <h1>更新日志</h1>
  <p class="lead">所有产品的每一次发布，最新优先。本页与应用内的更新提示用的是同一份数据。</p>
  %s
  <div class="filter" id="filter">%s</div>
  <section id="list">%s</section>
</main>""" % (product_cards(site, latest, "../"), filt, entries)
    write(os.path.join(out, "changelog", "index.html"), page(site, "更新日志", cl, "changelog", 1))

    nf = '<main><div class="eyebrow">404</div><h1>页面不存在</h1><p class="lead"><a href="/">回到首页 →</a></p></main>'
    write(os.path.join(out, "404.html"), page(site, "404", nf, "", 0).replace('href="assets/', 'href="/assets/')
          .replace('src="assets/', 'src="/assets/'))

    def strip(r):
        return {"version": r["version"], "date": r["date"], "flag": r["flag"], "note": r["note"],
                "groups": [{"title": g["title"], "items": g["items"]} for g in r["groups"] if g["items"]]}
    for pid, rs in by_p.items():
        os.makedirs(os.path.join(out, "updates", pid))
        write(os.path.join(out, "updates", pid, "changelog.json"),
              json.dumps({"product": pid, "latest": rs[0]["version"] if rs else None,
                          "releases": [strip(r) for r in rs]}, ensure_ascii=False, indent=1))
    write(os.path.join(out, "updates", "all.json"),
          json.dumps({"site_version": site["site_version"],
                      "products": {pid: (rs[0]["version"] if rs else None) for pid, rs in by_p.items()}},
                     ensure_ascii=False, indent=1))
    return out


def write(path, s):
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)


def main():
    try:
        out = build()
    except ChangelogError as ex:
        print("构建失败：%s" % ex, file=sys.stderr)
        return 1
    n = sum(1 for _ in os.walk(out) for _ in _[2])
    print("构建完成：%s（%d 个文件）" % (out, n))
    if "--serve" in sys.argv:
        import functools
        import http.server
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=out)
        print("预览：http://127.0.0.1:8000/")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8000), h).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
