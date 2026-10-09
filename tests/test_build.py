import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import build  # noqa: E402

SAMPLE = """<!-- 注释会被忽略 -->
## v1.2.0 · 2026-10-06 · 授权修复
### 新功能
- **静音时段**：夜里不响
- 支持 `brew` 安装，见 [文档](https://example.com)
### 修复
- 修复 <script> 注入
> 注：升级后需重新激活

## 1.1.0 · 2026-09-01
### 改进
- 更快
"""


class TestParse(unittest.TestCase):
    def test_basic_structure(self):
        rs = build.parse_changelog(SAMPLE, "demo")
        self.assertEqual([r["version"] for r in rs], ["1.2.0", "1.1.0"])
        r = rs[0]
        self.assertEqual(r["date"], "2026-10-06")
        self.assertEqual(r["flag"], "授权修复")
        self.assertEqual([g["title"] for g in r["groups"]], ["新功能", "修复"])
        self.assertEqual(r["note"], "升级后需重新激活")
        self.assertEqual(rs[1]["flag"], "")

    def test_inline_markdown_and_escaping(self):
        items = build.parse_changelog(SAMPLE, "demo")[0]["groups"]
        html_new = items[0]["items_html"]
        self.assertIn("<strong>静音时段</strong>", html_new[0])
        self.assertIn("<code>brew</code>", html_new[1])
        self.assertIn('<a href="https://example.com"', html_new[1])
        self.assertIn("&lt;script&gt;", items[1]["items_html"][0])
        self.assertNotIn("<script>", items[1]["items_html"][0])

    def test_plain_text_kept_for_json(self):
        g = build.parse_changelog(SAMPLE, "demo")[0]["groups"][0]
        self.assertEqual(g["items"][0], "**静音时段**：夜里不响")

    def test_errors_have_line_numbers(self):
        with self.assertRaises(build.ChangelogError) as e:
            build.parse_changelog("## v1.0 · 2026/10/06\n", "demo")
        self.assertIn("demo.md:1", str(e.exception))
        with self.assertRaises(build.ChangelogError) as e:
            build.parse_changelog("## v1.0 · 2026-10-06\n- 没有分类\n", "demo")
        self.assertIn("demo.md:2", str(e.exception))
        with self.assertRaises(build.ChangelogError):
            build.parse_changelog("## v1.0 · 2026-10-06\n## v1.0 · 2026-10-07\n### 修复\n- x\n", "demo")

    def test_empty_file_means_no_release(self):
        self.assertEqual(build.parse_changelog("<!-- 只有说明 -->\n\n", "demo"), [])

    def test_unsafe_link_rejected(self):
        g = build.parse_changelog("## 1.0 · 2026-10-06\n### 修复\n- [x](javascript:alert(1))\n", "d")[0]["groups"][0]
        self.assertNotIn("javascript:", g["items_html"][0])

    def test_cn_date(self):
        self.assertEqual(build.cn_date("2026-10-06"), "2026年10月6日")


class TestBuild(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        root = os.path.join(os.path.dirname(__file__), "..")
        for name in ("assets",):
            shutil.copytree(os.path.join(root, name), os.path.join(self.tmp, name))
        os.makedirs(os.path.join(self.tmp, "content", "changelog"))
        site = {
            "brand": "TEST", "site_version": "9.9.9", "lead": "x", "repo_url": "https://github.com/x/y",
            "products": [
                {"id": "a", "name": "Alpha", "desc": "d", "color": "#fff", "platforms": ["macOS"],
                 "downloads": [{"label": "macOS", "url": ""}]},
                {"id": "b", "name": "Beta", "desc": "d", "color": "#000", "platforms": ["Windows"],
                 "downloads": [{"label": "Windows", "url": "https://dl.example.com/b.exe"}]},
            ],
        }
        with open(os.path.join(self.tmp, "site.json"), "w", encoding="utf-8") as f:
            json.dump(site, f, ensure_ascii=False)
        with open(os.path.join(self.tmp, "content", "changelog", "a.md"), "w", encoding="utf-8") as f:
            f.write(SAMPLE)
        with open(os.path.join(self.tmp, "content", "changelog", "b.md"), "w", encoding="utf-8") as f:
            f.write("<!-- 还没发布 -->\n")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_outputs(self):
        out = build.build(self.tmp)
        for rel in ("index.html", "changelog/index.html", "404.html", ".nojekyll",
                    "updates/a/changelog.json", "updates/b/changelog.json", "updates/all.json",
                    "assets/site.css"):
            self.assertTrue(os.path.exists(os.path.join(out, rel)), rel)
        page = open(os.path.join(out, "changelog", "index.html"), encoding="utf-8").read()
        self.assertIn('id="a-v1.2.0"', page)
        self.assertIn("9.9.9", page)                       # 站点版本号必须显示
        self.assertIn("2026年10月6日", page)
        home = open(os.path.join(out, "index.html"), encoding="utf-8").read()
        self.assertIn("尚未发布", home)                     # Beta 没有发布记录
        self.assertIn("即将提供", home)                     # Alpha 下载地址为空
        self.assertIn("https://dl.example.com/b.exe", home)
        data = json.load(open(os.path.join(out, "updates", "a", "changelog.json"), encoding="utf-8"))
        self.assertEqual(data["latest"], "1.2.0")
        self.assertEqual(data["releases"][0]["groups"][0]["items"][0], "**静音时段**：夜里不响")
        self.assertEqual(json.load(open(os.path.join(out, "updates", "b", "changelog.json")))["latest"], None)

    def test_unknown_changelog_file_is_error(self):
        open(os.path.join(self.tmp, "content", "changelog", "zzz.md"), "w").write("")
        with self.assertRaises(build.ChangelogError):
            build.build(self.tmp)


if __name__ == "__main__":
    unittest.main()
