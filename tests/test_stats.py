import datetime
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import build  # noqa: E402
import stats  # noqa: E402

DAY = 86400
TODAY = datetime.date(2026, 10, 20)
T0 = int(datetime.datetime(2026, 10, 20, 12, 0, tzinfo=datetime.timezone.utc).timestamp())


def ev(iid, kind="app_start", ver="0.5.0", os_="macos", ago=0, app="PromptLedger"):
    return {"app": app, "install_id": iid, "kind": kind, "app_version": ver, "os": os_, "ts": T0 - ago * DAY}


class TestLoad(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def write(self, rel, lines):
        p = os.path.join(self.d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def test_reads_all_apps_and_months_skipping_bad_lines(self):
        self.write("PromptLedger/2026-09.jsonl", [json.dumps(ev("a", ago=30))])
        self.write("PromptLedger/2026-10.jsonl", [json.dumps(ev("a")), "not json", "", json.dumps({"app": "x"})])
        self.write("KVMini/2026-10.jsonl", [json.dumps(ev("k", app="KVMini"))])
        self.write("README.md", ["# 不是数据"])
        es = stats.load_events(self.d)
        self.assertEqual(sorted(e["install_id"] for e in es), ["a", "a", "k"])

    def test_missing_dir_gives_empty(self):
        self.assertEqual(stats.load_events(os.path.join(self.d, "nope")), [])

    def test_test_events_are_dropped(self):
        # 接通数据仓时写的 setup_test / append_test 不算真实使用
        self.write("PromptLedger/2026-10.jsonl", [json.dumps(ev("t", kind="setup_test")),
                                                  json.dumps(ev("t", kind="append_test")),
                                                  json.dumps(ev("a"))])
        self.assertEqual([e["install_id"] for e in stats.load_events(self.d)], ["a"])


class TestAggregate(unittest.TestCase):
    def test_counts_devices_and_active_windows(self):
        es = [ev("a"), ev("a", ago=1), ev("b", ago=5), ev("c", ago=20), ev("d", ago=40)]
        app = stats.aggregate(es, TODAY)["apps"][0]
        self.assertEqual(app["name"], "PromptLedger")
        self.assertEqual(app["devices"], 4)
        self.assertEqual(app["active7"], 2)       # a、b
        self.assertEqual(app["active30"], 3)      # a、b、c
        self.assertEqual(app["events"], 5)

    def test_version_distribution_uses_each_devices_latest_version(self):
        es = [ev("a", ver="0.4.0", ago=3), ev("a", ver="0.5.0"), ev("b", ver="0.4.0")]
        app = stats.aggregate(es, TODAY)["apps"][0]
        self.assertEqual(app["versions"], [["0.5.0", 1], ["0.4.0", 1]])

    def test_daily_series_is_unique_devices_per_day_oldest_first(self):
        es = [ev("a"), ev("a"), ev("b"), ev("a", ago=2)]
        daily = stats.aggregate(es, TODAY, days=3)["apps"][0]["daily"]
        self.assertEqual(daily, [["2026-10-18", 1], ["2026-10-19", 0], ["2026-10-20", 2]])

    def test_os_and_kinds(self):
        es = [ev("a", os_="macos"), ev("b", os_="windows"), ev("b", kind="panel_open", os_="windows")]
        app = stats.aggregate(es, TODAY)["apps"][0]
        self.assertEqual(app["os"], [["macos", 1], ["windows", 1]])
        self.assertEqual(app["kinds"], [["app_start", 2], ["panel_open", 1]])

    def test_apps_sorted_by_devices(self):
        es = [ev("a", app="A"), ev("b", app="B"), ev("c", app="B")]
        self.assertEqual([a["name"] for a in stats.aggregate(es, TODAY)["apps"]], ["B", "A"])

    def test_no_install_ids_leak_into_output(self):
        # 统计页是公开的：输出里只能有聚合数字，不能出现任何安装 id
        out = json.dumps(stats.aggregate([ev("secret-id-123")], TODAY))
        self.assertNotIn("secret-id-123", out)


class TestPage(unittest.TestCase):
    def test_build_renders_stats_pages_in_both_languages(self):
        root = os.path.join(os.path.dirname(__file__), "..")
        out = tempfile.mkdtemp()
        try:
            data = tempfile.mkdtemp()
            os.makedirs(os.path.join(data, "PromptLedger"))
            with open(os.path.join(data, "PromptLedger", "2026-10.jsonl"), "w") as f:
                f.write(json.dumps(ev("a")) + "\n")
            os.environ["STATS_DIR"] = data
            build.build(root, out)
            zh = open(os.path.join(out, "stats", "index.html"), encoding="utf-8").read()
            en = open(os.path.join(out, "en", "stats", "index.html"), encoding="utf-8").read()
            self.assertIn("PromptLedger", zh)
            self.assertIn("使用统计", zh)
            self.assertIn("Usage", en)
            home = open(os.path.join(out, "index.html"), encoding="utf-8").read()
            self.assertIn('href="stats/"', home)        # 顶栏有入口
        finally:
            os.environ.pop("STATS_DIR", None)
            shutil.rmtree(out)
            shutil.rmtree(data)

    def test_build_without_data_still_renders_placeholder(self):
        root = os.path.join(os.path.dirname(__file__), "..")
        out = tempfile.mkdtemp()
        try:
            os.environ["STATS_DIR"] = os.path.join(out, "missing")
            build.build(root, out)
            zh = open(os.path.join(out, "stats", "index.html"), encoding="utf-8").read()
            self.assertIn("暂无数据", zh)
        finally:
            os.environ.pop("STATS_DIR", None)
            shutil.rmtree(out)


if __name__ == "__main__":
    unittest.main()
