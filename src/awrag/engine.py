from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


COPYRIGHT = "Copyright (c) 2026 Lee Mercey. Owner: Cortex Evolved Systems. All rights reserved."
WATERMARK = "AWRAG public-review facsimile output; not source evidence. Verify against cited source coordinates."
LICENSE_REF = "AWRAG Public Review License"
FACSIMILE_WARNING = "This output is a local processing facsimile, not source evidence or professional advice."
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?|[^\sA-Za-z0-9]", re.UNICODE)
MAX_BLOCK_LINES = 40
STOP_ANCHORS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "do",
    "does",
    "doc",
    "docs",
    "document",
    "documents",
    "explain",
    "explained",
    "explains",
    "file",
    "files",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "project",
    "say",
    "said",
    "says",
    "mention",
    "mentioned",
    "mentions",
    "that",
    "the",
    "this",
    "to",
    "what",
    "where",
    "which",
    "who",
    "why",
    "with",
}


@dataclass(frozen=True)
class DatasetPaths:
    root: Path
    incoming: Path
    state: Path
    counts: Path
    coordinates: Path
    citations: Path
    outputs: Path
    receipts: Path
    sqlite_path: Path
    lexicon_path: Path
    manifest_path: Path


def safe_id(value: str) -> str:
    out = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "").strip()).strip("._")
    if not out:
        raise ValueError("dataset id is required")
    return out


def dataset_paths(runtime_root: str | Path, dataset_id: str) -> DatasetPaths:
    root = Path(runtime_root).expanduser().resolve() / "datasets" / safe_id(dataset_id)
    return DatasetPaths(
        root=root,
        incoming=root / "incoming",
        state=root / "state",
        counts=root / "counts",
        coordinates=root / "coordinates",
        citations=root / "citations",
        outputs=root / "outputs",
        receipts=root / "receipts",
        sqlite_path=root / "counts" / "dataset_counts.sqlite",
        lexicon_path=root / "state" / "dataset_lexicon.json",
        manifest_path=root / "dataset_manifest.json",
    )


def ensure_dataset(runtime_root: str | Path, dataset_id: str, *, owner: str = "operator_defined") -> dict[str, Any]:
    paths = dataset_paths(runtime_root, dataset_id)
    for path in (paths.root, paths.incoming, paths.state, paths.counts, paths.coordinates, paths.citations, paths.outputs, paths.receipts):
        path.mkdir(parents=True, exist_ok=True)
    if not paths.manifest_path.exists():
        write_json(paths.manifest_path, {
            "schema": "awrag_dataset_manifest@1",
            "created_at": utc_now(),
            "dataset_id": safe_id(dataset_id),
            "owner": owner,
            "scope": "dataset_local",
            "rag_allowed": True,
            "promotion_allowed": False,
            "global_training_allowed": False,
            "delete_with_dataset": True,
            "counts_are_memory": False,
            "counts_belong_to": "dataset",
        })
    if not paths.lexicon_path.exists():
        write_json(paths.lexicon_path, {
            "schema": "awrag_dataset_lexicon@1",
            "dataset_id": safe_id(dataset_id),
            "scope": "dataset_local",
            "anchor_count": 0,
            "anchors": [],
        })
    with connect(paths.sqlite_path) as db:
        init_db(db)
    return status(runtime_root, dataset_id)


def intake(runtime_root: str | Path, dataset_id: str, source: str | Path, *, owner: str = "operator_defined", window: int = 6) -> dict[str, Any]:
    ensure_dataset(runtime_root, dataset_id, owner=owner)
    paths = dataset_paths(runtime_root, dataset_id)
    source_path = Path(source).expanduser().resolve()
    files = list(iter_files(source_path))
    if not files:
        raise FileNotFoundError(source_path)

    anchor_observations: Counter[str] = Counter()
    relation_observations = 0
    block_count = 0
    citation_count = 0
    source_receipts: list[dict[str, Any]] = []

    with connect(paths.sqlite_path) as db:
        init_db(db)
        for file_path in files:
            file_digest = sha1_text(str(file_path))
            text = file_path.read_text(encoding="utf-8", errors="replace")
            blocks = split_blocks(text)
            source_receipts.append({"path": str(file_path), "block_count": len(blocks)})
            for block_index, block in enumerate(blocks, start=1):
                block_id = f"{file_digest}:{block_index}"
                anchors = anchorize(block["text"])
                block_count += 1
                citation_id = f"AWCIT-{sha1_text(block_id)[:10]}"
                citation_count += 1
                db.execute(
                    "insert or replace into blocks(block_id, file_path, line_start, line_end, text, citation_id) values(?,?,?,?,?,?)",
                    (block_id, str(file_path), block["line_start"], block["line_end"], block["text"], citation_id),
                )
                db.execute(
                    "insert or replace into citations(citation_id, block_id, marker, file_path, line_start, line_end, text_hash) values(?,?,?,?,?,?,?)",
                    (citation_id, block_id, f"[{citation_id}]", str(file_path), block["line_start"], block["line_end"], sha1_text(block["text"])),
                )
                for position, anchor in enumerate(anchors):
                    symbol = symbol_for(anchor)
                    anchor_observations[anchor] += 1
                    db.execute(
                        "insert into block_anchors(block_id, anchor, position) values(?,?,?)",
                        (block_id, anchor, position),
                    )
                    db.execute(
                        "insert into anchors(anchor, symbol, observations) values(?,?,1) "
                        "on conflict(anchor) do update set observations=observations+1",
                        (anchor, symbol),
                    )
                    for offset in range(-window, window + 1):
                        if offset == 0:
                            continue
                        neighbor_index = position + offset
                        if 0 <= neighbor_index < len(anchors):
                            neighbor = anchors[neighbor_index]
                            relation_observations += 1
                            db.execute(
                                "insert into relations(anchor, neighbor, offset, observations) values(?,?,?,1) "
                                "on conflict(anchor, neighbor, offset) do update set observations=observations+1",
                                (anchor, neighbor, offset),
                            )
        db.commit()
        write_lexicon(paths, db)
        write_citation_jsonl(paths, db)
        write_coordinate_index(paths, db)

    receipt = {
        "schema": "awrag_intake_receipt@1",
        "created_at": utc_now(),
        "dataset_id": safe_id(dataset_id),
        "scope": "dataset_local",
        "source": str(source_path),
        "source_file_count": len(files),
        "block_count": block_count,
        "citation_count": citation_count,
        "unique_anchor_count": len(anchor_observations),
        "anchor_observation_count": sum(anchor_observations.values()),
        "relation_observation_count": relation_observations,
        "persistent_memory": False,
        "promotion_allowed": False,
        "sources": source_receipts,
        "paths": public_paths(paths),
    }
    receipt_path = paths.receipts / f"intake_{unique_stamp()}.json"
    write_json(receipt_path, receipt)
    receipt["receipt_path"] = str(receipt_path)
    return with_protected_notice(receipt)


def query(runtime_root: str | Path, dataset_id: str, question: str, *, top_k: int = 5) -> dict[str, Any]:
    paths = dataset_paths(runtime_root, dataset_id)
    ensure_dataset(runtime_root, dataset_id)
    q_anchors = expand_query_anchors(anchorize(question))
    if not q_anchors:
        raise ValueError("question produced no anchors")
    q_counter = Counter(q_anchors)

    with connect(paths.sqlite_path) as db:
        init_db(db)
        relation_neighbors = top_relation_neighbors(db, q_counter, limit=16)
        raw_candidate_blocks = score_blocks(db, q_counter, relation_neighbors, top_k=max(top_k * 5, 25))
        qualified = qualify_evidence(question, Counter(anchorize(question)), raw_candidate_blocks, top_k=top_k)

    output = {
        "schema": "awrag_query_result@1",
        "created_at": utc_now(),
        "dataset_id": safe_id(dataset_id),
        "scope": "dataset_local",
        "question": question,
        "question_anchors": list(q_counter),
        "relation_neighbors": relation_neighbors,
        "model_used": "none",
        "model_may_search": False,
        "persistent_memory": False,
        "answer_packet": {
            "instruction": "Use cited local evidence coordinates only. This packet is a facsimile output, not source evidence.",
            "citations_owned_by": "AWRAG",
            "qualification": qualified["summary"],
            "qualification_receipts": qualified["receipts"],
            "locations": qualified["locations"],
            "rejected_locations": qualified["rejected"],
        },
    }
    output_path = paths.outputs / f"query_{unique_stamp()}_{sha1_text(question)[:8]}.json"
    write_json(output_path, output)
    output["output_path"] = str(output_path)
    return with_protected_notice(output)


def status(runtime_root: str | Path, dataset_id: str) -> dict[str, Any]:
    paths = dataset_paths(runtime_root, dataset_id)
    with connect(paths.sqlite_path) as db:
        init_db(db)
        anchors = scalar(db, "select count(*) from anchors")
        relations = scalar(db, "select count(*) from relations")
        blocks = scalar(db, "select count(*) from blocks")
        citations = scalar(db, "select count(*) from citations")
    return with_protected_notice({
        "schema": "awrag_dataset_status@1",
        "dataset_id": safe_id(dataset_id),
        "scope": "dataset_local",
        "dataset_root": str(paths.root),
        "sqlite_counts_path": str(paths.sqlite_path),
        "dataset_lexicon_path": str(paths.lexicon_path),
        "anchor_count": anchors,
        "relation_count": relations,
        "block_count": blocks,
        "citation_count": citations,
        "persistent_memory": False,
    })


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    return db


def init_db(db: sqlite3.Connection) -> None:
    db.executescript(
        """
        create table if not exists anchors(anchor text primary key, symbol text not null, observations integer not null);
        create table if not exists relations(anchor text not null, neighbor text not null, offset integer not null, observations integer not null, primary key(anchor, neighbor, offset));
        create table if not exists blocks(block_id text primary key, file_path text not null, line_start integer not null, line_end integer not null, text text not null, citation_id text not null);
        create table if not exists block_anchors(block_id text not null, anchor text not null, position integer not null);
        create table if not exists citations(citation_id text primary key, block_id text not null, marker text not null, file_path text not null, line_start integer not null, line_end integer not null, text_hash text not null);
        create index if not exists idx_block_anchors_anchor on block_anchors(anchor);
        create index if not exists idx_relations_anchor on relations(anchor);
        """
    )


def iter_files(path: Path) -> Iterable[Path]:
    suffixes = {".txt", ".md", ".markdown", ".rst", ".csv", ".json", ".jsonl"}
    if path.is_file() and path.suffix.lower() in suffixes:
        yield path
        return
    if path.is_dir():
        for item in sorted(path.rglob("*")):
            if item.is_file() and item.suffix.lower() in suffixes and not any(part.startswith(".") for part in item.parts):
                yield item


def split_blocks(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    blocks: list[dict[str, Any]] = []
    current: list[str] = []
    start = 1
    for index, line in enumerate(lines, start=1):
        if line.strip():
            if not current:
                start = index
            current.append(line)
            continue
        if current:
            blocks.extend(chunk_block(current, start))
            current = []
    if current:
        blocks.extend(chunk_block(current, start))
    if not blocks and text:
        blocks.append({"line_start": 1, "line_end": max(1, len(lines)), "text": text})
    return blocks


def chunk_block(lines: list[str], start_line: int) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for offset in range(0, len(lines), MAX_BLOCK_LINES):
        chunk = lines[offset:offset + MAX_BLOCK_LINES]
        chunks.append({
            "line_start": start_line + offset,
            "line_end": start_line + offset + len(chunk) - 1,
            "text": "\n".join(chunk),
        })
    return chunks


def anchorize(text: str) -> list[str]:
    anchors: list[str] = []
    for match in WORD_RE.finditer(text):
        value = match.group(0).strip().casefold()
        if not value:
            continue
        if not any(ch.isalnum() for ch in value):
            continue
        if value in STOP_ANCHORS:
            continue
        if value.isalnum() and any(ch.isalpha() for ch in value) and any(ch.isdigit() for ch in value):
            anchors.extend(ch for ch in value if ch.isalnum())
        else:
            anchors.append(normalize_anchor(value))
    return anchors


def normalize_anchor(anchor: str) -> str:
    value = str(anchor or "").casefold().strip()
    if len(value) > 4 and value.endswith("ies"):
        return value[:-3] + "y"
    if len(value) > 3 and value.endswith("s") and not value.endswith("ss"):
        return value[:-1]
    return value


def expand_query_anchors(anchors: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for anchor in anchors:
        variants = [anchor, normalize_anchor(anchor)]
        if anchor.isalpha() and len(anchor) > 2:
            variants.append(anchor + "s")
        for variant in variants:
            if variant and variant not in STOP_ANCHORS and variant not in seen:
                out.append(variant)
                seen.add(variant)
    return out


def symbol_for(anchor: str) -> str:
    return "0x" + sha1_text(anchor)[:10].upper()


def top_relation_neighbors(db: sqlite3.Connection, q_counter: Counter[str], *, limit: int) -> list[dict[str, Any]]:
    scores: Counter[str] = Counter()
    blocked = set(q_counter) | STOP_ANCHORS
    for anchor, weight in q_counter.items():
        for row in db.execute("select neighbor, sum(observations) as observations from relations where anchor=? group by neighbor", (anchor,)):
            neighbor = str(row["neighbor"])
            if neighbor in blocked:
                continue
            scores[neighbor] += int(row["observations"]) * weight
    return [{"anchor": anchor, "score": score} for anchor, score in scores.most_common(limit)]


def score_blocks(db: sqlite3.Connection, q_counter: Counter[str], relation_neighbors: list[dict[str, Any]], *, top_k: int) -> list[dict[str, Any]]:
    weights = Counter()
    direct_anchors = set(q_counter)
    for anchor, count in q_counter.items():
        weights[anchor] += 80 * count
    for index, row in enumerate(relation_neighbors):
        weights[str(row["anchor"])] += max(1, 4 - index // 4)
    block_scores: Counter[str] = Counter()
    hits: dict[str, set[str]] = {}
    direct_hits: Counter[str] = Counter()
    for anchor, weight in weights.items():
        df_row = db.execute("select count(distinct block_id) from block_anchors where anchor=?", (anchor,)).fetchone()
        document_frequency = int(df_row[0]) if df_row else 1
        adjusted_weight = weight / max(1.0, document_frequency ** 0.5)
        for row in db.execute("select distinct block_id from block_anchors where anchor=?", (anchor,)):
            block_id = str(row["block_id"])
            block_scores[block_id] += adjusted_weight
            hits.setdefault(block_id, set()).add(anchor)
            if anchor in direct_anchors:
                direct_hits[block_id] += 1
    out: list[dict[str, Any]] = []
    ranked_rows: list[tuple[str, float, float, int]] = []
    block_lengths = {
        str(row["block_id"]): int(row["anchor_count"])
        for row in db.execute("select block_id, count(*) as anchor_count from block_anchors group by block_id")
    }
    for block_id, score in block_scores.items():
        anchor_count = block_lengths.get(block_id, 1)
        density = float(score) / max(1.0, anchor_count ** 0.5)
        ranked_rows.append((block_id, float(score), density, anchor_count))
    ranked = sorted(
        ranked_rows,
        key=lambda item: (-direct_hits[item[0]], -item[2], -item[1], item[0]),
    )
    for block_id, score, density, anchor_count in ranked[:top_k]:
        block = db.execute(
            "select b.*, c.marker from blocks b join citations c on c.block_id=b.block_id where b.block_id=?",
            (block_id,),
        ).fetchone()
        if not block:
            continue
        out.append({
            "citation": str(block["marker"]),
            "file_path": str(block["file_path"]),
            "line_start": int(block["line_start"]),
            "line_end": int(block["line_end"]),
            "score": round(float(score), 4),
            "density_score": round(float(density), 4),
            "block_anchor_count": anchor_count,
            "direct_hit_count": int(direct_hits[block_id]),
            "direct_matched_anchors": sorted(hits.get(block_id, set()) & direct_anchors),
            "matched_anchors": sorted(hits.get(block_id, set())),
            "text": str(block["text"]),
        })
    return out


def qualify_evidence(question: str, q_counter: Counter[str], candidates: list[dict[str, Any]], *, top_k: int) -> dict[str, Any]:
    """Gate retrieval candidates before they become answer-packet evidence.

    Retrieval says a block is nearby. This qualifier asks whether the block is
    allowed to answer. It is intentionally deterministic and receipt-heavy.
    """
    question_terms = [anchor for anchor in q_counter if anchor not in STOP_ANCHORS]
    required_terms = significant_question_terms(question_terms)
    path_intent = has_path_or_config_intent(question)
    unsupported_intent = len(required_terms) >= 4

    receipts: list[dict[str, Any]] = []
    qualified_rows: list[tuple[float, dict[str, Any]]] = []
    rejected: list[dict[str, Any]] = []

    for candidate in candidates:
        receipt = qualify_candidate(candidate, required_terms, path_intent, unsupported_intent)
        receipts.append(receipt)
        enriched = dict(candidate)
        enriched["qualification"] = receipt
        if receipt["qualified"]:
            qualified_rows.append((float(receipt["qualified_score"]), enriched))
        else:
            rejected.append(enriched)

    qualified_rows.sort(key=lambda item: (-item[0], -float(item[1].get("density_score", 0)), -float(item[1].get("score", 0))))
    locations = [item[1] for item in qualified_rows[:top_k]]
    support_state = "qualified_evidence" if locations else "no_qualified_evidence"
    return {
        "summary": {
            "schema": "awrag_evidence_qualification_summary@1",
            "support_state": support_state,
            "raw_candidate_count": len(candidates),
            "qualified_count": len(qualified_rows),
            "rejected_count": len(rejected),
            "required_terms": required_terms,
            "path_or_config_intent": path_intent,
        },
        "receipts": receipts,
        "locations": locations,
        "rejected": rejected[:top_k],
    }


def qualify_candidate(candidate: dict[str, Any], required_terms: list[str], path_intent: bool, unsupported_intent: bool) -> dict[str, Any]:
    text = str(candidate.get("text", ""))
    text_anchors = set(anchorize(text))
    direct = set(candidate.get("direct_matched_anchors") or [])
    covered = sorted(anchor for anchor in required_terms if anchor in text_anchors or anchor in direct)
    missing = sorted(anchor for anchor in required_terms if anchor not in covered)
    coverage = len(covered) / max(1, len(required_terms))
    heading_only = is_heading_only(text)
    broad_heading = heading_only and is_broad_heading(text)
    slash_phrase = contains_unqualified_slash_phrase(text)

    reject_reasons: list[str] = []
    if broad_heading:
        reject_reasons.append("section_heading_ambiguity")
    if heading_only and coverage < 0.75:
        reject_reasons.append("heading_without_content")
    if path_intent and slash_phrase and not contains_true_path_or_endpoint(text):
        reject_reasons.append("path_config_classifier_miss")
    if unsupported_intent and coverage < 0.50:
        reject_reasons.append("unsupported_refusal_threshold")
    if len(required_terms) >= 3 and coverage < 0.34:
        reject_reasons.append("predicate_object_coverage_miss")

    qualified = not reject_reasons
    score = (
        float(candidate.get("density_score", 0))
        + 8.0 * coverage
        + min(4.0, float(candidate.get("direct_hit_count", 0)))
        - (3.0 if heading_only else 0.0)
    )
    return {
        "schema": "awrag_candidate_qualification@1",
        "candidate": candidate.get("citation"),
        "qualified": qualified,
        "reject_reasons": reject_reasons,
        "covered_terms": covered,
        "missing_terms": missing[:20],
        "coverage": round(coverage, 4),
        "heading_only": heading_only,
        "broad_heading": broad_heading,
        "path_or_config_candidate": contains_true_path_or_endpoint(text),
        "qualified_score": round(score, 4),
    }


def significant_question_terms(anchors: list[str]) -> list[str]:
    low_value = STOP_ANCHORS | {
        "answer", "ask", "asked", "claim", "data", "dataset", "describe", "described",
        "evidence", "find", "found", "give", "local", "provide", "question", "row",
        "section", "show", "staged", "under", "value",
    }
    out: list[str] = []
    seen: set[str] = set()
    for anchor in anchors:
        if anchor in low_value:
            continue
        if len(anchor) == 1 and not anchor.isdigit():
            continue
        if anchor not in seen:
            out.append(anchor)
            seen.add(anchor)
    return out


def is_heading_only(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    return len(lines) == 1 and (lines[0].startswith("#") or len(lines[0]) <= 80)


def is_broad_heading(text: str) -> bool:
    stripped = text.strip().strip("#*` ").casefold()
    broad = {
        "conclusion", "discussion", "implemented", "next steps", "governance",
        "overview", "summary", "background", "results", "methods", "user upload",
        "what it opens", "citation integration", "citations pane",
    }
    return stripped in broad or stripped.startswith(("implemented", "next steps"))


def has_path_or_config_intent(question: str) -> bool:
    q = question.casefold()
    return any(token in q for token in ("path", "config", "endpoint", "api", "route", "url", "file"))


def contains_unqualified_slash_phrase(text: str) -> bool:
    return bool(re.search(r"\b[a-zA-Z]{2,}/[a-zA-Z]{2,}\b", text))


def contains_true_path_or_endpoint(text: str) -> bool:
    patterns = [
        r"[A-Za-z]:\\",
        r"[/\\][A-Za-z0-9_.-]+[/\\]",
        r"\bapi/[A-Za-z0-9_./{}-]+",
        r"/api/[A-Za-z0-9_./{}-]+",
        r"\b[A-Za-z0-9_.-]+\.(json|toml|yaml|yml|py|md|txt|csv)\b",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def write_lexicon(paths: DatasetPaths, db: sqlite3.Connection) -> None:
    anchors = [
        {
            "anchor": str(row["anchor"]),
            "symbol": str(row["symbol"]),
            "observations": int(row["observations"]),
            "scope": "dataset_local",
            "promotion_allowed": False,
        }
        for row in db.execute("select anchor, symbol, observations from anchors order by anchor")
    ]
    write_json(paths.lexicon_path, {
        "schema": "awrag_dataset_lexicon@1",
        "dataset_id": paths.root.name,
        "scope": "dataset_local",
        "anchor_count": len(anchors),
        "anchors": anchors,
    })


def write_citation_jsonl(paths: DatasetPaths, db: sqlite3.Connection) -> None:
    path = paths.citations / "citations.jsonl"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in db.execute("select * from citations order by citation_id"):
            handle.write(json.dumps(with_protected_notice({
                "schema": "awrag_citation@1",
                "citation_id": row["citation_id"],
                "marker": row["marker"],
                "file_path": row["file_path"],
                "line_start": row["line_start"],
                "line_end": row["line_end"],
                "text_hash": row["text_hash"],
                "scope": "dataset_local",
            }), ensure_ascii=True) + "\n")


def write_coordinate_index(paths: DatasetPaths, db: sqlite3.Connection) -> None:
    path = paths.coordinates / "coordinate_index.jsonl"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in db.execute("select block_id, file_path, line_start, line_end, citation_id from blocks order by file_path, line_start"):
            handle.write(json.dumps(with_protected_notice({
                "schema": "awrag_coordinate@1",
                "block_id": row["block_id"],
                "file_path": row["file_path"],
                "line_start": row["line_start"],
                "line_end": row["line_end"],
                "citation_id": row["citation_id"],
                "scope": "dataset_local",
            }), ensure_ascii=True) + "\n")


def scalar(db: sqlite3.Connection, sql: str) -> int:
    row = db.execute(sql).fetchone()
    return int(row[0]) if row else 0


def public_paths(paths: DatasetPaths) -> dict[str, str]:
    return {
        "dataset_root": str(paths.root),
        "counts": str(paths.sqlite_path),
        "lexicon": str(paths.lexicon_path),
        "coordinates": str(paths.coordinates),
        "citations": str(paths.citations),
        "outputs": str(paths.outputs),
        "receipts": str(paths.receipts),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(with_protected_notice(payload), ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def protected_notice() -> dict[str, Any]:
    return {
        "copyright": COPYRIGHT,
        "owner": "Cortex Evolved Systems",
        "license": LICENSE_REF,
        "watermark": WATERMARK,
        "facsimile_warning": FACSIMILE_WARNING,
        "watermark_locked": True,
        "removal_prohibited": True,
    }


def with_protected_notice(payload: dict[str, Any]) -> dict[str, Any]:
    protected = protected_notice()
    protected.update(payload)
    for key, value in protected_notice().items():
        protected[key] = value
    return protected


def sha1_text(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8", errors="replace")).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def unique_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")

