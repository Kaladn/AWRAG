from __future__ import annotations

import json
from pathlib import Path

from awrag.engine import intake, query, status


def assert_protected_notice(payload: dict) -> None:
    assert payload["copyright"] == "Copyright (c) 2026 Lee Mercey. Owner: Cortex Evolved Systems. All rights reserved."
    assert payload["owner"] == "Cortex Evolved Systems"
    assert payload["license"] == "AWRAG Public Review License"
    assert payload["watermark_locked"] is True
    assert payload["removal_prohibited"] is True
    assert "facsimile" in payload["watermark"].lower()
    assert "not source evidence" in payload["watermark"].lower()


def test_intake_writes_dataset_local_counts_and_lexicon(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text(
        "AWRAG REVIEW FACSIMILE.\nDataset counts stay local.\n\nThe dataset lexicon stays with the dataset.",
        encoding="utf-8",
    )

    result = intake(tmp_path / "runtime", "reviewer_docs", source)

    dataset_root = tmp_path / "runtime" / "datasets" / "reviewer_docs"
    assert result["scope"] == "dataset_local"
    assert result["persistent_memory"] is False
    assert (dataset_root / "counts" / "dataset_counts.sqlite").exists()
    assert (dataset_root / "state" / "dataset_lexicon.json").exists()
    assert (dataset_root / "coordinates" / "coordinate_index.jsonl").exists()
    assert (dataset_root / "citations" / "citations.jsonl").exists()

    lexicon = json.loads((dataset_root / "state" / "dataset_lexicon.json").read_text(encoding="utf-8"))
    manifest = json.loads((dataset_root / "dataset_manifest.json").read_text(encoding="utf-8"))
    assert lexicon["scope"] == "dataset_local"
    assert lexicon["anchor_count"] > 0
    assert_protected_notice(result)
    assert_protected_notice(lexicon)
    assert_protected_notice(manifest)


def test_query_returns_awrag_owned_citations(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Dataset counts stay local and reviewer data is not persistent memory.", encoding="utf-8")
    intake(tmp_path / "runtime", "reviewer_docs", source)

    result = query(tmp_path / "runtime", "reviewer_docs", "Where do dataset counts stay?", top_k=2)

    assert result["scope"] == "dataset_local"
    assert result["model_used"] == "none"
    assert result["model_may_search"] is False
    assert_protected_notice(result)
    locations = result["answer_packet"]["locations"]
    assert locations
    assert locations[0]["citation"].startswith("[AWCIT-")
    assert "Dataset counts stay local" in locations[0]["text"]
    output_path = Path(result["output_path"])
    assert_protected_notice(json.loads(output_path.read_text(encoding="utf-8")))


def test_status_reports_no_persistent_memory(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Local counts only.", encoding="utf-8")
    intake(tmp_path / "runtime", "reviewer_docs", source)

    result = status(tmp_path / "runtime", "reviewer_docs")

    assert result["scope"] == "dataset_local"
    assert result["persistent_memory"] is False
    assert result["anchor_count"] > 0
    assert_protected_notice(result)


def test_every_persisted_artifact_has_indelible_watermark(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("AWRAG citations point to local lines.\n\nCoordinates stay with the dataset.", encoding="utf-8")

    receipt = intake(tmp_path / "runtime", "reviewer_docs", source)
    query_result = query(tmp_path / "runtime", "reviewer_docs", "Where do citations point?")
    dataset_root = tmp_path / "runtime" / "datasets" / "reviewer_docs"

    json_paths = [
        dataset_root / "dataset_manifest.json",
        dataset_root / "state" / "dataset_lexicon.json",
        Path(receipt["receipt_path"]),
        Path(query_result["output_path"]),
    ]
    for path in json_paths:
        assert_protected_notice(json.loads(path.read_text(encoding="utf-8")))

    jsonl_paths = [
        dataset_root / "citations" / "citations.jsonl",
        dataset_root / "coordinates" / "coordinate_index.jsonl",
    ]
    for path in jsonl_paths:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert rows
        for row in rows:
            assert_protected_notice(row)

