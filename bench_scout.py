#!/usr/bin/env python3
"""bench-scout: find the agent-memory benchmark that fits your system, offline, in one command.

Data: the memory-bench-registry snapshot (CC BY 4.0, Fengzdadi) in data/benchmarks.json.
Ranking: BM25 as in caveman's cavemem recall (k1=1.5, b=0.75, +1-smoothed IDF, same stopwords).

  python bench_scout.py find "coding agent memory across sessions" --top 5
  python bench_scout.py find locomo --exact          # same rows, same order as the registry website
  python bench_scout.py show locomo-conv             # every field with its source
  python bench_scout.py stats
  python bench_scout.py update                       # refresh the snapshot from the registry site
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data" / "benchmarks.json"
SOURCE_URL = "https://fengzdadi.github.io/memory-bench-registry/benchmarks.json"
LEVELS = ["unverified", "paper_only", "data_public", "official_script", "smoke_tested", "full_run"]
TYPES = ["conversational_longterm", "personalization", "episodic", "semantic_knowledge_update", "procedural_workflow",
         "coding_cross_session", "parametric", "multi_agent_group", "multimodal", "embodied", "memory_security"]
FLAGS = {
    "code": lambda e: bool(e["links"]["code"]),
    "data": lambda e: bool(e["links"]["data"]),
    "judge": lambda e: bool(e["judge_model"]),
    "peer": lambda e: bool(e["venue"]) and e["venue"] != "arXiv preprint",
}
K1, B = 1.5, 0.75
STOPWORDS = set("a an and are as at be by for from how in is it of on or that the this to was what when where which "
                "who why with".split())


def load(path: Path = DATA) -> list[dict]:
    entries = json.loads(path.read_text(encoding="utf-8"))
    for e in entries:  # same haystack the registry website searches
        e["_year"] = e["release_date"][:4] if e["release_date"] else "undated"
        e["_hay"] = "\n".join(filter(None, [e["name"], e["slug"], e["venue"], " ".join(e["memory_types"]),
                                            " ".join(e["metrics"]), e["judge_model"], e["notes"], e["scale"]["notes"],
                                            e["scale"]["avg_context_length"]])).lower()
    return entries


def tokenize(s: str) -> list[str]:
    return re.findall(r"[^\W_]+", s.lower())


def bm25(query: str, docs: list[str]) -> dict[int, float]:
    """doc index -> score, only for docs sharing a query term."""
    q = {t for t in tokenize(query) if t not in STOPWORDS}
    if not q or not docs:
        return {}
    tfs = [Counter(t for t in tokenize(d) if t not in STOPWORDS) for d in docs]
    n, avgdl = len(docs), sum(sum(tf.values()) for tf in tfs) / len(docs)
    if avgdl == 0:
        return {}
    idf = {t: math.log(1 + (n - df + 0.5) / (df + 0.5)) for t in q for df in [sum(t in tf for tf in tfs)]}
    out = {}
    for i, tf in enumerate(tfs):
        dl = sum(tf.values())
        s = sum(idf[t] * tf[t] * (K1 + 1) / (tf[t] + K1 * (1 - B + B * dl / avgdl)) for t in q if tf[t])
        if s > 0:
            out[i] = s
    return out


def facets(e: dict, types, levels, years, flags) -> bool:
    return ((not types or any(t in types for t in e["memory_types"])) and (not levels or e["repro_level"] in levels)
            and (not years or e["_year"] in years) and all(FLAGS[f](e) for f in flags or []))


def site_filter(entries, q="", types=None, levels=None, years=None, flags=None) -> list[dict]:
    """The registry website's search: every word is a substring, newest first, name hits first."""
    toks = q.lower().split()
    rows = [e for e in entries if all(t in e["_hay"] for t in toks) and facets(e, types, levels, years, flags)]
    rows.sort(key=lambda e: e["name"].casefold())
    rows.sort(key=lambda e: e["release_date"] or "", reverse=True)  # stable: ties keep name order, undated last
    return [e for e in rows if all(t in e["name"].lower() for t in toks)] + \
           [e for e in rows if not all(t in e["name"].lower() for t in toks)] if toks else rows


def find(entries, q, types=None, levels=None, years=None, flags=None, top=10) -> list[dict]:
    pool = [e for e in entries if facets(e, types, levels, years, flags)]
    scores = bm25(q, [e["_hay"] for e in pool])
    return [pool[i] for i in sorted(scores, key=lambda i: (-scores[i], pool[i]["name"].casefold()))][:top]


def by_slug(entries, slug):
    return next((e for e in entries if e["slug"] == slug), None)


def stats(entries) -> dict:
    lv, ty = Counter(e["repro_level"] for e in entries), Counter(t for e in entries for t in e["memory_types"])
    return {"entries": len(entries), "levels": {k: lv[k] for k in LEVELS}, "types": {k: ty[k] for k in TYPES}}


def line(e) -> str:
    sc = e["scale"]
    size = " ".join(f"{v:,}{u}" for v, u in [(sc["conversations"], " conv"), (sc["questions"], " Q")] if v is not None)
    link = e["links"]["code"] or e["links"]["paper"] or e["links"]["data"] or "-"
    return " | ".join([e["slug"], e["name"], e["release_date"] or "undated", ",".join(e["memory_types"]),
                       e["repro_level"], size or "-", link])


def public(e) -> dict:
    return {k: v for k, v in e.items() if not k.startswith("_")}


def update(path: Path = DATA) -> int:
    with urllib.request.urlopen(SOURCE_URL, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
    if not (isinstance(data, list) and data and all(isinstance(e, dict) and "slug" in e for e in data)):
        raise ValueError("unexpected registry data")  # keep the old snapshot
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)
    return len(data)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="bench_scout", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("find", help="rank benchmarks for a query")
    f.add_argument("query", nargs="?", default="")
    f.add_argument("--type", action="append", choices=TYPES)
    f.add_argument("--level", action="append", choices=LEVELS)
    f.add_argument("--year", action="append")
    f.add_argument("--has", action="append", choices=list(FLAGS))
    f.add_argument("--exact", action="store_true", help="website search: all words must appear, newest first")
    f.add_argument("--top", type=int, default=10)
    f.add_argument("--json", action="store_true")
    s = sub.add_parser("show", help="one benchmark with its sources")
    s.add_argument("slug")
    sub.add_parser("stats", help="counts by repro level and memory type")
    sub.add_parser("update", help="download the latest registry snapshot")
    a = p.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")

    if a.cmd == "update":
        print(f"updated {DATA.name}: {update()} entries")
        return 0
    entries = load()
    if a.cmd == "stats":
        print(json.dumps(stats(entries), indent=1))
    elif a.cmd == "show":
        e = by_slug(entries, a.slug)
        if not e:
            print(f"bench_scout: no benchmark '{a.slug}'", file=sys.stderr)
            return 1
        print(json.dumps(public(e), ensure_ascii=False, indent=1))
    else:
        facet = (a.type, a.level, a.year, a.has)
        rows = (site_filter(entries, a.query, *facet) if a.exact or not a.query
                else find(entries, a.query, *facet, top=len(entries)))[:a.top]
        if a.json:
            print(json.dumps([public(e) for e in rows], ensure_ascii=False, indent=1))
        else:
            print("\n".join(map(line, rows)) or "no match")
    return 0


if __name__ == "__main__":
    sys.exit(main())
