import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLICY = os.path.join(ROOT, "content", "static", "policy.json")
FORBIDDEN = ["¥", "付费", "解锁", "订单", "价格"]


class PolicyTest(unittest.TestCase):
    def setUp(self):
        with open(POLICY, encoding="utf-8") as f:
            self.p = json.load(f)

    def test_schema_and_free_defaults(self):
        self.assertEqual(self.p["schema"], 1)
        self.assertEqual(self.p["pricing"]["mode"], "free")
        self.assertFalse(self.p["force"]["enabled"])
        self.assertEqual(self.p["block"]["belowVersion"], "")
        self.assertEqual(self.p["force"]["graceDays"], 0)

    def test_shape_matches_internal_policy(self):
        self.assertEqual(sorted(self.p["force"]), ["enabled", "graceDays", "minVersion", "notes"])
        self.assertEqual(sorted(self.p["force"]["notes"]), ["en", "zh"])
        self.assertEqual(sorted(self.p["pricing"]), ["effectiveFrom", "mode", "notice"])

    def test_no_paid_words(self):
        raw = open(POLICY, encoding="utf-8").read()
        for w in FORBIDDEN:
            self.assertNotIn(w, raw)


if __name__ == "__main__":
    unittest.main()
