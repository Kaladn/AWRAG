# AWRAG

Copyright (c) 2026 Lee Mercey. Owner: Cortex Evolved Systems. All rights reserved.

## Declaration #1: This Demo Does Not Render Final Natural-Language Answers

This reviewer demo does not claim to be the final AnchorWorks speech/rendering
layer.

AnchorWorks currently demonstrates the evidence engine:

- local dataset intake
- dataset-local counts
- dataset-local lexical values
- source coordinate mapping
- evidence selection
- citation/provenance receipts
- strict data boundaries
- optional model/no-model adapter boundary

The demo output should be read as an evidence/coordinate packet, not as the
final human-facing answer product.

AnchorWorks does not "know" in the human conversational sense. It knows what
was provided, where it is located, how it connects, and whether evidence exists
inside the admitted dataset.

The missing production layer is the language bridge:

```text
AW evidence/coordinate packet
-> deterministic NLP question/answer shaping
-> final human-readable speech output
```

We are intentionally not using an LLM as the reasoning authority for this layer.
A language model may be used later as an optional wording adapter, but it must
not own evidence, citations, source selection, or truth.

The intended architecture is:

```text
AW finds and proves.
NLP fills the language gap.
LLM, if used, only words a locked packet.
```

Until the proper NLP-connected speech renderer is attached, reviewers should
evaluate this demo on whether data stays dataset-local, whether evidence is
found, whether source coordinates are correct, whether citations/receipts are
produced, whether unsupported answers are refused, and whether the system avoids
absorbing reviewer data into persistent memory.

Final natural-language rendering is intentionally out of scope for this package.

AWRAG is a small public-review/demo slice of AnchorWorks focused on local,
dataset-scoped retrieval:

```text
local data
-> dataset-local lexicon
-> dataset-local counts
-> coordinates
-> AWRAG citations
-> cited answer packet
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
```

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
  counts/dataset_counts.sqlite
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
