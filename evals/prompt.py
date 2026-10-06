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


# The short style leaves the label list out. A base model needs the list to know
# the label names. A model fine-tuned on these labels has learned them, so it can
# be asked with a prompt about a sixth of the length. Lab 2 trains and scores with it.
SHORT_PROMPT_VERSION = "short-v1"

SHORT_INSTRUCTIONS = """Which Congress.gov policy area does this bill belong to? Reply with the policy area only.

Bill title:
{title}"""

PROMPT_STYLES = ("list", "short")


def prompt_version(style: str = "list") -> str:
    return SHORT_PROMPT_VERSION if style == "short" else PROMPT_VERSION


def build_messages(title: str, style: str = "list") -> list[dict]:
    """One user message. "list": instructions, the label list, the title. "short": no label list."""
    if style == "short":
        return [{"role": "user", "content": SHORT_INSTRUCTIONS.format(title=title)}]
    if style != "list":
        raise ValueError(f"unknown prompt style: {style}")
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
_WRAP = "\"'`*“”‘’"


def parse_label(reply: str) -> tuple[str | None, str]:
    """Turn a model reply into (label, how). Strict on purpose.

    The reply counts only if, once these are removed, the whole reply is one label:
      - reasoning in <think>...</think>
      - an optional "Policy area:" style prefix
      - surrounding quotes, backticks or asterisks, and one final period
    Case, spacing and punctuation inside the label are ignored.
    how is "exact" for a label, "invalid" for anything else: a label inside a
    sentence, two labels, a negation ("Not Health"), or no label at all.
    """
    text = strip_thinking(reply).strip()
    text = _PREFIX.sub("", text).strip()
    text = text.strip(_WRAP).strip()
    if text.endswith("."):
        text = text[:-1]
    text = text.strip(_WRAP).strip()
    label = _BY_NORM.get(_norm(text))
    return (label, "exact") if label else (None, "invalid")
