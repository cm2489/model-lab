"""Validate Model Lab content files against content/SCHEMA.md.

Run from the repo root:  uv run python scripts/validate_content.py [--root PATH]

Checks content/labs.json, content/cards.json, foundations/cards.json and
progress.json. Prints one line per problem and exits 1 if there is any.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

STATUSES = {"planned", "draft", "ready"}
WHERES = {"laptop", "phone", "hosted"}
FOUNDATIONS = "foundations"
MAX_CORE_WORDS = 25

LAB_KEYS = ("id", "number", "title", "aim", "artifact", "est_minutes", "doc", "status", "steps")
STEP_KEYS = ("id", "title", "minutes", "where", "anchor")
CARD_KEYS = ("id", "lab", "after_step", "concept", "type", "front", "back")


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _nonempty_str(v) -> bool:
    return isinstance(v, str) and v.strip() != ""


def load_json(path: Path, errors: list[str], rel: str):
    """Return parsed JSON or None (after recording an error)."""
    if not path.is_file():
        errors.append(f"{rel}: file not found")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        errors.append(f"{rel}: not valid JSON ({exc})")
        return None


def slugify(heading: str) -> str:
    """GitHub-style heading anchor."""
    text = re.sub(r"<[^>]+>", "", heading)
    text = re.sub(r"[`*_\[\]()]", "", text).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text, flags=re.UNICODE)
    return text.replace(" ", "-")


def doc_anchors(text: str) -> tuple[set[str], set[str]]:
    """Return (explicit anchors, heading slugs) found in a Markdown document."""
    explicit = set(re.findall(r"""<a\s+[^>]*?(?:id|name)\s*=\s*["']([^"']+)["']""", text))
    explicit |= set(re.findall(r"\{#([A-Za-z0-9_\-]+)\}", text))
    slugs = set()
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        m = None if in_fence else re.match(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$", line)
        if m:
            heading = re.sub(r"\s*\{#[^}]*\}\s*$", "", m.group(1))
            slugs.add(slugify(heading))
    return explicit, slugs


def anchor_present(anchor: str, explicit: set[str], slugs: set[str]) -> bool:
    # A heading "Step 1: Install" slugs to "step-1-install"; accept it for anchor "step-1".
    return anchor in explicit or anchor in slugs or any(s.startswith(anchor + "-") for s in slugs)


def check_labs(root: Path, errors: list[str]) -> tuple[set[str], set[str]]:
    rel = "content/labs.json"
    data = load_json(root / rel, errors, rel)
    lab_ids: set[str] = set()
    step_ids: set[str] = set()
    if data is None:
        return lab_ids, step_ids
    if not isinstance(data, dict):
        errors.append(f"{rel}: top level must be an object")
        return lab_ids, step_ids
    track = data.get("track")
    if not isinstance(track, dict) or not _nonempty_str(track.get("id")) or not _nonempty_str(track.get("title")):
        errors.append(f"{rel}: 'track' must be an object with non-empty 'id' and 'title'")
    labs = data.get("labs")
    if not isinstance(labs, list) or not labs:
        errors.append(f"{rel}: 'labs' must be a non-empty list")
        return lab_ids, step_ids

    for i, lab in enumerate(labs):
        where = f"{rel}: labs[{i}]"
        if not isinstance(lab, dict):
            errors.append(f"{where}: must be an object")
            continue
        lid = lab.get("id")
        if _nonempty_str(lid):
            where = f"{rel}: lab '{lid}'"
        for key in LAB_KEYS:
            if key not in lab:
                errors.append(f"{where}: missing key '{key}'")
        if _nonempty_str(lid):
            if lid in lab_ids:
                errors.append(f"{where}: duplicate lab id")
            lab_ids.add(lid)
        elif "id" in lab:
            errors.append(f"{where}: 'id' must be a non-empty string")
        for key in ("title", "aim", "doc"):
            if key in lab and not _nonempty_str(lab[key]):
                errors.append(f"{where}: '{key}' must be a non-empty string")
        if "number" in lab and not _is_int(lab["number"]):
            errors.append(f"{where}: 'number' must be an integer")
        art = lab.get("artifact")
        if "artifact" in lab and (not isinstance(art, dict) or not _nonempty_str(art.get("title"))
                                  or not isinstance(art.get("public"), bool)):
            errors.append(f"{where}: 'artifact' must be an object with a 'title' string and a 'public' boolean")
        status = lab.get("status")
        if "status" in lab and status not in STATUSES:
            errors.append(f"{where}: status {status!r} must be one of {sorted(STATUSES)}")
        est = lab.get("est_minutes")
        if "est_minutes" in lab and not _is_int(est):
            errors.append(f"{where}: 'est_minutes' must be an integer")

        steps = lab.get("steps")
        if "steps" in lab and (not isinstance(steps, list) or not steps):
            errors.append(f"{where}: 'steps' must be a non-empty list")
            steps = None
        total = 0
        sum_ok = isinstance(steps, list)
        anchors: list[tuple[str, str]] = []
        for j, step in enumerate(steps or []):
            sw = f"{where}, steps[{j}]"
            if not isinstance(step, dict):
                errors.append(f"{sw}: must be an object")
                sum_ok = False
                continue
            sid = step.get("id")
            if _nonempty_str(sid):
                sw = f"{where}, step '{sid}'"
            for key in STEP_KEYS:
                if key not in step:
                    errors.append(f"{sw}: missing key '{key}'")
            if _nonempty_str(sid):
                if sid in step_ids:
                    errors.append(f"{sw}: duplicate step id")
                step_ids.add(sid)
                if _nonempty_str(lid) and not sid.startswith(lid + "."):
                    errors.append(f"{sw}: step id must start with its lab id '{lid}.'")
            elif "id" in step:
                errors.append(f"{sw}: 'id' must be a non-empty string")
            if "title" in step and not _nonempty_str(step["title"]):
                errors.append(f"{sw}: 'title' must be a non-empty string")
            mins = step.get("minutes")
            if "minutes" in step:
                if _is_int(mins) and mins >= 0:
                    total += mins
                else:
                    errors.append(f"{sw}: 'minutes' must be a non-negative integer")
                    sum_ok = False
            else:
                sum_ok = False
            if "where" in step and step["where"] not in WHERES:
                errors.append(f"{sw}: where {step['where']!r} must be one of {sorted(WHERES)}")
            if "anchor" in step and not _nonempty_str(step["anchor"]):
                errors.append(f"{sw}: 'anchor' must be a non-empty string")
            elif _nonempty_str(step.get("anchor")):
                anchors.append((step.get("id", f"steps[{j}]"), step["anchor"]))
        if sum_ok and _is_int(est) and est != total:
            errors.append(f"{where}: est_minutes is {est} but its steps add up to {total}")

        if status in ("draft", "ready") and _nonempty_str(lab.get("doc")):
            doc_path = root / lab["doc"]
            if not doc_path.is_file():
                errors.append(f"{where}: status is '{status}' but doc '{lab['doc']}' does not exist")
            else:
                explicit, slugs = doc_anchors(doc_path.read_text(encoding="utf-8"))
                for sid, anchor in anchors:
                    if not anchor_present(anchor, explicit, slugs):
                        errors.append(f"{where}: step '{sid}' anchor '{anchor}' has no heading or explicit anchor in {lab['doc']}")
    return lab_ids, step_ids


def check_cards(root: Path, rel: str, lab_ids: set[str], step_ids: set[str],
                seen: dict[str, str], errors: list[str]) -> None:
    data = load_json(root / rel, errors, rel)
    if data is None:
        return
    if not isinstance(data, list):
        errors.append(f"{rel}: top level must be a list")
        return
    for i, card in enumerate(data):
        where = f"{rel}: cards[{i}]"
        if not isinstance(card, dict):
            errors.append(f"{where}: must be an object")
            continue
        cid = card.get("id")
        if _nonempty_str(cid):
            where = f"{rel}: card '{cid}'"
        for key in CARD_KEYS:
            if key not in card:
                errors.append(f"{where}: missing key '{key}'")
        if _nonempty_str(cid):
            if cid in seen:
                errors.append(f"{where}: duplicate card id (also in {seen[cid]})")
            else:
                seen[cid] = rel
        elif "id" in card:
            errors.append(f"{where}: 'id' must be a non-empty string")
        lab = card.get("lab")
        if "lab" in card and not (lab == FOUNDATIONS or lab in lab_ids):
            errors.append(f"{where}: lab {lab!r} is not a lab id or '{FOUNDATIONS}'")
        step = card.get("after_step")
        if "after_step" in card and step is not None and step not in step_ids:
            errors.append(f"{where}: after_step {step!r} is not null or a real step id")
        for key in ("concept", "type", "front", "back"):
            if key in card and not _nonempty_str(card[key]):
                errors.append(f"{where}: '{key}' must be a non-empty string")
        back = card.get("back")
        if card.get("type") == "core" and _nonempty_str(back):
            words = len(back.split())
            if words > MAX_CORE_WORDS:
                errors.append(f"{where}: core card back has {words} words (max {MAX_CORE_WORDS})")


def parse_timestamp(value, where: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{where}: timestamp must be a string")
        return
    try:
        stamp = datetime.fromisoformat(value)
    except ValueError:
        errors.append(f"{where}: {value!r} is not an ISO 8601 timestamp")
        return
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        errors.append(f"{where}: {value!r} has no UTC offset (write e.g. -04:00)")


def parse_date(value, where: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{where}: date must be a string")
        return
    try:
        date.fromisoformat(value)
    except ValueError:
        errors.append(f"{where}: {value!r} is not a YYYY-MM-DD date")


def check_progress(root: Path, lab_ids: set[str], step_ids: set[str], errors: list[str]) -> None:
    rel = "progress.json"
    data = load_json(root / rel, errors, rel)
    if data is None:
        return
    if not isinstance(data, dict):
        errors.append(f"{rel}: top level must be an object")
        return
    for key in ("updated", "steps", "sessions", "artifacts"):
        if key not in data:
            errors.append(f"{rel}: missing key '{key}'")
    if data.get("updated") is not None and "updated" in data:
        parse_timestamp(data["updated"], f"{rel}: 'updated'", errors)

    steps = data.get("steps", {})
    if not isinstance(steps, dict):
        errors.append(f"{rel}: 'steps' must be an object")
    else:
        for sid, rec in steps.items():
            where = f"{rel}: steps['{sid}']"
            if sid not in step_ids:
                errors.append(f"{where}: unknown step id")
            if not isinstance(rec, dict):
                errors.append(f"{where}: must be an object")
                continue
            for key in ("done", "minutes", "note"):
                if key not in rec:
                    errors.append(f"{where}: missing key '{key}'")
            if "done" in rec:
                parse_timestamp(rec["done"], f"{where}: 'done'", errors)
            if "minutes" in rec and not (_is_int(rec["minutes"]) and rec["minutes"] >= 0):
                errors.append(f"{where}: 'minutes' must be a non-negative integer")
            if "note" in rec and not isinstance(rec["note"], str):
                errors.append(f"{where}: 'note' must be a string")

    sessions = data.get("sessions", [])
    if not isinstance(sessions, list):
        errors.append(f"{rel}: 'sessions' must be a list")
    else:
        for i, sess in enumerate(sessions):
            where = f"{rel}: sessions[{i}]"
            if not isinstance(sess, dict):
                errors.append(f"{where}: must be an object")
                continue
            for key in ("date", "minutes", "steps"):
                if key not in sess:
                    errors.append(f"{where}: missing key '{key}'")
            if "date" in sess:
                parse_date(sess["date"], f"{where}: 'date'", errors)
            if "minutes" in sess and not (_is_int(sess["minutes"]) and sess["minutes"] >= 0):
                errors.append(f"{where}: 'minutes' must be a non-negative integer")
            if "steps" in sess:
                if not isinstance(sess["steps"], list):
                    errors.append(f"{where}: 'steps' must be a list")
                else:
                    for sid in sess["steps"]:
                        if sid not in step_ids:
                            errors.append(f"{where}: unknown step id {sid!r}")

    artifacts = data.get("artifacts", [])
    if not isinstance(artifacts, list):
        errors.append(f"{rel}: 'artifacts' must be a list")
    else:
        for i, art in enumerate(artifacts):
            where = f"{rel}: artifacts[{i}]"
            if not isinstance(art, dict):
                errors.append(f"{where}: must be an object")
                continue
            for key in ("lab", "title", "url", "shipped"):
                if key not in art:
                    errors.append(f"{where}: missing key '{key}'")
            if "lab" in art and art["lab"] not in lab_ids:
                errors.append(f"{where}: unknown lab id {art['lab']!r}")
            for key in ("title", "url"):
                if key in art and not _nonempty_str(art[key]):
                    errors.append(f"{where}: '{key}' must be a non-empty string")
            if "shipped" in art:
                parse_date(art["shipped"], f"{where}: 'shipped'", errors)


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    lab_ids, step_ids = check_labs(root, errors)
    seen: dict[str, str] = {}
    for rel in ("content/cards.json", "foundations/cards.json"):
        check_cards(root, rel, lab_ids, step_ids, seen, errors)
    check_progress(root, lab_ids, step_ids, errors)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="repo root (default: current directory)")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    errors = validate(root)
    if errors:
        for line in errors:
            print(f"ERROR {line}")
        print(f"\n{len(errors)} problem(s) found.", file=sys.stderr)
        return 1
    print("Content OK: labs.json, cards.json, foundations/cards.json, progress.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
