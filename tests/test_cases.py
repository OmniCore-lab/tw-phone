"""Every case in cases.json must come out the same. Run: python -m unittest discover tests"""
import json, os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))
import tw_phone

CASES = json.load(open(os.path.join(ROOT, "cases.json"), encoding="utf-8"))


class Cases(unittest.TestCase):
    def test_classify(self):
        for c in CASES["classify"]:
            with self.subTest(v=c["v"]):
                self.assertEqual(tw_phone.classify(c["v"]), c["kind"])

    def test_phone_ok(self):
        for c in CASES["phone_ok"]:
            with self.subTest(t=c["t"]):
                self.assertEqual(tw_phone.phone_ok(c["t"], c["s"], c["e"]), c["ok"])


if __name__ == "__main__":
    unittest.main()
