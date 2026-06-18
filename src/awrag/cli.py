from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import COPYRIGHT, WATERMARK, ensure_dataset, intake, query, status


def main() -> None:
    parser = argparse.ArgumentParser(prog="awrag")
    parser.add_argument("--version", action="version", version="awrag 0.1.0")
    sub = parser.add_subparsers(dest="command", required=True)

    init_cmd = sub.add_parser("init", help="Create a dataset-local AWRAG scope")
    init_cmd.add_argument("--runtime-root", type=Path, required=True)
    init_cmd.add_argument("--dataset-id", required=True)
    init_cmd.add_argument("--owner", default="operator_defined")

    intake_cmd = sub.add_parser("intake", help="Build dataset-local lexicon, counts, coordinates, and citations")
    intake_cmd.add_argument("--runtime-root", type=Path, required=True)
    intake_cmd.add_argument("--dataset-id", required=True)
    intake_cmd.add_argument("--source", type=Path, required=True)
    intake_cmd.add_argument("--owner", default="operator_defined")
    intake_cmd.add_argument("--window", type=int, default=6)

    status_cmd = sub.add_parser("status", help="Show dataset-local status")
    status_cmd.add_argument("--runtime-root", type=Path, required=True)
    status_cmd.add_argument("--dataset-id", required=True)

    query_cmd = sub.add_parser("query", help="Return a cited local answer packet from dataset coordinates")
    query_cmd.add_argument("--runtime-root", type=Path, required=True)
    query_cmd.add_argument("--dataset-id", required=True)
    query_cmd.add_argument("--question", required=True)
    query_cmd.add_argument("--top-k", type=int, default=5)

    args = parser.parse_args()
    if args.command == "init":
        result = ensure_dataset(args.runtime_root, args.dataset_id, owner=args.owner)
    elif args.command == "intake":
        result = intake(args.runtime_root, args.dataset_id, args.source, owner=args.owner, window=args.window)
    elif args.command == "status":
        result = status(args.runtime_root, args.dataset_id)
    elif args.command == "query":
        result = query(args.runtime_root, args.dataset_id, args.question, top_k=args.top_k)
    else:
        parser.error("unknown command")

    result.setdefault("copyright", COPYRIGHT)
    result.setdefault("watermark", WATERMARK)
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()

