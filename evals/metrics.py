"""Scoring. Pure functions, standard library only, so CI needs nothing installed.

An invalid reply (no parseable label) always counts as wrong. It is never dropped.
"""

from __future__ import annotations

import collections
import math

INVALID = "INVALID"


def join(golden: list[dict], predictions: list[dict]) -> list[dict]:
    """Line up predictions with the golden set by id.

    The gold label always comes from the golden file, never from the
    predictions file, so a predictions file cannot grade itself.
    A golden example with no prediction counts as invalid.
    Duplicate prediction ids are rejected: which answer would count is ambiguous,
    and a second row could quietly replace a wrong answer with a right one.
    """
    seen, dupes = set(), set()
    for p in predictions:
        (dupes if p["id"] in seen else seen).add(p["id"])
    if dupes:
        raise ValueError(f"duplicate prediction ids: {', '.join(sorted(dupes)[:5])}")
    by_id = {p["id"]: p for p in predictions}
    rows = []
    for g in golden:
        p = by_id.get(g["id"], {})
        rows.append({**p, "id": g["id"], "gold": g["label"], "pred": p.get("pred")})
    return rows


def percentile(values: list[float], q: float) -> float | None:
    """Linear-interpolated percentile, q in [0, 100]."""
    if not values:
        return None
    v = sorted(values)
    k = (len(v) - 1) * q / 100
    lo, hi = math.floor(k), math.ceil(k)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


def classification(rows: list[dict]) -> dict:
    n = len(rows)
    correct = sum(1 for r in rows if r["pred"] == r["gold"])
    invalid = sum(1 for r in rows if r["pred"] is None)

    labels = sorted({r["gold"] for r in rows} | {r["pred"] for r in rows if r["pred"]})
    per_label = {}
    for lab in labels:
        tp = sum(1 for r in rows if r["pred"] == lab and r["gold"] == lab)
        fp = sum(1 for r in rows if r["pred"] == lab and r["gold"] != lab)
        fn = sum(1 for r in rows if r["gold"] == lab and r["pred"] != lab)
        p = tp / (tp + fp) if tp + fp else 0.0
        rcl = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * p * rcl / (p + rcl) if p + rcl else 0.0
        per_label[lab] = {"precision": round(p, 4), "recall": round(rcl, 4), "f1": round(f1, 4),
                          "support": tp + fn}

    mistakes = collections.Counter((r["gold"], r["pred"] or INVALID) for r in rows if r["pred"] != r["gold"])
    return {
        "n": n,
        "correct": correct,
        "accuracy": round(correct / n, 4) if n else 0.0,
        "macro_f1": round(sum(x["f1"] for x in per_label.values()) / len(per_label), 4) if per_label else 0.0,
        "invalid": invalid,
        "invalid_rate": round(invalid / n, 4) if n else 0.0,
        "per_label": per_label,
        "top_confusions": [{"gold": g, "pred": p, "count": c} for (g, p), c in mistakes.most_common(10)],
    }


def stops(rows: list[dict]) -> dict:
    """How each reply ended ("stop", "end_turn", "max_tokens", "refusal", ...)."""
    return dict(collections.Counter(str(r.get("stop")) for r in rows if r.get("stop") is not None))


def speed(rows: list[dict]) -> dict:
    lat = [r["latency_s"] for r in rows if r.get("latency_s") is not None]
    tps = [r["gen_tps"] for r in rows if r.get("gen_tps")]
    return {
        "latency_p50_s": round(percentile(lat, 50), 3) if lat else None,
        "latency_p90_s": round(percentile(lat, 90), 3) if lat else None,
        "tokens_per_second": round(percentile(tps, 50), 1) if tps else None,
    }


def cost(rows: list[dict], price_in: float | None, price_out: float | None, local: bool) -> dict:
    """Cost per 1,000 bills from the measured token counts.

    Prices are US dollars per million tokens, passed on the command line.
    Nothing is hard-coded: prices change, and a stale price is a wrong number.
    """
    n = len(rows)
    tin = sum(r.get("input_tokens") or 0 for r in rows)
    tout = sum(r.get("output_tokens") or 0 for r in rows)
    out = {"input_tokens": tin, "output_tokens": tout,
           "avg_input_tokens": round(tin / n, 1) if n else 0.0,
           "avg_output_tokens": round(tout / n, 1) if n else 0.0,
           "price_in_per_mtok": price_in, "price_out_per_mtok": price_out}
    if price_in is not None and price_out is not None and n:
        out["cost_per_1k_usd"] = round((tin * price_in + tout * price_out) / 1e6 / n * 1000, 4)
        out["cost_note"] = "measured tokens x prices given on the command line"
    elif local:
        out["cost_per_1k_usd"] = 0.0
        out["cost_note"] = "local run: $0 marginal cost (hardware and electricity not counted)"
    else:
        out["cost_per_1k_usd"] = None
        out["cost_note"] = "no prices given: pass --price-in and --price-out (USD per million tokens)"
    return out
