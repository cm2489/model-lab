"""Score a model on a split and write the results.

Examples:
  uv run python -m evals.run --backend mlx --model mlx-community/Qwen3.5-4B-4bit --split golden
  uv run python -m evals.run --backend anthropic --model claude-opus-5-5 --split golden \\
      --price-in 4 --price-out 20
  uv run python -m evals.run --backend predictions --predictions results/<run>/predictions.jsonl

Writes results/<run-name>/predictions.jsonl, metrics.json and score.md,
then rebuilds the table in results/README.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

from evals import metrics, report
from evals.files import ROOT, SPLITS, git_commit, now_et, read_jsonl
from evals.labels import LABELS
from evals.prompt import PROMPT_VERSION, build_messages, parse_label


def make_backend(args):
    if args.backend == "mlx":
        from evals.backends import MlxBackend

        return MlxBackend(args.model, max_tokens=args.max_tokens or 32, thinking=args.thinking)
    if args.backend == "anthropic":
        from evals.backends import AnthropicBackend

        effort = None if args.effort == "none" else args.effort
        return AnthropicBackend(args.model, max_tokens=max_tokens(args), effort=effort)
    raise ValueError(args.backend)


API_BACKENDS = {"anthropic"}
DEFAULT_MAX_TOKENS = {"mlx": 32, "anthropic": 512}


def max_tokens(args) -> int:
    return args.max_tokens or DEFAULT_MAX_TOKENS[args.backend]


def input_tokens_estimate(title: str) -> int:
    """A deliberately high guess of a prompt's input tokens: 1 token per 3 characters, plus 50.

    English runs nearer 4 characters per token, so real counts should come in lower.
    """
    return len(build_messages(title)[0]["content"]) // 3 + 50


def worst_case_usd(examples: list[dict], max_tokens: int, price_in: float, price_out: float) -> float:
    """The most a run can cost: every reply uses all of max_tokens (thinking included)."""
    tokens_in = sum(input_tokens_estimate(ex["title"]) for ex in examples)
    tokens_out = max_tokens * len(examples)
    return (tokens_in * price_in + tokens_out * price_out) / 1e6


# The prices the lab page documents, USD per million tokens (input, output).
# Used only to warn when you run a model the page did not price. Not used to bill.
DOCUMENTED_PRICES = {
    "claude-opus-5-5": (4.0, 20.0),
}
MAX_API_ROWS = 500  # an API run over this many bills needs --allow-large


def price_warning(model: str, price_in: float, price_out: float) -> str | None:
    """A one-line warning when the model or prices differ from what the lab page documents."""
    documented = DOCUMENTED_PRICES.get(model)
    if documented is None:
        return (f"warning: the lab page has no prices for {model}. The spend guard is only as good "
                "as the --price-in and --price-out you pass.")
    if (price_in, price_out) != documented:
        return (f"warning: the lab page documents ${documented[0]:g} / ${documented[1]:g} per million tokens "
                f"for {model}; you passed ${price_in:g} / ${price_out:g}. Check today's prices.")
    return None


def spend_guard(args, examples: list[dict], split_name: str) -> float:
    """Refuse a paid run that could cost more than --max-usd, or that is too big.

    It protects you only when you pass the real prices. Returns the worst-case
    estimate. Exits with an error before any request is sent.
    """
    if args.price_in is None or args.price_out is None:
        sys.exit("error: API runs need --price-in and --price-out (USD per million tokens), so the cost can be capped")
    if args.price_in <= 0 or args.price_out <= 0:
        sys.exit("error: --price-in and --price-out must be above zero. A zero price would switch the spend guard off.")
    if args.max_usd is None:
        sys.exit("error: API runs need --max-usd, the most you agree to spend on this run")
    if split_name in ("train", "valid") and not args.allow_large:
        sys.exit(f"error: refusing to send the {split_name} split ({len(examples)} bills) to a paid API. "
                 "Pass --allow-large if you really mean it.")
    if len(examples) > MAX_API_ROWS and not args.allow_large:
        sys.exit(f"error: refusing to send {len(examples)} bills to a paid API (limit {MAX_API_ROWS}). "
                 "Use --limit, or pass --allow-large if you really mean it.")
    warning = price_warning(args.model, args.price_in, args.price_out)
    if warning:
        print(warning, file=sys.stderr)
    worst = worst_case_usd(examples, max_tokens(args), args.price_in, args.price_out)
    print(f"spend guard: {len(examples)} bills, max_tokens {max_tokens(args)}, no retries, worst case ${worst:.2f}, "
          f"cap ${args.max_usd:.2f}", file=sys.stderr)
    if worst > args.max_usd:
        sys.exit(f"error: worst case ${worst:.2f} is over --max-usd ${args.max_usd:.2f}. "
                 "Lower --limit or --max-tokens, or raise --max-usd.")
    return worst


def predict_all(backend, examples: list[dict], out_path: Path, model: str) -> list[dict]:
    """Run the model on every example. Writes each prediction as soon as it exists."""
    rows = []
    with open(out_path, "w") as f:
        for i, ex in enumerate(examples, 1):
            t0 = time.perf_counter()
            r = backend(build_messages(ex["title"]))
            latency = time.perf_counter() - t0
            pred, how = parse_label(r["raw"])
            row = {"id": ex["id"], "title": ex["title"], "gold": ex["label"], "pred": pred, "parse": how,
                   "raw": r["raw"], "latency_s": round(latency, 4), "input_tokens": r["input_tokens"],
                   "output_tokens": r["output_tokens"], "gen_tps": r["gen_tps"], "stop": r["stop"],
                   "model": model}
            rows.append(row)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            mark = "ok " if pred == ex["label"] else ("INV" if pred is None else "x  ")
            print(f"[{i}/{len(examples)}] {mark} {latency:5.2f}s {ex['id']:<14} gold={ex['label']} | pred={pred}",
                  file=sys.stderr)
    return rows


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9.]+", "-", text.lower().split("/")[-1]).strip("-")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", required=True, choices=["mlx", "anthropic", "predictions"])
    ap.add_argument("--model", help="model id (required for mlx and anthropic)")
    ap.add_argument("--split", default="golden", choices=sorted(SPLITS))
    ap.add_argument("--data", help="score this JSONL file instead of a named split")
    ap.add_argument("--predictions", help="predictions backend: the predictions.jsonl to score")
    ap.add_argument("--run-name", help="folder name under results/ (default: model-split-date)")
    ap.add_argument("--results-dir", default=str(ROOT / "results"))
    ap.add_argument("--limit", type=int, help="only the first N examples (for a quick smoke test)")
    ap.add_argument("--price-in", type=float, help="USD per million input tokens")
    ap.add_argument("--price-out", type=float, help="USD per million output tokens")
    ap.add_argument("--max-tokens", type=int, help="reply length cap, thinking included (default: mlx 32, anthropic 512)")
    ap.add_argument("--thinking", action="store_true", help="mlx: let the model think first (off by default)")
    ap.add_argument("--effort", default="low", help="anthropic: low|medium|high|xhigh|max, or none to omit")
    ap.add_argument("--max-usd", type=float, help="API runs (required): refuse to start if the worst case is above this")
    ap.add_argument("--allow-large", action="store_true", help="API runs: allow the train or valid split")
    args = ap.parse_args(argv)

    data_path = Path(args.data) if args.data else SPLITS[args.split]
    split_name = Path(args.data).stem if args.data else args.split
    examples = read_jsonl(data_path)
    if args.limit:
        examples = examples[: args.limit]

    date = now_et()
    if args.backend == "predictions":
        if not args.predictions:
            ap.error("--predictions is required with --backend predictions")
        saved = read_jsonl(args.predictions)
        model = args.model or (saved[0].get("model") if saved else None) or "unknown"
    else:
        if not args.model:
            ap.error("--model is required with --backend mlx or anthropic")
        model = args.model
        if args.backend in API_BACKENDS:
            spend_guard(args, examples, split_name)  # before anything is written or sent

    run_name = args.run_name or f"{slug(model)}-{split_name}-{date[:16].replace(':', '').replace('T', '-')}"
    run_dir = Path(args.results_dir) / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    pred_path = run_dir / "predictions.jsonl"

    t0 = time.perf_counter()
    if args.backend == "predictions":
        known = set(LABELS)
        saved = [{**p, "pred": p.get("pred") if p.get("pred") in known else None} for p in saved]
        rows = metrics.join(examples, saved)
        if Path(args.predictions).resolve() != pred_path.resolve():
            pred_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
        local = False
    else:
        backend = make_backend(args)
        rows = predict_all(backend, examples, pred_path, model)
        local = backend.local
    wall = time.perf_counter() - t0

    meta = {"run_name": run_name, "backend": args.backend, "model": model, "split": split_name,
            "data": str(data_path.relative_to(ROOT)) if data_path.is_relative_to(ROOT) else str(data_path),
            "limit": args.limit, "date": date, "commit": git_commit(), "prompt_version": PROMPT_VERSION,
            "wall_time_s": round(wall, 1),
            "settings": {"max_tokens": max_tokens(args) if args.backend != "predictions" else None,
                         "thinking": args.thinking, "max_usd": args.max_usd,
                         "effort": args.effort if args.backend == "anthropic" else None}}
    if args.backend != "predictions":
        meta["runtime"] = getattr(backend, "runtime", None)
    m = {"meta": meta, "classification": metrics.classification(rows), "speed": metrics.speed(rows), "stops": metrics.stops(rows),
         "cost": metrics.cost(rows, args.price_in, args.price_out, local)}
    (run_dir / "metrics.json").write_text(json.dumps(m, indent=2) + "\n")
    (run_dir / "score.md").write_text(report.score_card(m))
    report.update_index(Path(args.results_dir))

    c, s, k = m["classification"], m["speed"], m["cost"]
    print(f"\nrun: {run_dir.relative_to(ROOT) if run_dir.is_relative_to(ROOT) else run_dir}")
    print(f"accuracy {c['accuracy']:.1%} ({c['correct']}/{c['n']})   macro-F1 {c['macro_f1']:.3f}   "
          f"invalid {c['invalid_rate']:.1%} ({c['invalid']})")
    print(f"latency p50 {s['latency_p50_s']}s  p90 {s['latency_p90_s']}s   tokens/s {s['tokens_per_second']}   "
          f"wall {wall:.0f}s")
    print(f"cost per 1,000 bills: {k['cost_per_1k_usd']}  ({k['cost_note']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
