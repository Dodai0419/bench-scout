# AGENTS.md: bench-scout

Use bench-scout when someone asks which benchmark to evaluate an agent memory system on (long-term chat memory, personalization, coding agents across sessions, memory poisoning, knowledge editing, multimodal memory), or wants facts about a named memory benchmark (scale, links, judge model, reproducibility) with sources.

## Commands (run from the repo root; Python 3.9+, no dependencies)

```bash
python bench_scout.py find "coding agent memory across sessions" --top 5   # BM25 ranked
python bench_scout.py find "memory poisoning" --type memory_security --has code
python bench_scout.py find locomo --exact        # the registry website search: all words, newest first
python bench_scout.py show locomo-conv           # every field plus where it came from
python bench_scout.py stats                      # counts by repro level and memory type
python bench_scout.py update                     # refresh data/benchmarks.json from the registry site
```

Filters: `--type` (conversational_longterm, personalization, episodic, semantic_knowledge_update, procedural_workflow, coding_cross_session, parametric, multi_agent_group, multimodal, embodied, memory_security), `--level` (paper_only, data_public, official_script, ...), `--year 2026`, `--has code|data|judge|peer`. Each can repeat. Add `--json` for full records.

Output: one line per benchmark: `slug | name | release | types | repro level | scale | best link`.

## Rules
- Quote numbers and links only from `show` output; every field there has a `sources` entry.
- `null` means the paper or repo does not say. Do not fill it in.
- Data is CC BY 4.0 from Fengzdadi/memory-bench-registry: credit it when you reuse it.
