# AWRAG Work Ledger

Copyright (c) 2026 Lee Mercey.
Owner: Cortex Evolved Systems.
All rights reserved.

This file records architecture-significant work in plain language. It exists so
backend substitutions, storage changes, model changes, data-scope changes, and
contract changes cannot be hidden as implementation details.

## 2026-06-18 - Native Binary Count Backend Recovery

### Operator Direction

The public AWRAG demo must represent the AnchorWorks-style count engine shape:

```text
local admitted data
-> dataset-local lexicon
-> native binary dataset-local counts
-> source coordinates
-> AWRAG-owned citations
-> evidence/coordinate packet
```

The public demo may use the demo-safe symbol namespace:

```text
symbol_system: awrag_public_6b@1
symbol_bytes: 6
scope: dataset_local_demo_only
```

but it must not replace the count engine with SQL.

### What Went Wrong

Codex introduced SQLite in commit:

```text
9ca8bad Publish dataset-local AWRAG review demo
```

That commit added `src/awrag/engine.py` with:

```text
import sqlite3
counts/dataset_counts.sqlite
SQL tables for anchors, relations, blocks, block_anchors, and citations
SQL query path for neighbor lookup and block scoring
```

This was wrong for AWRAG. It preserved some reviewer-facing scaffolding, but it
did not preserve the required native binary count backend shape.

### Why It Was Wrong

SQLite is a general database backend. AWRAG requires a local, deterministic,
native binary count spine for the public demo.

The mistake changed the system claim from:

```text
native compact count structure
fast deterministic relation search
binary count behavior
small active evidence layer
```

into:

```text
SQLite-backed indexed storage with AWRAG-shaped metadata
```

That is not the same system.

### Recovery Performed

SQLite was removed from `src/awrag/engine.py`.

The active public demo backend is now:

```text
count_backend: awrag_native_binary_counts@1
```

Dataset-local binary count files:

```text
counts/anchor_counts.awbin
counts/relation_counts.awbin
counts/block_anchor_postings.awbin
```

Reviewer-readable JSON/JSONL remains only for:

```text
dataset_manifest.json
state/dataset_lexicon.json
state/blocks.jsonl
coordinates/coordinate_index.jsonl
citations/citations.jsonl
outputs/
receipts/
```

### Tests Added

Regression test added:

```text
test_demo_uses_native_binary_counts_not_sqlite
```

The test requires:

```text
count_backend == awrag_native_binary_counts@1
anchor_counts.awbin exists
relation_counts.awbin exists
block_anchor_postings.awbin exists
dataset_counts.sqlite does not exist
sqlite_counts_path is not present in status output
```

### Verification

```text
python -m pytest tests -q
14 passed

python -m compileall src
passed

CLI verification:
count_backend = awrag_native_binary_counts@1
anchor_counts.awbin created
relation_counts.awbin created
block_anchor_postings.awbin created
```

### Current Honesty Statement

The public AWRAG demo now uses a demo-safe native binary count backend with
public six-byte dataset-local symbols.

It is not the private AnchorWorks lifetime count spine.

It must not be marketed as the private AnchorWorks symbol genome or private
lifetime memory system.

It may be described as:

```text
A public-review AWRAG slice using native fixed-width binary dataset counts and
demo-safe six-byte dataset-local symbols.
```

## Required Logging Rule Going Forward

Every future architecture-significant change must add a ledger entry before it
is considered complete.

Required fields:

```text
date
operator direction
files changed
contract affected
backend/storage affected
data scope affected
model authority affected
tests run
honesty statement
```

No backend, storage, model, symbol, count, citation, data-scope, or persistence
change may be treated as a private implementation detail.

## 2026-06-18 - Deterministic NLP Answer Resolver

### Operator Direction

Final answer output needs NLP, not LLM reasoning. AW owns evidence, citations,
coordinates, counts, and refusal. The language layer may only make admitted
locations readable.

### Change

Added:

```text
src/awrag/nlp_resolver.py
resolver: awrag_deterministic_nlp_resolver@1
```

The query output now includes:

```text
answer_packet
final_answer
```

The resolver receives only `answer_packet.locations`, picks readable
question-relevant sentences from those locations, and appends the AWRAG-owned
citation marker already present on the location.

### Guardrails

The resolver must not:

```text
search
read counts
read source files
create citations
rewrite citations
call an LLM
```

Unsupported packets return:

```text
status: not_enough_information
```

### Tests Added

Tests now verify:

```text
final_answer uses awrag_deterministic_nlp_resolver@1
model_used remains none
model_may_search remains false
citations come from answer_packet.locations
unsupported packets remain not_enough_information
```

## 2026-06-18 - Package Cleanup And Symbol Collision Guard

### Operator Direction

Before handoff, the reviewer package must be clean and generic:

```text
no bytecode caches
clear test instructions
public six-byte symbol collision guard
no dataset-specific code names
```

### Change

Added a dataset-local public symbol collision guard before binary count files
are written. If two different anchors map to the same six-byte public demo
symbol, intake fails instead of writing ambiguous counts.

Added explicit test instructions for:

```text
python -m pip install -e .
python -m pytest tests -q
```

and direct unpacked-package testing with:

```text
PYTHONPATH=src
```

### Tests Added

```text
test_intake_fails_on_public_symbol_collision
```
