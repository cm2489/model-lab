"""Model backends. Each one turns a list of chat messages into a reply plus token counts.

Heavy libraries are imported inside each backend, so scoring and the gate
run on plain Python with nothing installed.
"""

from __future__ import annotations


class MlxBackend:
    """A local model on Apple silicon, through mlx-lm. Greedy decoding (temperature 0)."""

    local = True

    def __init__(self, model_id: str, max_tokens: int = 32, thinking: bool = False,
                 adapter_path: str | None = None):
        from mlx_lm import load
        from mlx_lm.sample_utils import make_sampler
        import importlib.metadata

        self.runtime = f"mlx-lm {importlib.metadata.version('mlx-lm')}"

        # adapter_path: a folder of LoRA weights (adapters.safetensors) to load on top of the base model.
        self.model, self.tokenizer = load(model_id, adapter_path=adapter_path)
        self.sampler = make_sampler(temp=0.0)
        self.max_tokens = max_tokens
        # Qwen3.5 thinks by default: its chat template opens "<think>" for the reply.
        # enable_thinking=False makes the template insert an empty think block, so the
        # model answers at once. Templates without the switch ignore the extra argument.
        self.thinking = thinking

    def __call__(self, messages: list[dict]) -> dict:
        from mlx_lm import stream_generate

        prompt = self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, enable_thinking=self.thinking
        )
        text, last = "", None
        for last in stream_generate(self.model, self.tokenizer, prompt,
                                    max_tokens=self.max_tokens, sampler=self.sampler):
            text += last.text
        if self.thinking and "<think>" not in text:
            # The template already opened "<think>" in the prompt. Put it back so a
            # reply cut off mid-reasoning parses as invalid, not as a label it mentioned.
            text = "<think>\n" + text
        return {
            "raw": text,
            "input_tokens": last.prompt_tokens if last else len(prompt),
            "output_tokens": last.generation_tokens if last else 0,
            "gen_tps": round(last.generation_tps, 1) if last else None,
            "stop": last.finish_reason if last else None,
        }


class AnthropicBackend:
    """A frontier model through the Anthropic API. Needs ANTHROPIC_API_KEY in the environment.

    Claude Opus 5.5 always thinks; effort is the only control, so this sends
    effort "low" (classification does not need deep reasoning). Thinking
    tokens are billed as output tokens and are counted in output_tokens.
    No refusal fallback is set: a fallback would score a second model under
    the first one's name. A refusal is recorded as an invalid reply.
    """

    local = False

    def __init__(self, model_id: str, max_tokens: int = 2048, effort: str | None = "low", client=None):
        if client is None:
            import anthropic

            client = anthropic.Anthropic()
        self.client = client
        self.runtime = None
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.effort = effort

    def __call__(self, messages: list[dict]) -> dict:
        kwargs = {"model": self.model_id, "max_tokens": self.max_tokens, "messages": messages}
        if self.effort:
            kwargs["output_config"] = {"effort": self.effort}
        try:
            resp = self.client.messages.create(**kwargs)
        except Exception as e:  # noqa: BLE001
            if not _retryable(e):
                raise
            # The SDK already retried twice. Record the miss and keep going.
            return {"raw": f"[api error] {type(e).__name__}", "input_tokens": 0, "output_tokens": 0,
                    "gen_tps": None, "stop": "error"}
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        if resp.stop_reason == "refusal":
            text = "[refusal]"
        return {
            "raw": text,
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
            "gen_tps": None,
            "stop": resp.stop_reason,
        }


def _retryable(e: Exception) -> bool:
    """Rate limits, server errors and network errors. Auth or bad-request errors stop the run."""
    try:
        import anthropic
    except ImportError:
        return False
    if isinstance(e, (anthropic.RateLimitError, anthropic.APIConnectionError)):
        return True
    return isinstance(e, anthropic.APIStatusError) and e.status_code >= 500
