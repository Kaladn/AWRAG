# AWRAG Public Demo Checkpoint

Copyright (c) 2026 Lee Mercey.
Owner: Cortex Evolved Systems.
All rights reserved.

## Status

AWRAG is now a public-facing, reviewer-safe RAG slice of the larger
AnchorWorks/Cortex Evolved Systems architecture.

It is beyond a toy proof of concept. The demo proves the evidence contract in a
small, inspectable package:

```text
admitted data
-> dataset-local lexical values
-> dataset-local relation counts
-> source coordinates
-> AWRAG-owned citations
-> evidence qualification receipts
-> evidence/coordinate packet
```

It intentionally does not ship the final production speech renderer, private
lifetime memory, or private symbol genome.

## Done

- Public repo can be freshly cloned and run outside the dev tree.
- Runtime, incoming data, outputs, datasets, counts, citations, and receipts can
  live outside the codebase.
- Dataset-local intake builds:
  - dataset manifest
  - dataset lexicon
  - SQLite dataset counts
  - coordinate index
  - citation JSONL
  - watermarked receipts and query outputs
- Query path runs with `model_used=none` and `model_may_search=false`.
- AWRAG owns citations and source coordinates.
- Evidence qualifier now gates retrieval candidates before final packet
  selection.
- Public demo symbol namespace is explicit:

```text
symbol_system: awrag_public_6b@1
symbol_bytes: 6
symbol_scope: dataset_local_demo_only
transferable: false
lifetime_allowed: false
anchorworks_lifetime_symbol_compatible: false
```

- Public symbols are demo-safe dataset implementation IDs, not AnchorWorks
  lifetime symbols and not the private Cortex Evolved Systems symbol genome.
- README declares:
  - no final natural-language rendering claim
  - demo is beyond POC
  - demo surface is frozen for stabilization
  - public symbols are not private genome symbols

## Verified

Current verification:

```text
python -m pytest tests -q
13 passed
```

Recent isolated reviewer-runtime runs verified:

- fresh GitHub clone execution
- 100-question local-doc stress run
- TechQA dataset-local intake
- SciFact dataset-local intake
- cross-dataset miss ontology audit

Key audit receipt:

```text
data_absent: 0
index_absent: 0
anchor_absent: 0
```

The main remaining misses are qualification and interpretation misses, not
basic data visibility failures.

## Frozen Demo Rule

After the evidence qualifier and public six-byte symbol namespace, this demo is
stabilization-only.

Allowed work:

- bug fixes
- tests
- documentation
- receipt clarity
- contract hardening
- reviewer packaging
- security/license/path hygiene

Not allowed without a new explicit architecture decision:

- new workers
- dataset-specific hacks
- private lifetime memory
- private symbol genome export
- final speech renderer
- LLM reasoning authority
- connector sprawl

## Next Needs

The next work is not expansion. It is tightening.

Priority order:

1. **Contract hardening**
   Ensure every generated artifact clearly states demo scope, dataset-local
   scope, symbol namespace, model authority, and citation ownership.

2. **Evidence qualifier receipts**
   Make qualification receipts easier to audit:
   accepted terms, missing terms, reject reasons, and support state.

3. **Unsupported/refusal gate**
   Tighten no-evidence behavior so weak nearby text does not become false
   evidence.

4. **Question role parsing**
   Improve subject/predicate/object and scope/context extraction without using
   an LLM as authority.

5. **Path/config classifier**
   Separate real paths/endpoints/configs from slash phrases such as
   `before/after` or `pass/fail`.

6. **Quantity receipts**
   Keep numbers as evidence objects with role, unit, source coordinate, and
   computation basis.

7. **Reviewer package polish**
   Keep install/run instructions, READ_FIRST text, manifests, and reports
   aligned with the frozen public contract.

## Core Law

```text
Public AWRAG proves the dataset-local evidence contract.
Private AnchorWorks keeps the lifetime symbol genome and memory authority.
Do not blur those namespaces.
```
