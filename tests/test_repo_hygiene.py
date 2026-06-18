from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_public_repo_has_no_hard_coded_local_paths() -> None:
    slash = "\\"
    forbidden = [
        "C:" + slash,
        "D:" + slash,
        "E:" + slash,
        "/" + "Users" + "/",
        "/" + "home" + "/",
        "AnchorWorks" + "_Clean_Runtime",
        "AnchorWorks" + "_Local_Runtime",
        "my" + "dyi",
        "LEX" + "AR",
    ]
    offenders: list[str] = []
    for path in REPO_ROOT.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        if path.suffix.lower() not in {".py", ".md", ".txt", ".toml", ".json", ".yml", ".yaml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for needle in forbidden:
            if needle in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {needle}")

    assert offenders == []
