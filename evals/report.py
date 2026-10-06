"""Markdown output: one score card per run, and the table in results/README.md."""

from __future__ import annotations

import json
from pathlib import Path


def _pct(x):
    return "n/a" if x is None else f"{x * 100:.1f}%"


def _num(x, fmt="{:.2f}"):
    return "n/a" if x is None else fmt.format(x)


def _money(x):
    return "n/a" if x is None else f"${x:.2f}"


COLUMNS = ["Run", "Model", "Backend", "Prompt", "Split (n)", "Accuracy", "Macro-F1", "Invalid",
           "p50 / p90 s", "tok/s", "$ per 1k bills", "Date (ET)", "Commit"]


def table_row(m: dict) -> str:
    meta, c, s, k = m["meta"], m["classification"], m["speed"], m["cost"]
    cells = [
        f"[{meta['run_name']}]({meta['run_name']}/score.md)",
        f"`{meta['model']}`" + (f" + LoRA `{meta['adapter'].rstrip('/').rsplit('/', 1)[-1]}`" if meta.get("adapter") else ""),
        meta["backend"],
        meta.get("prompt_style", "list"),
        f"{meta['split']} ({c['n']})",
        _pct(c["accuracy"]),
        _num(c["macro_f1"]),
        _pct(c["invalid_rate"]),
        f"{_num(s['latency_p50_s'])} / {_num(s['latency_p90_s'])}",
        _num(s["tokens_per_second"], "{:.0f}"),
        _money(k["cost_per_1k_usd"]),
        meta["date"][:16].replace("T", " "),
        f"`{meta['commit']}`",
    ]
    return "| " + " | ".join(cells) + " |"


def score_card(m: dict) -> str:
    meta, c, s, k = m["meta"], m["classification"], m["speed"], m["cost"]
    lines = [
        f"# {meta['run_name']}",
        "",
        f"- Model: `{meta['model']}` ({meta['backend']})",
        f"- Split: {meta['split']}, {c['n']} examples"
        + (f" (first {meta['limit']} only)" if meta.get("limit") else ""),
        f"- Date: {meta['date']} (Eastern Time)",
        f"- Commit: `{meta['commit']}`, prompt {meta['prompt_version']}",
        f"- Wall time: {meta['wall_time_s']:.0f} s",
        "",
        "| " + " | ".join(COLUMNS) + " |",
        "|" + "---|" * len(COLUMNS),
        table_row(m),
        "",
        f"Correct {c['correct']} of {c['n']}. Invalid replies: {c['invalid']} (counted as wrong).",
        f"How replies ended: {', '.join(f'{k} {v}' for k, v in sorted(m.get('stops', {}).items())) or 'n/a'}."
        " A reply that hit max_tokens was cut off.",
        f"Cost: {k['cost_note']}. Average tokens per bill: {k['avg_input_tokens']} in, {k['avg_output_tokens']} out.",
        "",
        "## Top confusions (gold → predicted)",
        "",
        "| Gold | Predicted | Count |",
        "|---|---|---|",
        *[f"| {x['gold']} | {x['pred']} | {x['count']} |" for x in c["top_confusions"]],
        "",
        "## Per label",
        "",
        "| Label | Precision | Recall | F1 | Support |",
        "|---|---|---|---|---|",
        *[f"| {lab} | {v['precision']:.2f} | {v['recall']:.2f} | {v['f1']:.2f} | {v['support']} |"
          for lab, v in sorted(c["per_label"].items(), key=lambda kv: -kv[1]["support"])],
        "",
    ]
    return "\n".join(lines)


INDEX_HEADER = """# Score table

Every run of `evals.run` adds a row. Built by `evals/report.py` from `results/*/metrics.json`; do not edit by hand.

- Accuracy counts invalid replies as wrong.
- Cost per 1,000 bills uses the measured token counts and the prices given on the command line.
  Local runs show $0.00: marginal cost only, hardware and electricity not counted.
- tok/s is generation speed reported by the local runtime. API runs leave it blank.
- Dates are Eastern Time.

"""


def update_index(results_dir: Path) -> None:
    runs = []
    for p in sorted(results_dir.glob("*/metrics.json")):
        m = json.loads(p.read_text())
        runs.append(m)
    runs.sort(key=lambda m: m["meta"]["date"])
    body = ["| " + " | ".join(COLUMNS) + " |", "|" + "---|" * len(COLUMNS), *[table_row(m) for m in runs]]
    (results_dir / "README.md").write_text(INDEX_HEADER + "\n".join(body) + "\n")
