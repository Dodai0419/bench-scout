<div align="center">

# bench-scout

**Find the agent-memory benchmark that fits your system in one offline command.**

207 source-traced benchmarks from [memory-bench-registry](https://github.com/Fengzdadi/memory-bench-registry), ranked with the BM25 recall from [caveman](https://github.com/JuliusBrussee/caveman)'s memory store. One Python file, no dependencies.

Works with **Claude Code** and **Codex**.

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg) ![Status: prototype](https://img.shields.io/badge/status-prototype-orange.svg)

</div>

## Quick start
```bash
git clone https://github.com/Dodai0419/bench-scout && cd bench-scout
python bench_scout.py find "coding agent memory across sessions" --top 4
```
```
chainswe | ChainSWE | 2026-07 | coding_cross_session | data_public | 100 conv 304 Q | https://arxiv.org/abs/2607.02606
memorycode | MemoryCode | 2025-02 | coding_cross_session,conversational_longterm,semantic_knowledge_update | official_script | 360 conv | https://github.com/Cohere-Labs-Community/MemoryCode
memcalib | MemCalib | 2026-09 | personalization | data_public | 1,500 Q | https://github.com/Quark-Medical/memcalib
stateful-swe-bench | Stateful SWE-bench | 2025-10 | coding_cross_session,personalization | official_script | 15 conv 500 Q | https://github.com/OpenHands/ToM-SWE
```

## The problem
- There are now 200+ agent-memory benchmarks and new ones every week; picking one means reading a 207-row README.
- The registry website needs every word as an exact substring: "remember user preferences over many chats" finds nothing there (bench-scout ranks REALTALK and ConvoMem in its top 3).
- An agent asked "what should I evaluate my memory layer on?" has no offline, citable way to answer.

## The solution
| Idea | Fixes |
|------|-------|
| **BM25 ranking ported from caveman's cavemem** (k1 1.5, b 0.75, same tokenizer and stopwords) | Natural-language questions rank the right benchmarks without exact words |
| **`--exact` reproduces the registry website search** (same fields, same order) | Nothing you could find on the site is lost |
| **`show` prints every field with its `sources` entry** | Answers stay traceable to a paper section or README line |
| **Facets: `--type`, `--level`, `--year`, `--has code/data/judge/peer`** | "Peer-reviewed, has data, memory security" in one line |

```bash
python bench_scout.py find "memory poisoning" --type memory_security --has code
python bench_scout.py find locomo --exact
python bench_scout.py show locomo-conv
python bench_scout.py stats
python bench_scout.py update      # pull the latest registry snapshot
```

## Use with Claude Code
```bash
/plugin marketplace add Dodai0419/bench-scout
/plugin install bench-scout@bench-scout
```

## Use with Codex (ChatGPT)
```bash
git clone https://github.com/Dodai0419/bench-scout && cp -r bench-scout/skills/* ~/.codex/skills/
```
Or copy `AGENTS.md` to your project root.

## Benchmarks
Same data (registry commit `e0d909a`, 207 entries). Windows 11, Python 3.11.1, median of 5 runs unless noted.

| | original | this repo |
|-|-|-|
| load all 207 entries (in process) | 2.77 s (`build_readme.load_entries()`, PyYAML, median of 3) | 15 ms (warm; 219 ms first run) |
| search answer from the CLI | 3.97 s to build the site (`build_site.py`), then a browser | 0.46 s (`find locomo --exact`) |
| counts by level and type | 5.23 s (`build_readme.py --check`, median of 3) | 0.46 s (`stats`) |
| natural-language ranking | not available (substring filter) | 0.54 s (`find "coding agent memory across sessions"`) |
| lines of code | 805 (build_readme 144 + build_site 59 + site/index.html 602) + 111 (cavemem bm25.go) | 169 |
| dependencies | 3 (PyYAML, jsonschema, Jinja2) + Go for cavemem | 0 |

Parity: `--exact` returns the same slugs in the same order as the website's own filter code (run in Node on the same data) for 8 queries; `stats` equals the registry README counts. Both are unit tests (`python -m unittest -q`). The registry's contributor tools (`validate.py`, README generation, `discover.py`) are not included: use the upstream repo to add entries.

## Inspired by
- [Fengzdadi/memory-bench-registry](https://github.com/Fengzdadi/memory-bench-registry): the data (CC BY 4.0) and the website search rules.
- [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman): the BM25 recall from cavemem (`mem/bm25.go`, Apache-2.0).

## Roadmap
- [ ] `compare a b c` side-by-side table for a short list
- [ ] MCP server mode so agents can call `find` without a shell

## License
MIT for the code. `data/benchmarks.json` is CC BY 4.0 (Fengzdadi). See `NOTICE`.
