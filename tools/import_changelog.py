#!/usr/bin/env python3
"""从应用源码里的应用内更新日志（Rust `ChangelogEntry` 数组）生成**草稿** drafts/<产品>.md。

应用内日志是写给开发者自己看的，规则过滤只能去掉大部分内部条目，剩下的仍需人工改写成用户语言，
所以本脚本只出草稿：对照草稿改写后，再手动更新 content/changelog/<产品>.md。

    python3 tools/import_changelog.py kvmini     ~/Documents/Git/KVMini/src-tauri/src/main.rs
    python3 tools/import_changelog.py snipscribe ~/Documents/Git/OnenoteCopy/src-tauri/src/changelog.rs
    加 --dry-run 只打印统计，不写文件

规则（应用内日志是写给开发者自己看的，公开网站只留用户能感知的变化）：
- 剔除含内部术语的条目（Bug 编号、构建脚本、签名、单测、SDK、审核元数据……）
- SnipScribe 只导入 1.0.0 及以后（之前是上架前的内部版本）
- 归类：SnipScribe 看行首 emoji；KVMini 看行首动词
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


def parse_rust(text):
    out = []
    for b in re.findall(r"ChangelogEntry\s*\{(.*?)\n\s*\},", text, re.S):
        v = re.search(r'version:\s*"([^"]+)"', b)
        d = re.search(r'date:\s*"([^"]+)"', b)
        ch = re.search(r"changes:\s*vec!\[(.*?)\]\s*,\s*\n", b, re.S)
        if not (v and d and ch):
            continue
        items = [unescape(x) for x in re.findall(r'"((?:[^"\\]|\\.)*)"\.to_string\(\)', ch.group(1))]
        out.append({"version": v.group(1), "date": d.group(1), "items": items})
    return out


def vkey(v):
    return tuple(int(x) for x in re.findall(r"\d+", v))


def classify(product, item):
    """返回 (分组, 清洗后的文本)；分组为 None 表示剔除，'note' 表示放进版本备注。"""
    text = item.strip()
    m = LEAD_EMOJI.match(text)
    emoji = m.group(1) if m else ""
    text = LEAD_EMOJI.sub("", text)
    text = TAG.sub("", text).strip()
    if "仍在开发中" in text or "请只在可信" in text:
        return "note", text
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


def to_markdown(product, entries):
    lines = []
    kept_versions = dropped = kept = 0
    for e in sorted(entries, key=lambda x: vkey(x["version"]), reverse=True):
        if product == "snipscribe" and vkey(e["version"]) < (1, 0, 0):
            continue
        groups = {"新功能": [], "改进": [], "修复": []}
        notes = []
        for it in e["items"]:
            g, t = classify(product, it)
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
                lines.append("### " + g)
                lines += ["- " + t for t in groups[g]]
        for n in notes:
            lines.append("> 注：" + n)
        lines.append("")
    return "\n".join(lines), {"versions": kept_versions, "kept": kept, "dropped": dropped}


HEADER = "<!-- 草稿：由 tools/import_changelog.py 生成，需人工改写后再并入 content/changelog/ -->\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("product")
    ap.add_argument("source")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dst = os.path.join(root, "drafts", a.product + ".md")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(os.path.expanduser(a.source), encoding="utf-8") as f:
        entries = parse_rust(f.read())
    if not entries:
        print("在 %s 里没找到 ChangelogEntry" % a.source, file=sys.stderr)
        return 1
    body, st = to_markdown(a.product, entries)
    print("%s：源 %d 个版本 → 网站 %d 个版本；保留 %d 条，剔除内部条目 %d 条"
          % (a.product, len(entries), st["versions"], st["kept"], st["dropped"]))
    if not a.dry_run:
        with open(dst, "w", encoding="utf-8") as f:
            f.write(HEADER + "\n" + body)
        print("已写入", dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
