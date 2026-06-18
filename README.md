# AWRAG

Copyright (c) 2026 Lee Mercey. Owner: Cortex Evolved Systems. All rights reserved.

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
awrag intake --runtime-root $runtime --dataset-id reviewer_docs --source "C:\path\to\docs"
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
