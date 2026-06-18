from __future__ import annotations

import json
from pathlib import Path

from awrag.engine import intake, query, status, symbol_for


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
    assert (dataset_root / "counts" / "anchor_counts.awbin").exists()
    assert (dataset_root / "counts" / "relation_counts.awbin").exists()
    assert (dataset_root / "counts" / "block_anchor_postings.awbin").exists()
    assert (dataset_root / "state" / "dataset_lexicon.json").exists()
    assert (dataset_root / "coordinates" / "coordinate_index.jsonl").exists()
    assert (dataset_root / "citations" / "citations.jsonl").exists()

    lexicon = json.loads((dataset_root / "state" / "dataset_lexicon.json").read_text(encoding="utf-8"))
    manifest = json.loads((dataset_root / "dataset_manifest.json").read_text(encoding="utf-8"))
    assert lexicon["scope"] == "dataset_local"
    assert lexicon["symbol_system"] == "awrag_public_6b@1"
    assert lexicon["symbol_bytes"] == 6
    assert lexicon["symbol_transferable"] is False
    assert lexicon["anchorworks_lifetime_symbol_compatible"] is False
    assert lexicon["anchor_count"] > 0
    assert lexicon["anchors"][0]["symbol_system"] == "awrag_public_6b@1"
    assert lexicon["anchors"][0]["transferable"] is False
    assert lexicon["anchors"][0]["lifetime_allowed"] is False
    assert_protected_notice(result)
    assert_protected_notice(lexicon)
    assert_protected_notice(manifest)
    assert manifest["symbol_system"] == "awrag_public_6b@1"
    assert manifest["symbol_bytes"] == 6
    assert manifest["count_backend"] == "awrag_native_binary_counts@1"
    assert manifest["symbol_transferable"] is False
    assert manifest["anchorworks_lifetime_symbol_compatible"] is False


def test_demo_uses_native_binary_counts_not_sqlite(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Native binary counts stay dataset-local.", encoding="utf-8")

    result = intake(tmp_path / "runtime", "reviewer_docs", source)
    dataset_root = tmp_path / "runtime" / "datasets" / "reviewer_docs"
    status_result = status(tmp_path / "runtime", "reviewer_docs")

    assert result["count_backend"] == "awrag_native_binary_counts@1"
    assert status_result["count_backend"] == "awrag_native_binary_counts@1"
    assert not (dataset_root / "counts" / "dataset_counts.sqlite").exists()
    assert "sqlite_counts_path" not in status_result
    assert status_result["anchor_counts_path"].endswith("anchor_counts.awbin")
    assert status_result["relation_counts_path"].endswith("relation_counts.awbin")
    assert status_result["block_anchor_postings_path"].endswith("block_anchor_postings.awbin")


def test_public_symbols_are_fixed_six_byte_dataset_local_ids() -> None:
    symbol = symbol_for("dataset")

    assert symbol.startswith("0x")
    assert len(symbol) == 14
    int(symbol[2:], 16)


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


def test_query_prefers_compact_direct_evidence_over_large_noisy_block(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    noisy_lines = ["| Title | Link | Notes |", "| --- | --- | --- |"]
    noisy_lines.extend(f"| Generic model adapter table row {index} | link | filler data boundary citation installer |" for index in range(90))
    source.write_text(
        "\n".join(noisy_lines)
        + "\n\n"
        + "Dataset-local counts are explained here. The dataset lexicon and counts stay with the dataset.",
        encoding="utf-8",
    )
    intake(tmp_path / "runtime", "reviewer_docs", source)

    result = query(tmp_path / "runtime", "reviewer_docs", "What explains dataset-local counts?", top_k=3)
    top = result["answer_packet"]["locations"][0]

    assert "Dataset-local counts are explained here" in top["text"]
    assert top["direct_hit_count"] >= 2


def test_query_ignores_standalone_punctuation_anchors(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "Question marks and table pipes should not dominate retrieval.\n\n"
        "Dataset-local citation rules are explained in this compact block.",
        encoding="utf-8",
    )
    intake(tmp_path / "runtime", "reviewer_docs", source)

    result = query(tmp_path / "runtime", "reviewer_docs", "What are the citation rules?", top_k=2)
    top = result["answer_packet"]["locations"][0]

    assert "Dataset-local citation rules" in top["text"]
    assert "?" not in top["matched_anchors"]
    assert "|" not in top["matched_anchors"]


def test_rapid_queries_write_distinct_outputs(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Dataset counts stay local. Citations point to source coordinates.", encoding="utf-8")
    intake(tmp_path / "runtime", "reviewer_docs", source)

    first = query(tmp_path / "runtime", "reviewer_docs", "Where do dataset counts stay?")
    second = query(tmp_path / "runtime", "reviewer_docs", "Where do citations point?")

    assert first["output_path"] != second["output_path"]
    assert Path(first["output_path"]).exists()
    assert Path(second["output_path"]).exists()


def test_generic_question_words_do_not_outrank_content_anchors(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "The project says many things about files and documents.\n\n"
        "AWRAG citations are owned by the system and point to dataset-local coordinates.",
        encoding="utf-8",
    )
    intake(tmp_path / "runtime", "reviewer_docs", source)

    result = query(tmp_path / "runtime", "reviewer_docs", "What does the project say about citations?", top_k=2)
    top = result["answer_packet"]["locations"][0]

    assert "AWRAG citations are owned" in top["text"]
    assert "say" not in top["matched_anchors"]
    assert "project" not in top["matched_anchors"]


def test_acronym_surfaces_are_casefolded_anchors_not_letter_streams(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "Local LLM providers are configured through the model adapter.",
        encoding="utf-8",
    )
    intake(tmp_path / "runtime", "reviewer_docs", source)

    result = query(tmp_path / "runtime", "reviewer_docs", "Where are llm providers configured?", top_k=1)
    top = result["answer_packet"]["locations"][0]

    assert "Local LLM providers" in top["text"]
    assert "llm" in top["matched_anchors"]
    assert "l" not in top["matched_anchors"]
    assert "m" not in top["matched_anchors"]


def test_evidence_qualifier_demotes_broad_heading_for_content(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "## Next Steps\n\n"
        "The next production step is to attach the evidence qualifier before final citation packet selection.",
        encoding="utf-8",
    )
    intake(tmp_path / "runtime", "reviewer_docs", source)

    result = query(tmp_path / "runtime", "reviewer_docs", "What are the next production steps?", top_k=2)
    locations = result["answer_packet"]["locations"]

    assert locations
    assert "evidence qualifier" in locations[0]["text"]
    assert result["answer_packet"]["qualification"]["qualified_count"] >= 1
    rejected_text = "\n".join(row["text"] for row in result["answer_packet"]["rejected_locations"])
    assert "## Next Steps" in rejected_text


def test_evidence_qualifier_refuses_unsupported_low_coverage_query(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "Compliance policy updates are documented for local datasets.",
        encoding="utf-8",
    )
    intake(tmp_path / "runtime", "reviewer_docs", source)

    result = query(tmp_path / "runtime", "reviewer_docs", "Where is the Mars database compliance policy defined?", top_k=3)

    assert result["answer_packet"]["locations"] == []
    assert result["answer_packet"]["qualification"]["support_state"] == "no_qualified_evidence"
    assert result["answer_packet"]["rejected_locations"]
    assert "unsupported_refusal_threshold" in result["answer_packet"]["rejected_locations"][0]["qualification"]["reject_reasons"]

