"""The prompt every backend sends, and the parser that turns a reply into one label.

The same prompt goes to every model so the comparison is fair. If you change it,
bump PROMPT_VERSION so old and new scores are never mixed up in one table.
"""

from __future__ import annotations

import re

from evals.labels import LABELS

PROMPT_VERSION = "v1"

INSTRUCTIONS = """You classify US congressional bills into exactly one policy area.

Policy areas:
{labels}

Bill title:
{title}

Reply with the one policy area that fits best, written exactly as it appears in the list. Reply with the policy area only, no other words."""


def build_messages(title: str) -> list[dict]:
    """One user message: instructions, the label list, the bill title."""
    labels = "\n".join(f"- {label}" for label in LABELS)
    return [{"role": "user", "content": INSTRUCTIONS.format(labels=labels, title=title)}]


def _norm(text: str) -> str:
    """Lowercase, and treat any run of spaces or punctuation as one space.

    Commas count as punctuation, so "Arts, Culture, Religion" and
    "arts culture religion" normalize the same way. Two labels joined by a
    comma ("Taxation, Health") do not normalize to any single label.
    """
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


_BY_NORM = {_norm(label): label for label in LABELS}


def strip_thinking(text: str) -> str:
    """Drop any reasoning a model printed before its answer.

    Qwen-style models wrap reasoning in <think>...</think>. When thinking is on,
    the opening tag is part of the prompt, so the reply may hold only the
    closing tag. Keep what comes after the last </think>. An unclosed <think>
    means the model never reached an answer, so nothing is left.
    """
    if "</think>" in text:
        return text.rsplit("</think>", 1)[1]
    if "<think>" in text:
        return ""
    return text


_PREFIX = re.compile(r"^(policy area|answer|label|category)\s*:\s*", re.I)
_MARKERS = re.compile(r"^(#{1,6}\s+|[-*+]\s+|\d+[.)]\s+)")  # markdown heading or list marker
_WRAP = "\"'`*“”‘’"
_TRAILING = ".!?;:"


def _trim(text: str) -> str:
    return text.strip().strip(_WRAP).strip()


def parse_label(reply: str) -> tuple[str | None, str]:
    """Turn a model reply into (label, how). Strict on purpose.

    Removed, in this order:
      1. reasoning in <think>...</think>
      2. whitespace, and surrounding quotes, backticks or asterisks
      3. one markdown heading marker ("# ") or list marker ("- ", "* ", "1. ")
      4. an optional "Policy area:" style prefix, also when wrapped in asterisks
         ("**Policy area:** Health")
      5. trailing punctuation (. ! ? ; :), then whitespace and wrapping again
    What is left must equal exactly one label, ignoring case, spacing and
    punctuation inside it ("arts culture religion" is "Arts, Culture, Religion").

    how is "exact" for a label, "invalid" for anything else: a label inside a
    sentence, two labels, a negation ("Not Health"), or no label at all.
    """
    text = _trim(strip_thinking(reply))
    text = _trim(_MARKERS.sub("", text))
    text = _trim(_PREFIX.sub("", text))
    text = _trim(text.rstrip(_TRAILING))
    label = _BY_NORM.get(_norm(text))
    return (label, "exact") if label else (None, "invalid")
