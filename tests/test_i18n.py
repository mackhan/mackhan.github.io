"""多语言（中文 / English）：英文页面、语言切换、hreflang、英文更新日志与中文版本对齐"""
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import build  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CJK = re.compile(r"[\u3400-\u9fff\uff00-\uffef\u3000-\u303f]")

ZH = """## v1.1.0 · 2026-10-06
### 新功能
- 静音时段
> 注：升级后需重新激活

## v1.0.0 · 2026-09-01
### 修复
- 更快
"""
EN = """## v1.1.0 · 2026-10-06
### New
- Quiet hours
> Note: re-activate after updating

## v1.0.0 · 2026-09-01
### Fixed
- Faster
"""


def read(*p):
    with open(os.path.join(*p), encoding="utf-8") as f:
        return f.read()


class TestI18nBuild(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(self.tmp, "assets"))
        os.makedirs(os.path.join(self.tmp, "content", "changelog", "en"))
        site = {
            "brand": "TEST", "site_version": "9.9.9", "base_url": "https://example.github.io/",
            "lead": "中文简介", "lead_en": "English lead", "repo_url": "https://github.com/x/y",
            "products": [
                {"id": "a", "name": "阿尔法", "name_en": "Alpha", "desc": "中文描述", "desc_en": "English desc",
                 "color": "#fff", "platforms": ["macOS"], "note": "中文备注", "note_en": "English note",
                 "downloads": [{"label": "下载", "label_en": "Download", "url": "https://dl.example.com/a"},
                               {"label": "安卓", "label_en": "Android", "url": ""}],
                 "links": [{"label": "隐私政策", "label_en": "Privacy", "url": "/a/privacy/"}]},
                {"id": "b", "name": "Beta", "desc": "只有中文", "color": "#000", "platforms": ["Windows"],
                 "downloads": []},
            ],
        }
        with open(os.path.join(self.tmp, "site.json"), "w", encoding="utf-8") as f:
            json.dump(site, f, ensure_ascii=False)
        self.write("a.md", ZH)
        self.write("en/a.md", EN)
        self.write("b.md", "## v2.0.0 · 2026-08-01\n### 修复\n- 仅有中文的条目\n")   # b 没有英文版 → 回落中文并标注

    def write(self, rel, s):
        with open(os.path.join(self.tmp, "content", "changelog", rel), "w", encoding="utf-8") as f:
            f.write(s)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_english_pages_exist_with_lang_attribute(self):
        out = build.build(self.tmp)
        for rel in ("en/index.html", "en/changelog/index.html"):
            page = read(out, rel)
            self.assertIn('<html lang="en">', page, rel)
        self.assertIn('<html lang="zh-CN">', read(out, "index.html"))

    def test_english_home_uses_english_texts(self):
        out = build.build(self.tmp)
        home = read(out, "en", "index.html")
        for s in ("English lead", "Alpha", "English desc", "English note", "Download", "Privacy",
                  "Android · Coming soon", "Oct 6, 2026"):
            self.assertIn(s, home)
        for s in ("中文简介", "阿尔法", "即将提供", "更新日志"):
            self.assertNotIn(s, home)

    def test_english_changelog_uses_english_entries_and_dates(self):
        out = build.build(self.tmp)
        cl = read(out, "en", "changelog", "index.html")
        self.assertIn("Quiet hours", cl)
        self.assertIn("Note: re-activate after updating", cl)
        self.assertIn("Sep 1, 2026", cl)
        self.assertNotIn("静音时段", cl)
        # 没有英文版的产品：回落中文条目并说明
        self.assertIn("Release notes for Beta are only available in Chinese", cl)
        self.assertIn("仅有中文的条目", cl)

    def test_language_switch_and_hreflang(self):
        out = build.build(self.tmp)
        zh = read(out, "changelog", "index.html")
        en = read(out, "en", "changelog", "index.html")
        self.assertIn('hreflang="en" href="https://example.github.io/en/changelog/"', zh)
        self.assertIn('hreflang="zh-CN" href="https://example.github.io/changelog/"', en)
        self.assertIn('hreflang="x-default" href="https://example.github.io/changelog/"', en)
        self.assertRegex(zh, r'<a[^>]*data-lang="en"[^>]*href="\.\./en/changelog/"')
        self.assertRegex(en, r'<a[^>]*data-lang="zh"[^>]*href="\.\./\.\./changelog/"')

    def test_chinese_pages_suggest_english_for_non_chinese_browsers(self):
        """中文页：浏览器语言不是中文、且用户没手动选过语言时跳到英文页"""
        out = build.build(self.tmp)
        zh = read(out, "index.html")
        self.assertIn("navigator.language", zh)
        self.assertIn("siteLang", zh)
        self.assertNotIn("navigator.language", read(out, "en", "index.html"))

    def test_english_changelog_must_cover_every_chinese_version(self):
        self.write("en/a.md", EN.split("## v1.0.0")[0])
        with self.assertRaises(build.ChangelogError) as e:
            build.build(self.tmp)
        self.assertIn("1.0.0", str(e.exception))

    def test_english_changelog_dates_must_match(self):
        self.write("en/a.md", EN.replace("2026-09-01", "2026-09-02"))
        with self.assertRaises(build.ChangelogError):
            build.build(self.tmp)

    def test_english_note_prefix_is_stripped(self):
        r = build.parse_changelog(EN, "a")[0]
        self.assertEqual(r["note"], "re-activate after updating")

    def test_404_is_bilingual(self):
        out = build.build(self.tmp)
        nf = read(out, "404.html")
        self.assertIn("页面不存在", nf)
        self.assertIn("Page not found", nf)


class TestRealContentI18n(unittest.TestCase):
    """仓库里的真实内容：每个产品都有英文更新日志，英文页面不含中文"""

    def setUp(self):
        self.out = tempfile.mkdtemp()
        self.dist = build.build(ROOT, os.path.join(self.out, "dist"))

    def tearDown(self):
        shutil.rmtree(self.out)

    def test_every_product_has_an_english_changelog(self):
        site = json.loads(read(ROOT, "site.json"))
        for p in site["products"]:
            self.assertTrue(os.path.isfile(os.path.join(ROOT, "content", "changelog", "en", p["id"] + ".md")), p["id"])

    def test_english_pages_contain_no_chinese(self):
        for rel in (("en", "index.html"), ("en", "changelog", "index.html")):
            text = re.sub(r"<[^>]+>", " ", read(self.dist, *rel))
            text = text.replace("中文", "")   # 语言切换按钮本身
            found = CJK.findall(text)
            self.assertEqual(found, [], "/".join(rel) + " 含中文：" + "".join(found[:40]))


if __name__ == "__main__":
    unittest.main()
