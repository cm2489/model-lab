"""Score a model on a split and write the results.

Examples:
  uv run python -m evals.run --backend mlx --model mlx-community/Qwen3.5-4B-4bit --split golden
  uv run python -m evals.run --backend anthropic --model claude-opus-5-5 --split golden \\
      --price-in 4 --price-out 20
  uv run python -m evals.run --backend predictions --predictions results/<run>/predictions.jsonl
  uv run python -m evals.run --backend mlx --model mlx-community/Qwen3.5-4B-4bit \\
      --adapter-path adapters/policy-area --prompt short

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
from evals.prompt import PROMPT_STYLES, build_messages, parse_label, prompt_version


def make_backend(args):
    if args.backend == "mlx":
        from evals.backends import MlxBackend

        return MlxBackend(args.model, max_tokens=args.max_tokens or 32, thinking=args.thinking,
                          adapter_path=args.adapter_path)
    if args.backend == "anthropic":
        from evals.backends import AnthropicBackend

        effort = None if args.effort == "none" else args.effort
        return AnthropicBackend(args.model, max_tokens=args.max_tokens or 2048, effort=effort)
    raise ValueError(args.backend)


def predict_all(backend, examples: list[dict], out_path: Path, model: str, style: str = "list") -> list[dict]:
    """Run the model on every example. Writes each prediction as soon as it exists."""
    rows = []
    with open(out_path, "w") as f:
        for i, ex in enumerate(examples, 1):
            t0 = time.perf_counter()
            r = backend(build_messages(ex["title"], style))
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
    ap.add_argument("--max-tokens", type=int, help="reply length cap (default: mlx 32, anthropic 2048)")
    ap.add_argument("--thinking", action="store_true", help="mlx: let the model think first (off by default)")
    ap.add_argument("--effort", default="low", help="anthropic: low|medium|high|xhigh|max, or none to omit")
    ap.add_argument("--prompt", default="list", choices=PROMPT_STYLES,
                    help="list: the prompt names every label (default). short: no label list, for a tuned model")
    ap.add_argument("--adapter-path", help="mlx: folder of LoRA weights to load on top of --model")
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

    tuned = "-tuned" if args.adapter_path else ""
    run_name = args.run_name or f"{slug(model)}{tuned}-{split_name}-{date[:16].replace(':', '').replace('T', '-')}"
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
        rows = predict_all(backend, examples, pred_path, model, args.prompt)
        local = backend.local
    wall = time.perf_counter() - t0

    meta = {"run_name": run_name, "backend": args.backend, "model": model, "split": split_name,
            "data": str(data_path.relative_to(ROOT)) if data_path.is_relative_to(ROOT) else str(data_path),
            "limit": args.limit, "date": date, "commit": git_commit(),
            "prompt_version": prompt_version(args.prompt), "prompt_style": args.prompt,
            "adapter": args.adapter_path,
            "wall_time_s": round(wall, 1),
            "settings": {"max_tokens": args.max_tokens, "thinking": args.thinking,
                         "effort": args.effort if args.backend == "anthropic" else None}}
    if args.backend != "predictions":
        meta["runtime"] = getattr(backend, "runtime", None)
    m = {"meta": meta, "classification": metrics.classification(rows), "speed": metrics.speed(rows),
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
