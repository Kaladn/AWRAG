# AWRAG Architecture Guardrails

Copyright (c) 2026 Lee Mercey.
Owner: Cortex Evolved Systems.
All rights reserved.

These guardrails are part of the public AWRAG demo contract.

## Backend Substitution Rule

No backend substitution is allowed without an explicit work-ledger entry and a
test that proves the selected backend.

Forbidden as silent implementation details:

```text
SQL database replacement for native binary counts
external vector database replacement for local counts
hosted search replacement for local deterministic search
LLM reasoning replacement for AWRAG evidence selection
implicit lifetime-memory writes
private AnchorWorks symbol genome export
```

## Count Backend Rule

The public AWRAG demo count backend is:

```text
awrag_native_binary_counts@1
```

Required dataset-local count files:

```text
counts/anchor_counts.awbin
counts/relation_counts.awbin
counts/block_anchor_postings.awbin
```

The public demo must not create or depend on:

```text
counts/dataset_counts.sqlite
sqlite_counts_path
sqlite3
SQL tables for relation retrieval
```

## Symbol Namespace Rule

The public demo symbol namespace is:

```text
symbol_system: awrag_public_6b@1
symbol_bytes: 6
scope: dataset_local_demo_only
transferable: false
lifetime_allowed: false
anchorworks_lifetime_symbol_compatible: false
```

Public demo symbols are not the private AnchorWorks/Cortex Evolved Systems
symbol genome.

## Data Scope Rule

RAG data belongs to the dataset.

Dataset-local artifacts:

```text
dataset_manifest.json
state/dataset_lexicon.json
state/blocks.jsonl
counts/*.awbin
coordinates/coordinate_index.jsonl
citations/citations.jsonl
outputs/
receipts/
```

This package must not write reviewer data into persistent/user/lifetime memory.

## Model Authority Rule

The public demo default is:

```text
model_used: none
model_may_search: false
```

An optional model may only word a locked evidence packet. It may not own:

```text
source selection
evidence truth
citations
coordinates
counts
data scope
```

## Citation Rule

AWRAG owns citations.

The model does not invent, attach, rewrite, or validate citations. Citations come
from local coordinates and AWRAG citation records.

## Completion Rule

A change is not complete until:

```text
tests pass
grep proves forbidden backend strings are absent except negative tests/docs
WORK_LEDGER.md records the architecture impact
README/CHECKPOINT match the actual runtime behavior
```
