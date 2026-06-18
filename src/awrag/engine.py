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
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?|[^\sA-Za-z0-9]", re.UNICODE)


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
            "copyright": COPYRIGHT,
            "watermark": WATERMARK,
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
            "copyright": COPYRIGHT,
            "watermark": WATERMARK,
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
        "copyright": COPYRIGHT,
        "watermark": WATERMARK,
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
    receipt_path = paths.receipts / f"intake_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    write_json(receipt_path, receipt)
    receipt["receipt_path"] = str(receipt_path)
    return receipt


def query(runtime_root: str | Path, dataset_id: str, question: str, *, top_k: int = 5) -> dict[str, Any]:
    paths = dataset_paths(runtime_root, dataset_id)
    ensure_dataset(runtime_root, dataset_id)
    q_anchors = anchorize(question)
    if not q_anchors:
        raise ValueError("question produced no anchors")
    q_counter = Counter(q_anchors)

    with connect(paths.sqlite_path) as db:
        init_db(db)
        relation_neighbors = top_relation_neighbors(db, q_counter, limit=16)
        candidate_blocks = score_blocks(db, q_counter, relation_neighbors, top_k=top_k)

    output = {
        "schema": "awrag_query_result@1",
        "created_at": utc_now(),
        "copyright": COPYRIGHT,
        "watermark": WATERMARK,
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
            "locations": candidate_blocks,
        },
    }
    output_path = paths.outputs / f"query_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    write_json(output_path, output)
    output["output_path"] = str(output_path)
    return output


def status(runtime_root: str | Path, dataset_id: str) -> dict[str, Any]:
    paths = dataset_paths(runtime_root, dataset_id)
    with connect(paths.sqlite_path) as db:
        init_db(db)
        anchors = scalar(db, "select count(*) from anchors")
        relations = scalar(db, "select count(*) from relations")
        blocks = scalar(db, "select count(*) from blocks")
        citations = scalar(db, "select count(*) from citations")
    return {
        "schema": "awrag_dataset_status@1",
        "copyright": COPYRIGHT,
        "watermark": WATERMARK,
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
    }


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
            blocks.append({"line_start": start, "line_end": index - 1, "text": "\n".join(current)})
            current = []
    if current:
        blocks.append({"line_start": start, "line_end": len(lines), "text": "\n".join(current)})
    if not blocks and text:
        blocks.append({"line_start": 1, "line_end": max(1, len(lines)), "text": text})
    return blocks


def anchorize(text: str) -> list[str]:
    anchors: list[str] = []
    for match in WORD_RE.finditer(text):
        value = match.group(0).strip().casefold()
        if not value:
            continue
        if value.isalnum() and any(ch.isalpha() for ch in value) and any(ch.isdigit() for ch in value):
            anchors.extend(ch for ch in value if ch.isalnum())
        elif value.isalpha() and len(value) >= 3 and len(value) <= 8 and not any(ch in "aeiou" for ch in value):
            anchors.extend(value)
        else:
            anchors.append(value)
    return anchors


def symbol_for(anchor: str) -> str:
    return "0x" + sha1_text(anchor)[:10].upper()


def top_relation_neighbors(db: sqlite3.Connection, q_counter: Counter[str], *, limit: int) -> list[dict[str, Any]]:
    scores: Counter[str] = Counter()
    for anchor, weight in q_counter.items():
        for row in db.execute("select neighbor, sum(observations) as observations from relations where anchor=? group by neighbor", (anchor,)):
            scores[str(row["neighbor"])] += int(row["observations"]) * weight
    return [{"anchor": anchor, "score": score} for anchor, score in scores.most_common(limit)]


def score_blocks(db: sqlite3.Connection, q_counter: Counter[str], relation_neighbors: list[dict[str, Any]], *, top_k: int) -> list[dict[str, Any]]:
    weights = Counter(q_counter)
    for index, row in enumerate(relation_neighbors):
        weights[str(row["anchor"])] += max(1, 8 - index // 2)
    block_scores: Counter[str] = Counter()
    hits: dict[str, set[str]] = {}
    for anchor, weight in weights.items():
        for row in db.execute("select distinct block_id from block_anchors where anchor=?", (anchor,)):
            block_id = str(row["block_id"])
            block_scores[block_id] += weight
            hits.setdefault(block_id, set()).add(anchor)
    out: list[dict[str, Any]] = []
    for block_id, score in block_scores.most_common(top_k):
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
            "score": int(score),
            "matched_anchors": sorted(hits.get(block_id, set())),
            "text": str(block["text"]),
        })
    return out


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
        "copyright": COPYRIGHT,
        "watermark": WATERMARK,
        "dataset_id": paths.root.name,
        "scope": "dataset_local",
        "anchor_count": len(anchors),
        "anchors": anchors,
    })


def write_citation_jsonl(paths: DatasetPaths, db: sqlite3.Connection) -> None:
    path = paths.citations / "citations.jsonl"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in db.execute("select * from citations order by citation_id"):
            handle.write(json.dumps({
                "schema": "awrag_citation@1",
                "copyright": COPYRIGHT,
                "watermark": WATERMARK,
                "citation_id": row["citation_id"],
                "marker": row["marker"],
                "file_path": row["file_path"],
                "line_start": row["line_start"],
                "line_end": row["line_end"],
                "text_hash": row["text_hash"],
                "scope": "dataset_local",
            }, ensure_ascii=True) + "\n")


def write_coordinate_index(paths: DatasetPaths, db: sqlite3.Connection) -> None:
    path = paths.coordinates / "coordinate_index.jsonl"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in db.execute("select block_id, file_path, line_start, line_end, citation_id from blocks order by file_path, line_start"):
            handle.write(json.dumps({
                "schema": "awrag_coordinate@1",
                "copyright": COPYRIGHT,
                "watermark": WATERMARK,
                "block_id": row["block_id"],
                "file_path": row["file_path"],
                "line_start": row["line_start"],
                "line_end": row["line_end"],
                "citation_id": row["citation_id"],
                "scope": "dataset_local",
            }, ensure_ascii=True) + "\n")


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
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def sha1_text(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8", errors="replace")).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

