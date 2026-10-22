#!/usr/bin/env python3
"""从应用源码里的应用内更新日志生成**草稿** drafts/<产品>[.en].md。

应用内日志是写给开发者自己看的，规则过滤只能去掉大部分内部条目，剩下的仍需人工改写成用户语言，
所以本脚本只出草稿：对照草稿改写后，再手动更新 content/changelog/<产品>.md。

    python3 tools/import_changelog.py kvmini     ~/Documents/Git/KVMini/src-tauri/src/main.rs
    python3 tools/import_changelog.py snipscribe ~/Documents/Git/OnenoteCopy/src-tauri/src/changelog.rs
    python3 tools/import_changelog.py lifetree   ~/Documents/Git/AI\\ Project/生命树-APP/LifeTree/LifeTree/Core/AppChangelog.swift
    加 --dry-run 只打印统计，不写文件
    加 --lang en 出英文草稿（drafts/<产品>.en.md），--lang both 中英都出

源文件格式按扩展名自动判断：.rs = Rust `ChangelogEntry`，.swift = Swift `ChangelogEntry(...)`。

规则（应用内日志是写给开发者自己看的，公开网站只留用户能感知的变化）：
- 剔除含内部术语的条目（Bug 编号、构建脚本、签名、单测、SDK、审核元数据……）
- SnipScribe 只导入 1.0.0 及以后（之前是上架前的内部版本）
- 生命树（lifetree）的条目本身就是用户语言，不做术语过滤，只归类
- 归类：SnipScribe 看行首 emoji；KVMini / 生命树看行首动词
- 一个版本过滤后没有条目，就不出现在网站上
"""
import argparse
import os
import re
import sys

# 区分大小写、英文按整词匹配：曾因不区分大小写把「Office」里的 ffi 当成 FFI 误删
INTERNAL = re.compile(
    r"BUG-?\d|Bug ?#\d|\b(?:FFI|ASC|SDK|MAS|ObjC|LTO|CI|IAP|StoreKit|TestFlight|Rust|Maccy|Carbon)\b|"
    r"\b(?:codesign|entitlements?|commerce|arboard|productId|navigator|locale|spawn|clippy|cargo|feature)\b|"
    r"build\.sh|CGEvent|NSPasteboard|Info\.plist|CFBundle|direct-paste|"
    r"单测|单元测试|测试全部|用例|源码|沙盒|二进制|元数据|根因|真凶|回查|实测|归档|铁律|奥卡姆|重构|"
    r"沿用 v|防回归|DMG 版|日志模块|流水线|诊断|更新日志|推广图|开发期|白名单|"
    r"调试|debug|PeerLog|TDD|测试覆盖|契约测试|runtime\.log|\b0x[0-9A-Fa-f]+\b")
# 代码标识符：snake_case、camelCase、PascalCase 复合词、::、()、文件后缀、key=value
JARGON = re.compile(
    r"\b[a-z]+_[a-z0-9_]+\b|\b[a-z]+[A-Z]\w*\b|\b[A-Z][a-z]+[A-Z]\w*\b|::|\w\(\)|"
    r"\.(?:sh|json|toml|js|ts|rs|dll|plist)\b|\w+=\w+|i18n|\btrait\b|payload|\bkey\b|\bhook\b|Hook\b|模块|协议")
BRANDS = re.compile(r"BetterTouchTool|CleanShot|PowerPoint|WordPad|OneNote|SnipScribe|KVMini|MacBook|iPhone|macOS")
PAREN = re.compile(r"（[^（）]*）|\([^()]*\)")


def jargon(s):
    return bool(JARGON.search(BRANDS.sub("", s)))


def simplify(text):
    """去掉括号里的技术细节、冒号后的根因分析；剩下的仍有代码标识符就返回空串（整条剔除）。"""
    text = re.sub(r"[（(]P\d[）)]", "", text)
    text = PAREN.sub(lambda m: "" if jargon(m.group(0)) or INTERNAL.search(m.group(0)) else m.group(0), text)
    if "：" in text:
        head, tail = text.split("：", 1)
        if (jargon(tail) or INTERNAL.search(tail)) and len(head) >= 6:
            text = head
    text = re.sub(r"\s{2,}", " ", text).strip().rstrip("，,；;")
    if jargon(text) or INTERNAL.search(text):
        return ""
    return text


EMOJI_GROUP = {"✨": "新功能", "🆕": "新功能", "🐛": "修复", "🩹": "修复"}
EMOJI_DROP = set("🧪🔁📝🍎🔒🔍✅")
LEAD_EMOJI = re.compile(r"^([\U0001F000-\U0001FFFF\u2600-\u27BF\u2B00-\u2BFF])\ufe0f?\s*")
TAG = re.compile(r"^【[^】]*】\s*")


def unescape(s):
    s = re.sub(r"\\u\{([0-9a-fA-F]+)\}", lambda m: chr(int(m.group(1), 16)), s)
    return s.replace('\\"', '"').replace("\\\\", "\\")


def vec_items(block, key, rust=True):
    """取 `key: vec![ ... ]`（Rust）里的字符串；没有该 key 返回 []"""
    m = re.search(key + r":\s*vec!\[(.*?)\n?\s*\]", block, re.S) if rust else None
    if not m:
        return []
    return [unescape(x) for x in re.findall(r'"((?:[^"\\]|\\.)*)"\.to_string\(\)', m.group(1))]


def parse_rust(text):
    """Rust 的 ChangelogEntry { ... }；changes_en 有就一并返回（--lang en 要用）"""
    out = []
    for b in re.findall(r"ChangelogEntry\s*\{(.*?)\n\s*\},", text, re.S):
        v = re.search(r'version:\s*"([^"]+)"', b)
        d = re.search(r'date:\s*"([^"]+)"', b)
        if not (v and d):
            continue
        items = vec_items(b, "changes")
        if not items:
            continue
        out.append({
            "version": v.group(1),
            "date": d.group(1),
            "items": items,
            "items_en": vec_items(b, "changes_en"),
        })
    return out


def parse_swift(text):
    """解析 Swift 的 ChangelogEntry(version:date:changes:changesEn:)

    changesEn 可选：老版本可能还没补英文，这时中文条目照样要出来（不能整条消失）
    """
    out = []
    for m in re.finditer(
            r'ChangelogEntry\(\s*version:\s*"([^"]+)",\s*date:\s*"([^"]+)",\s*'
            r'changes:\s*\[(.*?)\n\s*\](?:,\s*changesEn:\s*\[(.*?)\n\s*\])?\s*\)', text, re.S):
        version, date, zh, en = m.groups()
        out.append({
            "version": version,
            "date": date,
            "items": [unescape(x) for x in re.findall(r'"((?:[^"\\]|\\.)*)"', zh)],
            "items_en": [unescape(x) for x in re.findall(r'"((?:[^"\\]|\\.)*)"', en or "")],
        })
    return out


def vkey(v):
    return tuple(int(x) for x in re.findall(r"\d+", v))


# 生命树的 App 内条目本身就是用户语言（还要给 App 里的更新弹窗看），不做术语过滤
NO_FILTER = {"lifetree"}

EN_GROUP = {"新功能": "New", "改进": "Improved", "修复": "Fixed"}


def classify_en(text):
    """英文条目归类：返回中文分组键，渲染时再映射成 New / Improved / Fixed"""
    if re.match(r"^(fix|fixed|fixes|resolve[sd]?|no longer)", text, re.I):
        return "修复"
    if re.match(r"^(new|add(ed|s)?|support(s|ed)?|introduc\w+|first)", text, re.I):
        return "新功能"
    return "改进"


def classify(product, item, en=False):
    """返回 (分组, 清洗后的文本)；分组为 None 表示剔除，'note' 表示放进版本备注。"""
    text = item.strip()
    m = LEAD_EMOJI.match(text)
    emoji = m.group(1) if m else ""
    text = LEAD_EMOJI.sub("", text)
    text = TAG.sub("", text).strip()
    if "仍在开发中" in text or "请只在可信" in text:
        return "note", text
    if en:
        return classify_en(text), text
    if product not in NO_FILTER:
        text = simplify(text)
        if not text:
            return None, text
    if product == "snipscribe":
        if emoji in EMOJI_DROP:
            return None, text
        if emoji in EMOJI_GROUP:
            return EMOJI_GROUP[emoji], text
        if text.startswith(("修复", "解决")):
            return "修复", text
        return "改进", text
    if re.match(r"^(修复|修正|解决)", text):
        return "修复", text
    if re.match(r"^(新增|新功能|支持|首版|首个)", text):
        return "新功能", text
    return "改进", text


def to_markdown(product, entries, lang="zh"):
    """lang=zh 出中文草稿，lang=en 出英文草稿（条目取 changesEn，分组标题 New/Improved/Fixed）"""
    en = lang == "en"
    lines = []
    kept_versions = dropped = kept = 0
    for e in sorted(entries, key=lambda x: vkey(x["version"]), reverse=True):
        if product == "snipscribe" and vkey(e["version"]) < (1, 0, 0):
            continue
        items = e.get("items_en") if en else e["items"]
        if not items:
            continue
        # 英文条目沿用中文的归类：同一条改动在两种语言里应该是同一类
        # （中英文行首用词不同，各按各的动词分会把同一条分到不同的组）
        zh_keys = None
        if en and e.get("items"):
            zh_keys = [classify(product, it)[0] for it in e["items"]]
        groups = {"新功能": [], "改进": [], "修复": []}
        notes = []
        for i, it in enumerate(items):
            g = zh_keys[i] if zh_keys and i < len(zh_keys) and zh_keys[i] else None
            if g:
                t = it.strip()
            else:
                g, t = classify(product, it, en=en)
            if g is None:
                dropped += 1
            elif g == "note":
                notes.append(t)
            else:
                groups[g].append(t.replace("\n", " "))
                kept += 1
        if not any(groups.values()):
            continue
        kept_versions += 1
        lines.append("## v%s · %s" % (e["version"], e["date"]))
        for g in ("新功能", "改进", "修复"):
            if groups[g]:
                lines.append("### " + (EN_GROUP[g] if en else g))
                lines += ["- " + t for t in groups[g]]
        for n in notes:
            lines.append("> " + ("Note: " if en else "注：") + n)
        lines.append("")
    return "\n".join(lines), {"versions": kept_versions, "kept": kept, "dropped": dropped}


HEADER = "<!-- 草稿：由 tools/import_changelog.py 生成，需人工改写后再并入 content/changelog/ -->\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("product")
    ap.add_argument("source")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--lang", default="zh", choices=["zh", "en", "both"],
                    help="出中文草稿 / 英文草稿 / 两种都要（默认 zh）")
    a = ap.parse_args()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.expanduser(a.source), encoding="utf-8") as f:
        src = f.read()
    entries = parse_swift(src) if a.source.endswith(".swift") else parse_rust(src)
    if not entries:
        print("在 %s 里没找到 ChangelogEntry" % a.source, file=sys.stderr)
        return 1
    if a.lang in ("en", "both"):
        missing = [e["version"] for e in entries if not e.get("items_en")]
        if missing:
            print("[提示] 这些版本没有英文条目，英文草稿里不会出现：%s" % "、".join(missing))

    for lang in (["zh", "en"] if a.lang == "both" else [a.lang]):
        dst = os.path.join(root, "drafts", a.product + (".en.md" if lang == "en" else ".md"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        body, st = to_markdown(a.product, entries, lang)
        print("%s(%s)：源 %d 个版本 → 网站 %d 个版本；保留 %d 条，剔除 %d 条"
              % (a.product, lang, len(entries), st["versions"], st["kept"], st["dropped"]))
        if not a.dry_run:
            with open(dst, "w", encoding="utf-8") as f:
                f.write(HEADER + "\n" + body)
            print("已写入", dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
