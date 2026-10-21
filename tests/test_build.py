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

    def test_mobile_viewer_published_as_is(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        shutil.copytree(os.path.join(root, "pa"), os.path.join(self.tmp, "pa"))
        out = build.build(self.tmp)
        for f in ("index.html", "app.js", "sw.js", "style.css", "manifest.webmanifest", "icons/icon-192.png"):
            self.assertTrue(os.path.isfile(os.path.join(out, "pa", f)), f)
        html_ = open(os.path.join(out, "pa", "index.html"), encoding="utf-8").read()
        self.assertIn("connect-src https://api.github.com", html_)   # 只允许连 GitHub API
        self.assertIn('name="referrer" content="no-referrer"', html_)
        app = open(os.path.join(out, "pa", "app.js"), encoding="utf-8").read()
        self.assertNotIn("innerHTML = r", app)                         # 提示词不经 innerHTML

    def test_unknown_changelog_file_is_error(self):
        open(os.path.join(self.tmp, "content", "changelog", "zzz.md"), "w").write("")
        with self.assertRaises(build.ChangelogError):
            build.build(self.tmp)

    def test_static_pages_published_at_their_path(self):
        """content/static/ 原样发布：应用内“隐私政策”指向 /KVMini/privacy-policy，此前 404"""
        d = os.path.join(self.tmp, "content", "static", "KVMini", "privacy-policy")
        os.makedirs(d)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write("<html>privacy</html>")
        out = build.build(self.tmp)
        self.assertEqual(open(os.path.join(out, "KVMini", "privacy-policy", "index.html"), encoding="utf-8").read(),
                         "<html>privacy</html>")

    def test_static_pages_cannot_overwrite_generated_ones(self):
        d = os.path.join(self.tmp, "content", "static", "changelog")
        os.makedirs(d)
        open(os.path.join(d, "index.html"), "w").write("x")
        with self.assertRaises(build.ChangelogError):
            build.build(self.tmp)

    def test_product_links_rendered(self):
        """产品卡片可以带额外链接（隐私政策 / 源码等）"""
        site = json.load(open(os.path.join(self.tmp, "site.json"), encoding="utf-8"))
        site["products"][0]["links"] = [{"label": "隐私政策", "url": "/KVMini/privacy-policy/"}]
        json.dump(site, open(os.path.join(self.tmp, "site.json"), "w", encoding="utf-8"), ensure_ascii=False)
        out = build.build(self.tmp)
        home = open(os.path.join(out, "index.html"), encoding="utf-8").read()
        self.assertIn('href="/KVMini/privacy-policy/"', home)
        self.assertIn("隐私政策", home)

    def _add_links(self, links):
        site = json.load(open(os.path.join(self.tmp, "site.json"), encoding="utf-8"))
        site["products"][0]["links"] = links
        json.dump(site, open(os.path.join(self.tmp, "site.json"), "w", encoding="utf-8"), ensure_ascii=False)

    def test_product_page_generated_per_language(self):
        """没有独立站点的产品，每个语言都生成一页；页里只列本产品的更新日志"""
        self._add_links([{"label": "项目主页", "url": "/a/"},
                         {"label": "更新日志", "url": "/changelog/?p=a"},
                         {"label": "隐私政策", "url": "/a/privacy-policy/"}])
        out = build.build(self.tmp)
        for rel in ("a/index.html", "en/a/index.html", "b/index.html"):
            self.assertTrue(os.path.isfile(os.path.join(out, rel)), rel)
        zh = open(os.path.join(out, "a", "index.html"), encoding="utf-8").read()
        self.assertIn("Alpha", zh)
        self.assertIn('id="a-v1.2.0"', zh)          # 本产品的版本
        self.assertNotIn('id="b-v', zh)             # 不该出现别的产品
        self.assertIn('href="../changelog/?p=a"', zh)
        self.assertIn('href="/a/privacy-policy/"', zh)   # 静态隐私页只有一份，保持绝对链接
        en = open(os.path.join(out, "en", "a", "index.html"), encoding="utf-8").read()
        self.assertIn('href="../../changelog/?p=a"', en)   # 英文页不能跳回中文更新日志

    def test_product_page_for_unreleased_product(self):
        """没发布过的产品：显示「尚未发布」和空状态，下载地址为空时显示「即将提供」"""
        self._add_links([])
        site = json.load(open(os.path.join(self.tmp, "site.json"), encoding="utf-8"))
        site["products"][0]["downloads"] = [{"label": "macOS", "url": ""}]
        json.dump(site, open(os.path.join(self.tmp, "site.json"), "w", encoding="utf-8"), ensure_ascii=False)
        out = build.build(self.tmp)
        a = open(os.path.join(out, "a", "index.html"), encoding="utf-8").read()
        self.assertIn("即将提供", a)
        b = open(os.path.join(out, "b", "index.html"), encoding="utf-8").read()
        self.assertIn("尚未发布", b)
        self.assertIn("还没有发布记录。", b)

    def test_product_with_own_site_has_no_generated_page(self):
        """有 site 字段的产品用自己的独立站点，本站不再重复生成一页"""
        site = json.load(open(os.path.join(self.tmp, "site.json"), encoding="utf-8"))
        site["products"][0]["site"] = "https://example.com/alpha/"
        json.dump(site, open(os.path.join(self.tmp, "site.json"), "w", encoding="utf-8"), ensure_ascii=False)
        out = build.build(self.tmp)
        self.assertFalse(os.path.exists(os.path.join(out, "a", "index.html")))
        home = open(os.path.join(out, "index.html"), encoding="utf-8").read()
        self.assertIn('href="https://example.com/alpha/"', home)

    def test_page_field_overrides_directory_name(self):
        """page 字段让落地页目录跟已有的隐私政策目录对齐（大小写也要一致）"""
        site = json.load(open(os.path.join(self.tmp, "site.json"), encoding="utf-8"))
        site["products"][0]["page"] = "Alpha"
        json.dump(site, open(os.path.join(self.tmp, "site.json"), "w", encoding="utf-8"), ensure_ascii=False)
        out = build.build(self.tmp)
        self.assertTrue(os.path.isfile(os.path.join(out, "Alpha", "index.html")))
        self.assertIn('href="Alpha/"', open(os.path.join(out, "index.html"), encoding="utf-8").read())

    def test_static_index_html_cannot_shadow_product_page(self):
        d = os.path.join(self.tmp, "content", "static", "a")
        os.makedirs(d)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write("x")
        with self.assertRaises(build.ChangelogError):
            build.build(self.tmp)


class RealContentTest(unittest.TestCase):
    """仓库里的真实内容：KVMini 必须有可用下载、有效的隐私政策页、更新日志不落后"""

    def setUp(self):
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.out = tempfile.mkdtemp()
        build.build(self.root, os.path.join(self.out, "dist"))
        self.dist = os.path.join(self.out, "dist")

    def tearDown(self):
        shutil.rmtree(self.out)

    def test_kvmini_has_real_downloads_and_privacy_page(self):
        site = json.load(open(os.path.join(self.root, "site.json"), encoding="utf-8"))
        kv = next(p for p in site["products"] if p["id"] == "kvmini")
        urls = [d["url"] for d in kv["downloads"]]
        self.assertTrue(all(urls), "KVMini 下载地址不能为空（会显示“即将提供”）")
        self.assertTrue(all(u.startswith("https://github.com/mackhan/KVMini/releases/") for u in urls))
        page = os.path.join(self.dist, "KVMini", "privacy-policy", "index.html")
        self.assertTrue(os.path.isfile(page), "应用内隐私政策链接指向这里")
        self.assertIn("KVMini", open(page, encoding="utf-8").read())

    def test_every_product_links_to_home_privacy_and_changelog(self):
        """每个产品都要有「项目主页 / 隐私政策 / 更新日志」三件套，链到的页面必须真的存在"""
        site = json.load(open(os.path.join(self.root, "site.json"), encoding="utf-8"))
        self.assertEqual(len(site["products"]), 6)
        for p in site["products"]:
            links = {l["label"]: l["url"] for l in p.get("links", [])}
            self.assertEqual({"项目主页", "隐私政策", "更新日志"} - set(links), set(),
                             "%s 缺少链接，现有：%s" % (p["id"], sorted(links)))
            for label in ("项目主页", "隐私政策"):
                url = links[label]
                if url.startswith("/"):        # 外部站点（MovieBox）不检查
                    f = os.path.join(self.dist, url.lstrip("/"), "index.html")
                    self.assertTrue(os.path.isfile(f), "%s 的「%s」指向 %s，但文件不存在" % (p["id"], label, url))
            if links["更新日志"].startswith("/"):
                self.assertIn("?p=%s" % p["id"], links["更新日志"])

    def test_product_pages_render_for_every_product_without_own_site(self):
        """没有独立站点的产品，本站每个语言都要有一页落地页"""
        site = json.load(open(os.path.join(self.root, "site.json"), encoding="utf-8"))
        for p in site["products"]:
            if p.get("site"):
                continue
            d = build.page_dir(p)
            for root in ("", "en"):
                f = os.path.join(self.dist, root, d, "index.html")
                self.assertTrue(os.path.isfile(f), f)
            zh = open(os.path.join(self.dist, d, "index.html"), encoding="utf-8").read()
            self.assertIn(build.tr(p, "name", "zh"), zh)
            self.assertIn("id=\"%s-v" % p["id"], zh)

    def test_kvmini_latest_release_no_longer_claims_plaintext(self):
        data = json.load(open(os.path.join(self.dist, "updates", "kvmini", "changelog.json"), encoding="utf-8"))
        self.assertNotIn("明文", data["releases"][0]["note"])
        self.assertGreaterEqual(build.vkey(data["latest"]), (0, 3, 4))


if __name__ == "__main__":
    unittest.main()
