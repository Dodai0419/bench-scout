import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import bench_scout as bs  # noqa: E402

ENTRIES = bs.load(ROOT / "data" / "benchmarks.json")


class BM25(unittest.TestCase):
    # Cases ported from caveman mem/bm25_test.go
    def test_tokenize(self):
        self.assertEqual(bs.tokenize("Hello, WORLD! foo_bar baz123"), ["hello", "world", "foo", "bar", "baz123"])

    def test_ranked_and_deterministic(self):
        docs = ["alpha beta gamma delta", "alpha alpha beta", "epsilon zeta"]
        s1, s2 = bs.bm25("alpha beta", docs), bs.bm25("alpha beta", docs)
        self.assertEqual(s1, s2)
        self.assertNotIn(2, s1)
        self.assertGreater(s1[0], 0)
        self.assertGreater(s1[1], s1[0])

    def test_empty(self):
        self.assertEqual(bs.bm25("", ["alpha"]), {})
        self.assertEqual(bs.bm25("alpha", []), {})
        self.assertEqual(bs.bm25("the of", ["the of alpha"]), {})  # stopwords only


class SiteParity(unittest.TestCase):
    """--exact must return what the upstream website shows, in the same order."""

    def test_same_as_upstream_site(self):
        cases = json.loads((ROOT / "tests" / "fixtures" / "site_parity.json").read_text(encoding="utf-8"))
        for c in cases:
            f = c["case"]
            got = bs.site_filter(ENTRIES, f.get("q", ""), f.get("types"), f.get("levels"), f.get("years"), f.get("flags"))
            self.assertEqual([e["slug"] for e in got], c["slugs"], f)


class Stats(unittest.TestCase):
    def test_matches_upstream_readme(self):
        s = bs.stats(ENTRIES)
        self.assertEqual(s["entries"], 207)
        self.assertEqual(s["levels"], {"unverified": 0, "paper_only": 37, "data_public": 31, "official_script": 139,
                                       "smoke_tested": 0, "full_run": 0})
        self.assertEqual(s["types"]["conversational_longterm"], 81)
        self.assertEqual(s["types"]["coding_cross_session"], 17)
        self.assertEqual(s["types"]["memory_security"], 18)


class Find(unittest.TestCase):
    def test_bm25_finds_without_exact_words(self):
        top = [e["slug"] for e in bs.find(ENTRIES, "coding agent memory across sessions", top=5)]
        self.assertTrue(any(bs.by_slug(ENTRIES, s)["memory_types"].count("coding_cross_session") for s in top), top)

    def test_filters_apply_to_ranking(self):
        hits = bs.find(ENTRIES, "memory poisoning attack", types=["memory_security"], top=50)
        self.assertTrue(hits)
        self.assertTrue(all("memory_security" in e["memory_types"] for e in hits))

    def test_cli_runs(self):
        out = subprocess.run([sys.executable, str(ROOT / "bench_scout.py"), "find", "memory poisoning attack", "--top", "3"],
                             capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(len(out.stdout.strip().splitlines()), 3)


if __name__ == "__main__":
    unittest.main()
