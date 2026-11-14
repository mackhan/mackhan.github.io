import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDS = ["kvmini", "snipscribe", "moviebox", "tupu", "idphoto", "lifetree", "promptledger"]
FORBIDDEN = ["¥", "付费", "解锁", "订单", "价格"]


class ProductPolicyTest(unittest.TestCase):
    def test_every_product_has_its_own_policy(self):
        for pid in IDS:
            path = os.path.join(ROOT, "content", "static", "policy", pid + ".json")
            self.assertTrue(os.path.exists(path), "缺少 " + pid + ".json")
            raw = open(path, encoding="utf-8").read()
            d = json.loads(raw)
            self.assertEqual(d["product"], pid)
            self.assertIsInstance(d["revision"], int)
            self.assertEqual(d["policy"]["pricing"]["mode"], "free")
            self.assertFalse(d["policy"]["force"]["enabled"])
            self.assertRegex(d["policy"]["updatedAt"], r"^\d{4}-\d{2}-\d{2}$")
            for w in FORBIDDEN:
                self.assertNotIn(w, raw)

    def test_legacy_single_policy_still_exists(self):
        path = os.path.join(ROOT, "content", "static", "policy.json")
        self.assertTrue(os.path.exists(path))


if __name__ == "__main__":
    unittest.main()
