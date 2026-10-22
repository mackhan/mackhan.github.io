"""tools/sync_product.py：把产品清单同步到 site.json 与中英更新日志。

只测「写文件的结果」，不联网（清单用 dict 直接传）。
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import sync_product as S  # noqa: E402


@contextlib.contextmanager
def quiet():
    """脚本会 print 进度，测试里吃掉"""
    with contextlib.redirect_stdout(io.StringIO()):
        yield

HEADER = "<!-- 说明注释：加在最上面 -->\n"
OLD = "## v0.3.4 · 2026-10-14\n### 改进\n- 老条目\n"


def entry(version, date, title="改进", items=None):
    return {
        "version": version,
        "date": date,
        "groups": [{"title": title, "items": items or ["- %s 的条目" % version]}],
    }


class SyncChangelogTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = os.path.join(self.tmp, "site")
        os.makedirs(os.path.join(self.root, "content", "changelog", "en"))
        self.old_root = S.ROOT
        S.ROOT = self.root
        self.path = os.path.join(self.root, "content", "changelog", "demo.md")
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(HEADER + "\n" + OLD)

    def tearDown(self):
        S.ROOT = self.old_root
        shutil.rmtree(self.tmp, ignore_errors=True)

    def read(self):
        with open(self.path, encoding="utf-8") as f:
            return f.read()

    def versions(self):
        import re
        return re.findall(r"^##\s*v?([\d.]+)", self.read(), re.M)

    def test_new_versions_go_above_older_ones(self):
        m = {"changelog": [entry("0.4.1", "2026-10-22"), entry("0.4.0", "2026-10-20")]}
        with quiet():
            S.sync_changelog("demo", m, "changelog", "zh")
        self.assertEqual(self.versions(), ["0.4.1", "0.4.0", "0.3.4"])

    def test_header_comment_stays_on_top(self):
        m = {"changelog": [entry("0.4.0", "2026-10-20")]}
        with quiet():
            S.sync_changelog("demo", m, "changelog", "zh")
        self.assertTrue(self.read().startswith(HEADER))

    def test_older_versions_skipped_by_default(self):
        m = {"changelog": [entry("0.2.0", "2026-09-01")]}
        with quiet():
            S.sync_changelog("demo", m, "changelog", "zh")
        self.assertEqual(self.versions(), ["0.3.4"])

    def test_backfill_adds_older_versions(self):
        m = {"changelog": [entry("0.2.0", "2026-09-01")]}
        with quiet():
            S.sync_changelog("demo", m, "changelog", "zh", backfill=True)
        self.assertEqual(self.versions(), ["0.3.4", "0.2.0"])

    def test_check_does_not_write(self):
        m = {"changelog": [entry("0.4.0", "2026-10-20")]}
        with quiet():
            changed = S.sync_changelog("demo", m, "changelog", "zh", dry=True)
        self.assertTrue(changed)
        self.assertEqual(self.versions(), ["0.3.4"])

    def test_running_twice_changes_nothing(self):
        """发布脚本会连着跑，第二次必须是 no-op"""
        m = {"changelog": [entry("0.4.0", "2026-10-20")]}
        with quiet():
            S.sync_changelog("demo", m, "changelog", "zh")
        first = self.read()
        with quiet():
            changed = S.sync_changelog("demo", m, "changelog", "zh")
        self.assertFalse(changed)
        self.assertEqual(self.read(), first)

    def test_short_and_long_version_count_as_one(self):
        """lifetree.md 里同时有 v1.0 与 v1.0.0，不能插出两份"""
        m = {"changelog": [entry("1.0", "2026-10-16")]}
        with quiet():
            S.sync_changelog("demo", m, "changelog", "zh", backfill=True)
        with quiet():
            S.sync_changelog("demo", {"changelog": [entry("1.0.0", "2026-10-19")]},
                             "changelog", "zh", backfill=True)
        self.assertEqual(self.versions(), ["1.0", "0.3.4"])

    def test_missing_file_exits_instead_of_crashing(self):
        os.remove(self.path)
        with quiet():
            with self.assertRaises(SystemExit):
                S.sync_changelog("demo", {"changelog": [entry("0.4.0", "2026-10-20")]},
                                 "changelog", "zh")

    def test_missing_english_is_skipped(self):
        with quiet():
            changed = S.sync_changelog("demo", {}, "changelog_en", "en")
        self.assertFalse(changed)


class SiteJsonTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = os.path.join(self.tmp, "site")
        os.makedirs(self.root)
        self.old_root = S.ROOT
        S.ROOT = self.root
        with open(os.path.join(self.root, "site.json"), "w", encoding="utf-8") as f:
            json.dump({"products": [{"id": "demo", "name": "Demo"}]}, f, ensure_ascii=False)
        self.url = "https://example.com/manifest.json"

    def tearDown(self):
        S.ROOT = self.old_root
        shutil.rmtree(self.tmp, ignore_errors=True)

    def prod(self):
        with open(os.path.join(self.root, "site.json"), encoding="utf-8") as f:
            return json.load(f)["products"][0]

    def test_downloads_keep_english_labels(self):
        m = {"downloads": [{"label": "安装包", "label_en": "Installer", "url": "https://x/y"}]}
        with quiet():
            S.sync_site_json("demo", m, self.url)
        self.assertEqual(self.prod()["downloads"], m["downloads"])

    def test_local_manifest_path_is_not_published(self):
        m = {"platforms": ["macOS"]}
        with quiet():
            S.sync_site_json("demo", m, "/Users/me/demo/pages/manifest.json", local=True)
        self.assertIsNone(self.prod().get("manifest"))

    def test_missing_label_en_is_not_written_as_null(self):
        """null 会让英文页回落中文标签，i18n 测试直接失败"""
        m = {"downloads": [{"label": "安装包", "url": "https://x/y"}]}
        with quiet():
            S.sync_site_json("demo", m, self.url)
        self.assertNotIn("label_en", self.prod()["downloads"][0])

    def test_url_manifest_is_recorded(self):
        with quiet():
            S.sync_site_json("demo", {"platforms": ["macOS"]}, self.url)
        self.assertEqual(self.prod()["manifest"], self.url)


if __name__ == "__main__":
    unittest.main()


class VkeyTest(unittest.TestCase):
    """版本号比较口径必须与 build.py 一致"""

    def test_short_and_long_version_are_equal(self):
        self.assertEqual(S.vkey("1.0"), S.vkey("1.0.0"))

    def test_prerelease_suffix_ignored(self):
        self.assertEqual(S.vkey("1.2.0-beta.1"), S.vkey("1.2.0"))

    def test_numeric_not_lexicographic(self):
        self.assertGreater(S.vkey("0.4.10"), S.vkey("0.4.9"))
