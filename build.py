#!/usr/bin/env python3
"""发布站构建脚本：content/changelog/<产品>.md + site.json → dist/

    python3 build.py            # 构建到 dist/
    python3 build.py --serve    # 构建后在 http://127.0.0.1:8000 预览

产出（中文在根目录，英文在 /en/）：
    dist/index.html                    产品列表（最新版本 + 下载）
    dist/changelog/index.html          全部产品的更新日志，可按产品筛选，每个版本都有锚点
    dist/en/index.html                 英文产品列表
    dist/en/changelog/index.html       英文更新日志（content/changelog/en/<产品>.md）
    dist/updates/<产品>/changelog.json 应用内「有新版本」弹窗读这个（与网页同源）
    dist/updates/all.json
    dist/<路径>                        content/static/<路径> 原样复制（如 KVMini/privacy-policy/）

多语言：
    - site.json 中文字段为默认，英文用 `<字段>_en`（lead_en、name_en、desc_en、note_en、
      platforms_en、downloads[].label_en、links[].label_en），缺省时回落中文
    - 英文更新日志 content/changelog/en/<产品>.md 必须覆盖中文版的每个版本（版本号与日期一致），
      否则构建失败；没有英文文件的产品，英文页显示中文条目并标注
    - 中文页在浏览器语言不是中文、且用户没手动选过语言时跳到英文页

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
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

# 界面文案。新增语言：在这里加一组，并在 site.json 中提供 `<字段>_<语言>`
LANGS = {
    "zh": {
        "html_lang": "zh-CN", "hreflang": "zh-CN", "root": "", "switch_to": "en", "switch_label": "English",
        "nav_home": "产品", "nav_changelog": "更新日志", "nav_download": "下载",
        # 首屏大标题拆成两段：末尾那个词（home_h1_tail）单独上主色渐变，其余保持白色
        "home_title": "产品", "home_eyebrow": "Apps", "home_h1": "让日常，多一点", "home_h1_tail": "称手",
        "more": "查看全部更新日志 →",
        "cl_title": "更新日志", "cl_eyebrow": "Updates", "cl_h1": "更新日志",
        "cl_lead": "所有产品的每一次发布，最新优先。本页与应用内的更新提示用的是同一份数据。",
        "all": "全部", "empty": "还没有发布记录。", "unreleased": "尚未发布", "soon": "即将提供",
        "note": "注：", "footer": "站点 v%s · 构建于 %s", "zh_only": "",
        "stat_products": "款产品", "stat_platforms": "个平台", "stat_updated": "最近更新",
    },
    "en": {
        "html_lang": "en", "hreflang": "en", "root": "en/", "switch_to": "zh", "switch_label": "中文",
        "nav_home": "Products", "nav_changelog": "Changelog", "nav_download": "Download",
        # 英文的尾词前要留空格，用字符串末尾的空格实现（中文不需要）
        "home_title": "Products", "home_eyebrow": "Apps", "home_h1": "Everyday things, made ",
        "home_h1_tail": "well",
        "more": "See all release notes →",
        "cl_title": "Changelog", "cl_eyebrow": "Updates", "cl_h1": "Changelog",
        "cl_lead": "Every release of every product, newest first.",
        "all": "All", "empty": "No releases yet.", "unreleased": "Not released yet", "soon": "Coming soon",
        "note": "Note: ", "footer": "Site v%s · built %s",
        "zh_only": "Release notes for %s are only available in Chinese.",
        "stat_products": "products", "stat_platforms": "platforms", "stat_updated": "Last update",
    },
}


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
            note = re.sub(r"^>\s*(注[:：]|Note:)?\s*", "", line)
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


def en_date(iso):
    d = datetime.date.fromisoformat(iso)
    return "%s %d, %d" % (MONTHS[d.month - 1], d.day, d.year)


def fmt_date(iso, lang):
    return cn_date(iso) if lang == "zh" else en_date(iso)


def vkey(v):
    return tuple(int(x) for x in re.findall(r"\d+", v.split("-")[0].split("+")[0]))


def tr(obj, key, lang):
    """取 `<key>_<lang>`，没有则回落中文字段"""
    if lang != "zh" and obj.get("%s_%s" % (key, lang)):
        return obj["%s_%s" % (key, lang)]
    return obj.get(key, "")


def check_translation(pid, zh, en):
    """英文更新日志必须与中文版的版本、日期一一对应"""
    zmap = {r["version"]: r["date"] for r in zh}
    emap = {r["version"]: r["date"] for r in en}
    missing = sorted(set(zmap) - set(emap), key=vkey, reverse=True)
    extra = sorted(set(emap) - set(zmap), key=vkey, reverse=True)
    wrong = [v for v in zmap if v in emap and zmap[v] != emap[v]]
    if missing or extra or wrong:
        raise ChangelogError("en/%s.md 与 %s.md 不一致：缺少 %s；多出 %s；日期不同 %s" % (
            pid, pid, ", ".join(missing) or "无", ", ".join(extra) or "无", ", ".join(wrong) or "无"))


# ---------- 渲染 ----------

def page(site, lang, title, body, active, path, depth, up=None, redirect=True):
    """path：本页相对站点根的路径（不含语言前缀），如 "" 或 "changelog/" """
    L = LANGS[lang]
    other = LANGS[L["switch_to"]]
    up = ("../" * depth) if up is None else up
    home = up + L["root"]
    e = html.escape
    nav = "".join('<a class="%s" href="%s%s">%s</a>' % ("on" if k == active else "", home, href, name)
                  for k, href, name in (("home", "", L["nav_home"]), ("changelog", "changelog/", L["nav_changelog"])))
    switch = '<a class="lang" data-lang="%s" hreflang="%s" href="%s%s%s">%s</a>' % (
        L["switch_to"], other["hreflang"], up, other["root"], path, L["switch_label"])
    base = site.get("base_url", "").rstrip("/") + "/"
    alternates = "".join('<link rel="alternate" hreflang="%s" href="%s%s%s">\n' % (
        LANGS[k]["hreflang"], base, LANGS[k]["root"], path) for k in LANGS)
    alternates += '<link rel="alternate" hreflang="x-default" href="%s%s">\n' % (base, path)
    # 中文页：浏览器语言不是中文、且没手动选过语言时跳到英文页（选择记在 localStorage.siteLang）
    auto = ""
    if lang == "zh" and redirect:
        auto = ('<script>(function(){try{if(localStorage.getItem("siteLang"))return;'
                'var l=(navigator.languages&&navigator.languages[0])||navigator.language||"";'
                'if(l&&!/^zh/i.test(l))location.replace("%s%s%s"+location.search+location.hash);}catch(e){}})();</script>\n'
                % (up, LANGS["en"]["root"], path))
    return """<!doctype html>
<html lang="%(html_lang)s">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s · %(brand)s</title>
<meta name="description" content="%(lead)s">
%(alternates)s%(auto)s<link rel="stylesheet" href="%(up)sassets/site.css?v=%(ver)s">
<link rel="preload" href="%(up)sassets/fonts/instrument-serif-latin.woff2" as="font" type="font/woff2" crossorigin>
</head>
<body>
<div class="wrap">
<header>
  <a class="logo" href="%(home)s"><i></i>%(brand)s</a>
  <nav>%(nav)s%(switch)s<a class="btn" href="%(home)s#products">%(download)s</a></nav>
</header>
%(body)s
<footer>
  <span>%(footer)s</span>
  <span><a href="%(repo)s" target="_blank" rel="noopener">GitHub</a></span>
</footer>
</div>
<script src="%(up)sassets/site.js?v=%(ver)s"></script>
</body>
</html>
""" % {"html_lang": L["html_lang"], "title": e(title), "brand": e(tr(site, "brand", lang)),
       "lead": e(tr(site, "lead", lang)), "alternates": alternates, "auto": auto, "up": up, "home": home,
       "nav": nav, "switch": switch, "download": L["nav_download"], "body": body,
       "ver": e(site["site_version"]), "footer": e(L["footer"] % (site["site_version"], site["_built"])),
       "repo": e(site["repo_url"])}


def product_cards(site, latest, base, lang):
    """base：本语言的站点根（相对当前页），用于拼更新日志链接"""
    L = LANGS[lang]
    out = []
    for p in site["products"]:
        r = latest.get(p["id"])
        # 版本号做成徽章并链到对应产品的更新日志；没发布过就只给「尚未发布」
        ver = ('<a class="ver" href="%schangelog/#%s-v%s">v%s</a>' % (
            base, p["id"], r["version"], r["version"])) if r else ""
        when = '<span class="date">%s</span>' % (fmt_date(r["date"], lang) if r else L["unreleased"])
        # 平台此前一直没显示出来（site.json 里有 platforms），卡片信息量的一半在这
        plats = tr(p, "platforms", lang) or []
        plats_html = "".join('<span class="plat">%s</span>' % html.escape(str(x)) for x in plats)
        dls = []
        for d in p.get("downloads", []):
            label = html.escape(tr(d, "label", lang))
            if d.get("url"):
                dls.append('<a href="%s">%s</a>' % (html.escape(d["url"], quote=True), label))
            else:
                dls.append('<span class="soon" title="%s">%s · %s</span>' % (L["soon"], label, L["soon"]))
        links = "".join('<a href="%s">%s</a>' % (html.escape(l["url"], quote=True), html.escape(tr(l, "label", lang)))
                        for l in p.get("links", []) if l.get("url") and SAFE_URL.match(l["url"]))
        note = tr(p, "note", lang)
        note = '<p class="pnote">%s</p>' % inline(note) if note else ""
        out.append("""<div class="prod" style="--c:%s" data-k="%s">
  <div class="ptop"><span class="dot"></span><h3>%s</h3>%s</div>
  <div class="pmeta">%s%s</div>
  <p class="desc">%s</p>%s<div class="dl">%s</div>%s</div>""" % (
            html.escape(p["color"]), p["id"], html.escape(tr(p, "name", lang)), ver,
            '<div class="plats">%s</div>' % plats_html if plats_html else "", when,
            html.escape(tr(p, "desc", lang)), note, "".join(dls),
            '<div class="links">%s</div>' % links if links else ""))
    return '<section class="products" id="products">%s</section>' % "".join(out)


def entry(r, p, lang):
    rid = "%s-v%s" % (r["product"], r["version"])
    plats = "".join('<span class="plat">%s</span>' % html.escape(x)
                    for x in (tr(p, "platforms", lang) or []))
    flag = '<span class="flag">%s</span>' % html.escape(r["flag"]) if r["flag"] else ""
    groups = "".join("<h3>%s</h3><ul>%s</ul>" % (html.escape(g["title"]), "".join("<li>%s</li>" % i for i in g["items_html"]))
                     for g in r["groups"] if g["items"])
    note = '<p class="note">%s%s</p>' % (LANGS[lang]["note"], inline(r["note"])) if r["note"] else ""
    return """<article class="entry" id="%s" data-p="%s">
  <div class="meta"><a class="ver" href="#%s">v%s</a><span class="tag" style="--c:%s">%s</span>
  <span class="date">%s</span>%s%s</div>%s%s</article>""" % (
        rid, r["product"], rid, html.escape(r["version"]), html.escape(p["color"]), html.escape(tr(p, "name", lang)),
        fmt_date(r["date"], lang), plats, flag, groups, note)


def load_changelogs(cdir, prods):
    by_p = {pid: [] for pid in prods}
    for fn in sorted(os.listdir(cdir)):
        if not fn.endswith(".md"):
            continue
        pid = fn[:-3]
        if pid not in prods:
            raise ChangelogError("%s 没有在 site.json 的 products 里登记" % fn)
        with open(os.path.join(cdir, fn), encoding="utf-8") as f:
            by_p[pid] = parse_changelog(f.read(), pid)
    for rs in by_p.values():
        rs.sort(key=lambda r: vkey(r["version"]), reverse=True)
    return by_p


def build(root=ROOT, out=None):
    out = out or os.path.join(root, "dist")
    with open(os.path.join(root, "site.json"), encoding="utf-8") as f:
        site = json.load(f)
    site["_built"] = datetime.date.today().isoformat()
    prods = {p["id"]: p for p in site["products"]}

    cdir = os.path.join(root, "content", "changelog")
    by_lang = {"zh": load_changelogs(cdir, prods)}
    zh_only = []
    for lang in LANGS:
        if lang == "zh":
            continue
        ldir = os.path.join(cdir, lang)
        translated = load_changelogs(ldir, prods) if os.path.isdir(ldir) else {pid: [] for pid in prods}
        merged = {}
        for pid, zrs in by_lang["zh"].items():
            has_file = os.path.isfile(os.path.join(ldir, pid + ".md"))
            if has_file:
                check_translation(pid, zrs, translated[pid])
                merged[pid] = translated[pid]
            else:
                merged[pid] = zrs
                if zrs and lang == "en":
                    zh_only.append(pid)
        by_lang[lang] = merged

    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, "changelog"))
    shutil.copytree(os.path.join(root, "assets"), os.path.join(out, "assets"))
    if os.path.isdir(os.path.join(root, "pa")):   # Prompt Archive 手机端（纯静态，原样发布到 /pa/）
        shutil.copytree(os.path.join(root, "pa"), os.path.join(out, "pa"))
    open(os.path.join(out, ".nojekyll"), "w").close()
    static = os.path.join(root, "content", "static")
    if os.path.isdir(static):   # 原样发布的静态页（隐私政策等），不得覆盖生成的页面
        reserved = {"index.html", "404.html", "changelog", "updates", "assets", "pa"} | \
            {LANGS[k]["root"].strip("/") for k in LANGS if LANGS[k]["root"]}
        for name in os.listdir(static):
            if name in reserved:
                raise ChangelogError("content/static/%s 与生成的页面重名" % name)
            src, dst = os.path.join(static, name), os.path.join(out, name)
            (shutil.copytree if os.path.isdir(src) else shutil.copy2)(src, dst)

    e = html.escape
    for lang, L in LANGS.items():
        by_p = by_lang[lang]
        latest = {pid: rs[0] for pid, rs in by_p.items() if rs}
        allrs = sorted((r for rs in by_p.values() for r in rs), key=lambda r: (r["date"], vkey(r["version"])),
                       reverse=True)
        ldir = os.path.join(out, L["root"]) if L["root"] else out
        os.makedirs(os.path.join(ldir, "changelog"), exist_ok=True)
        hd = 1 if L["root"] else 0          # 本语言首页的目录深度

        # 首屏统计带：产品数 / 覆盖平台数 / 最近一次发布
        plats_all = []
        for p in site["products"]:
            for x in (tr(p, "platforms", lang) or []):
                if x not in plats_all:
                    plats_all.append(x)
        newest = max((r["date"] for r in latest.values() if r), default="")
        stats = ('<div class="stats"><span><b>%d</b> %s</span><span><b>%d</b> %s</span>'
                 '<span>%s <b>%s</b></span></div>') % (
            len(site["products"]), L["stat_products"], len(plats_all), L["stat_platforms"],
            L["stat_updated"], fmt_date(newest, lang) if newest else "—")

        home = """<main>
  <div class="eyebrow">%s</div>
  <h1>%s<span class="hl">%s</span></h1>
  <p class="lead">%s</p>
  %s
  %s
  <p class="more"><a href="changelog/">%s</a></p>
</main>""" % (L["home_eyebrow"], L["home_h1"], e(L["home_h1_tail"]),
              e(tr(site, "lead", lang)), stats,
              product_cards(site, latest, "", lang), L["more"])
        write(os.path.join(ldir, "index.html"), page(site, lang, L["home_title"], home, "home", "", hd))

        filt = '<button class="on" data-k="all">%s</button>' % L["all"] + "".join(
            '<button data-k="%s">%s</button>' % (p["id"], e(tr(p, "name", lang))) for p in site["products"])
        entries = "".join(entry(r, prods[r["product"]], lang) for r in allrs) or \
            '<p class="empty">%s</p>' % L["empty"]
        notice = "".join('<p class="note">%s</p>' % e(L["zh_only"] % tr(prods[pid], "name", lang))
                         for pid in (zh_only if lang == "en" else []))
        cl = """<main>
  <div class="eyebrow">%s</div>
  <h1>%s</h1>
  <p class="lead">%s</p>
  %s
  <div class="filter" id="filter">%s</div>
  %s<section id="list">%s</section>
</main>""" % (L["cl_eyebrow"], L["cl_h1"], L["cl_lead"], product_cards(site, latest, "../", lang), filt, notice, entries)
        write(os.path.join(ldir, "changelog", "index.html"),
              page(site, lang, L["cl_title"], cl, "changelog", "changelog/", hd + 1))

    nf = ('<main><div class="eyebrow">404</div><h1>页面不存在 · Page not found</h1>'
          '<p class="lead"><a href="/">回到首页 →</a> · <a href="/en/">Back to home →</a></p></main>')
    write(os.path.join(out, "404.html"), page(site, "zh", "404", nf, "", "", 0, up="/", redirect=False))

    def strip(r):
        return {"version": r["version"], "date": r["date"], "flag": r["flag"], "note": r["note"],
                "groups": [{"title": g["title"], "items": g["items"]} for g in r["groups"] if g["items"]]}
    for pid, rs in by_lang["zh"].items():
        os.makedirs(os.path.join(out, "updates", pid))
        write(os.path.join(out, "updates", pid, "changelog.json"),
              json.dumps({"product": pid, "latest": rs[0]["version"] if rs else None,
                          "releases": [strip(r) for r in rs]}, ensure_ascii=False, indent=1))
    write(os.path.join(out, "updates", "all.json"),
          json.dumps({"site_version": site["site_version"],
                      "products": {pid: (rs[0]["version"] if rs else None) for pid, rs in by_lang["zh"].items()}},
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
