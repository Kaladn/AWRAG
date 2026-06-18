# AWRAG

Copyright (c) 2026 Lee Mercey. Owner: Cortex Evolved Systems. All rights reserved.

## Declaration #1: This Demo Uses Deterministic NLP, Not LLM Reasoning

This reviewer demo does not use an LLM as the final answer authority.

AnchorWorks currently demonstrates the evidence engine:

- local dataset intake
- dataset-local counts
- dataset-local lexical values
- source coordinate mapping
- evidence selection
- citation/provenance receipts
- strict data boundaries
- optional model/no-model adapter boundary
- deterministic NLP wording from locked evidence packets

The demo output includes both an evidence/coordinate packet and a small
deterministic NLP answer resolved from that locked packet.

AnchorWorks does not "know" in the human conversational sense. It knows what
was provided, where it is located, how it connects, and whether evidence exists
inside the admitted dataset.

The current language bridge is intentionally narrow:

```text
AW evidence/coordinate packet
-> deterministic NLP resolver
-> cited readable answer
```

We are intentionally not using an LLM as the reasoning authority for this layer.
A language model may be used later as an optional wording adapter, but it must
not own evidence, citations, source selection, or truth.

The intended architecture is:

```text
AW finds and proves.
NLP resolves speech from AW-provided locations.
LLM, if used, only words a locked packet.
```

Reviewers should evaluate this demo on whether data stays dataset-local, whether
evidence is found, whether source coordinates are correct, whether
citations/receipts are produced, whether unsupported answers are refused, and
whether the deterministic NLP resolver preserves AW-owned citations.

## Declaration #2: This Is Beyond POC, And The Demo Surface Is Now Frozen

This package is not a toy proof of concept. It is a small, inspectable
implementation of the AnchorWorks evidence contract:

```text
admitted data
-> dataset-local lexical values
-> dataset-local relational counts
-> source coordinates
-> AWRAG-owned citations
-> qualification receipts
-> evidence/coordinate packet
```

The local demo size is a review constraint, not an architecture limit. The same
contract can be applied to larger admitted corpora, file stores, document
systems, databases, or prebuilt indexes when a connector exposes stable records,
chunks, rows, or coordinates.

After the evidence qualifier addition, this reviewer demo enters
stabilization-only mode. No new worker, dataset-specific adapter, renderer,
model behavior, or feature lane should be added to this demo package unless it
protects an existing contract, fixes a verified bug, improves tests, or clarifies
reviewer documentation.

The intended next work is tightening:

```text
contracts
tests
receipts
failure reports
reviewer instructions
```

not expanding the demo into a swamp of one-off modules.

## Declaration #3: Public Demo Symbols Are Not The Private Symbol Genome

AWRAG public/demo symbols use a separate six-byte dataset-local namespace:

```text
symbol_system: awrag_public_6b@1
symbol_bytes: 6
scope: dataset_local_demo_only
transferable: false
lifetime_allowed: false
anchorworks_lifetime_symbol_compatible: false
```

This demo keeps the compact-symbol pattern:

```text
anchors
-> public/demo symbols
-> dataset-local relation counts
```

but it does not expose, emulate, or export the private AnchorWorks/Cortex
Evolved Systems symbol genome. Public AWRAG symbols are implementation IDs for
one dataset-local package. They are not portable authority, not lifetime memory,
and not compatible with private AnchorWorks symbol identity.

This protects both sides:

```text
Public AWRAG:
  demo-safe six-byte dataset symbols
  local counts and citations
  reviewer-inspectable behavior

Private AnchorWorks:
  protected lifetime symbol genome
  proprietary symbol assignment
  system-specific memory authority
```

AWRAG is a small public-review/demo slice of AnchorWorks focused on local,
dataset-scoped retrieval:

```text
local data
-> dataset-local lexicon
-> native binary dataset-local counts
-> coordinates
-> AWRAG citations
-> evidence packet
-> deterministic NLP answer
```

## License Posture

This repository is public for review, demonstration, and evaluation only. It is
not open source under an OSI license. See `LICENSE`.

## Watermark

Generated outputs are AWRAG public-review facsimiles. They are not source
evidence. Verify against cited source coordinates.

## Data Boundary

```text
RAG counts belong to the dataset.
Dataset lexical values belong to the dataset.
No persistent/user memory is written by this package.
No model is allowed to search.
Citations are created by AWRAG from local coordinates.
The public demo count backend is native fixed-width binary, not SQLite.
Final answer text is resolved by deterministic NLP from locked AWRAG locations,
not by LLM reasoning.
```

Architecture-significant changes are logged in `WORK_LEDGER.md`. Backend,
storage, symbol, data-scope, citation, or model-authority substitutions are
governed by `ARCHITECTURE_GUARDRAILS.md`.

## Install

```powershell
python -m pip install -e .
```

## Quick Start

```powershell
$runtime = "$HOME\AWRAG_Runtime"
awrag init --runtime-root $runtime --dataset-id reviewer_docs
awrag intake --runtime-root $runtime --dataset-id reviewer_docs --source "<path-to-reviewer-docs>"
awrag status --runtime-root $runtime --dataset-id reviewer_docs
awrag query --runtime-root $runtime --dataset-id reviewer_docs --question "What does this dataset say about local counts?"
```

The dataset-local runtime is created under:

```text
<runtime-root>/datasets/<dataset-id>/
  dataset_manifest.json
  state/dataset_lexicon.json
  counts/anchor_counts.awbin
  counts/relation_counts.awbin
  counts/block_anchor_postings.awbin
  coordinates/coordinate_index.jsonl
  citations/citations.jsonl
  outputs/
  receipts/
```

## Not Included

This public demo does not include:

- live AnchorWorks runtime memory
- persistent/user counts
- private datasets
- redistribution-restricted evaluation payloads
- model credentials
- hosted service code
