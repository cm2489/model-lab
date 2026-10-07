"""Small file helpers shared by the CLI tools."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
SPLITS = {
    "golden": ROOT / "evals" / "golden.jsonl",
    "valid": ROOT / "data" / "valid.jsonl",
    "train": ROOT / "data" / "train.jsonl",
}


def read_jsonl(path: str | Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def now_et() -> str:
    return datetime.now(ZoneInfo("America/New_York")).isoformat(timespec="seconds")


def git_commit(root: Path = ROOT) -> str:
    """Short commit hash, with "-dirty" when tracked files outside results/ have uncommitted changes.

    results/ is ignored because every run rewrites results/README.md. A "-dirty"
    stamp therefore means the code, prompt or data differed from that commit,
    so the run cannot be reproduced from the commit alone.
    """
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root,
                             capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no", "--", ".", ":!results"],
                               cwd=root, capture_output=True, text=True).stdout.strip()
        return sha + ("-dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
