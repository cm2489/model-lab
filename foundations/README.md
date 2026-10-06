# Foundations (optional background)

**What to do:** skip this folder unless a lab leaves you stuck on a basic idea. If it does, read the one session that matches, try the check questions, then go back to the lab.

None of it is required. No lab step depends on it.

## What is here

Four short sessions on how language models work, plus 54 flashcards.

| Session | Time | Read it when |
|---|---|---|
| [3. Neural nets](sessions/s3-neural-nets.md) | about 2 h | "weights" or "parameters" is a fuzzy word for you |
| [4. How models learn](sessions/s4-how-models-learn.md) | about 2 h | you want to know what training and fine-tuning actually change |
| [5. Tokenization](sessions/s5-tokenization.md) | about 2.5 h | chat templates, token counts or per-token prices confuse you |
| [6. Transformers](sessions/s6-transformers.md) | about 2.5 h | context length and its cost confuse you |

Times are the original estimates, not measured. Each session includes video watching, a produce task and a teach-back, so reading the lesson alone is much shorter.

Other files:

- [cards.json](cards.json): the flashcards, always available, tagged `"lab": "foundations"`.
- [cards-original.json](cards-original.json): the untouched originals, kept so nothing is lost.
- [tutor-notes.md](tutor-notes.md): notes for an AI tutor or a study partner who guides you through a session.
- [SOURCES.md](SOURCES.md): every outside link and whether it worked on 2026-10-06.

## How each session connects to the labs

- **Weights and loss (sessions 3 and 4) -> what fine-tuning changes.** A model is a big pile of numbers called weights. Training moves them to lower a loss number. Fine-tuning does the same on a small slice of them. Read these before Lab 2.
- **Tokenization (session 5) -> chat templates and token costs.** The model never sees letters, only token IDs. That is why chat templates matter, why token counts differ by language, and why prices are per token. Read this before preparing training data.
- **Transformers (session 6) -> context length and cost.** Attention compares every token with every other token, so long contexts cost much more. Read this before the serving and cost work.

## How to study a session

1. Read one lesson block.
2. Answer its check question in your head or on paper.
3. Only then open the hint and answer.
4. Do the quiz, the produce task and the teach-back at the end. The answers are hidden on purpose.

## Dated material

These lessons were written in June 2026 for an earlier course. The science (neurons, gradient descent, backprop, BPE, attention) does not change. These details do, so check them before you quote them:

- Vocabulary sizes: GPT-2 at 50,257 tokens and "later OpenAI tokenizers around 100k" (sessions 5 and card `fnd-s5.c12`). Newer models use other sizes.
- The "same text costs about 3x more tokens in Hindi than English" figure (session 5 and card `fnd-s5.c7`). The ratio depends on the tokenizer. Newer tokenizers narrow the gap for some languages.
- The `SolidGoldMagikarp` glitch-token story (session 5): it comes from GPT-2 and GPT-3 era tokenizers, documented in 2023.
- "Frontier models have billions of parameters" (session 3): current frontier models may be larger. The point (same kind of object, more dials) still holds.
- Context-window examples such as "4k to 400k tokens" (session 6): real context windows have grown since. The quadratic-cost reasoning still holds.
- "Long-context systems exist via heavy engineering and architectural variants" (session 6): this area moves fast.
- Tool names and pages: the Tiktokenizer site and "OpenAI's tokenizer page" (session 5), and the 3Blue1Brown lesson pages. See [SOURCES.md](SOURCES.md).
- Session 3 describes sigmoid as the 3Blue1Brown intro choice and ReLU as the modern default. That is still the general picture.

Nothing in the lessons was rewritten for the science. Wording was lightly edited so the sessions stand alone: references to the earlier course's note system were reworded to "your notes".
