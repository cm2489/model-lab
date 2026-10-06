# The customization toolchain, October 6, 2026

## Short version

- Climb the ladder in order: prompt, then retrieval and tools, then prompt optimization, then LoRA fine-tuning of a small open model, and only then reinforcement learning or distillation. Fine-tune for form and behavior, not for facts.
- A 32 GB Apple-silicon Mac can run models up to roughly 27 to 30B at 4-bit, and can plausibly LoRA-tune small models (4B to 9B) with mlx-lm. Nobody measured training time or memory on that class of Mac, so test early.
- Hosted fine-tuning is cheap (single-digit dollars for small jobs), so data and evals are the real work, not compute.
- OpenAI is winding down its fine-tuning platform. Open weights avoid that risk.
- Training on outputs from Claude, OpenAI or Gemini models is restricted by their terms. Safer data: your own or a client's data, human labels, or permissively licensed open teachers.

Confidence words: `verified`, `likely`, `not verified`. See the [README](README.md). Prices were read on the date shown. Each source is shown as ([label](link), date).

## 1. The customization ladder

| Rung | What it is | Right when | Confidence |
|---|---|---|---|
| 1. Prompt | Better instructions and examples | Always first. A working eval that fails here is the start of every later rung | `likely` |
| 2. Retrieval and tools | Put the facts in context at run time | The problem is missing knowledge. Retrieval beats fine-tuning for factual recall | `likely` |
| 3. Prompt optimization | Tools such as DSPy with the GEPA optimizer search for better prompts automatically | You have an eval and 20 to 100 examples (the 20 to 100 figure is one source's claim). GEPA beats GRPO by about 6 percent on average (up to 20 percent) with up to 35 times fewer rollouts, and beats the MIPROv2 optimizer by over 10 percent. ICLR 2026 oral. These are paper claims, not reproduced here | `verified` for the paper's claims ([arXiv](https://arxiv.org/abs/2507.19457), 2025-07) |
| 4. LoRA fine-tuning (SFT) | Train a small adapter so a small model follows a format, tone or domain vocabulary | Prompt plus retrieval fails a task-specific eval; you have hundreds of production-like examples; volume or privacy makes a small model worth owning | `likely` |
| 5. Preference tuning and RL (DPO, GRPO) | Train against a reward or preference | Later rung. Needs a programmatic reward or grader, plus rollouts, so it costs more than SFT. DPO costs about 2.5 times SFT | `likely` |
| 6. Distillation | Teach a small model from a larger teacher | Cost and latency compression. Mind the teacher's license and terms (see section 8) | `likely` |

- The ordering of prompt, retrieval, fine-tune, distill is practitioner consensus from several 2026 guides. One vendor's documentation (Unsloth) claims fine-tuning can replace retrieval, which conflicts with that consensus. A checklist from one guide: a working eval that fails with prompt plus retrieval, hundreds of production-matched examples, and 12 months of ownership. Budget 3 to 5 times the training cost for upkeep (one blog's claim, `not verified`). `likely` ([BigData Boutique](https://bigdataboutique.com/blog/fine-tuning-llms-when-rag-isnt-enough), 2026-05-10; [Winder.ai](https://winder.ai/rag-vs-fine-tuning-2026-decision-framework/), 2026-06).
- Distilling a frontier model into a small tuned model at about one tenth of the inference cost is a cited pattern (Winder.ai, 2026-06). `likely`.
- Time-to-first-dollar claims for any narrow customization service are a synthesis, not a sourced fact. `not verified`.

## 2. Tool status

| Tool | Status as of Oct 6, 2026 | Confidence |
|---|---|---|
| **mlx-lm** (Apple silicon) | Version 0.32.0 released 2026-10-01; requires Python 3.11 or newer. Supports LoRA (default), DoRA and full fine-tuning; QLoRA by training on a quantized model. Memory levers: batch size, number of layers tuned, gradient checkpointing, accumulation. The repository contains Qwen3.5 (hybrid attention, with a training code path) and Gemma 4 model files. An end-to-end LoRA run on Qwen3.5-4B was later measured and worked (see section 4). GitHub's release page shows v0.31.3 (Apr 22, 2026) as the newest tag it displays, which does not match PyPI's 0.32.0; not reconciled. The community project mlx-tune adds DPO, GRPO and ORPO on Mac with an Unsloth-style API | `verified` for version and requirements ([PyPI](https://pypi.org/project/mlx-lm/), 2026-10-01; [LORA.md](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md), 2026-10); `verified` for Qwen3.5-4B training (section 4) |
| **Unsloth** | Core is Apache-2.0; the Studio interface is AGPL-3.0. Catalog lists 4-bit builds of Qwen3.8-27B, all Gemma 4 sizes, gpt-oss and Muse Glimmer, but not Granite 4.2 or Inkling. **Mac training support is contradicted across its own pages**: the requirements page says Mac training, MLX and GGUF are all supported; the March 2026 Studio launch post said MLX training was "coming soon"; the README now says it can train on macOS; another line says Apple silicon "is in the works". Unresolved without a smoke test | `verified` for license and catalog ([README](https://github.com/unslothai/unsloth), 2026-10-06; [catalog](https://unsloth.ai/docs/get-started/unsloth-model-catalog), 2026); `not verified` for Mac training ([requirements](https://unsloth.ai/docs/get-started/fine-tuning-for-beginners/unsloth-requirements), 2026; [Studio post](https://unslothai.substack.com/p/introducing-unsloth-studio), 2026-03-17) |
| **TRL** (Hugging Face) | Latest v1.14.1 (2026-09-29). The DistillationTrainer has been stable since v1.10.0 (2026-08-13). v1.11 moved to vLLM's native server; v1.13 added 1M-token long-context training. GRPO and RLOO trainers are stable. The exact date of v1.0 was not confirmed | `verified` ([releases](https://github.com/huggingface/trl/releases), 2026-09-29; [docs](https://huggingface.co/docs/trl/index), 2026) |
| **Axolotl** | Latest v0.20.0 (2026-09-30): GGUF export, context parallelism, native NVFP4 LoRA. v0.18 added 4-bit expert LoRA and QLoRA for sparse MoE. (Version 0.16 from April is stale.) Operation on Apple silicon was not researched | `verified` ([releases](https://github.com/axolotl-ai-cloud/axolotl/releases), 2026-09-30) |
| **llama.cpp and GGUF** | The ggml and llama.cpp team joined Hugging Face on 2026-02-20 and the project stays open source. GGUF export from mlx-lm covers only a few older architectures at fp16 | `verified` ([HF blog](https://huggingface.co/blog/ngxson/ggml-and-llama-cpp-join-hugging-face), 2026-02-20) |
| **Ollama** | Announced an MLX backend preview in 0.19 (2026-03-30). The blog says it needs a Mac with "more than 32GB" of unified memory and names M5-series chips. A secondary source says "32GB or more" with automatic fallback and lists 0.34.3 (2026-09-19) as the latest stable. Whether a 32 GB Mac gets the MLX path is **unresolved**. A claim that MLX became stable in v0.30 (May 2026) was not confirmed | `not verified` ([Ollama blog](https://ollama.com/blog/mlx), 2026-03-30; [secondary](https://yage.ai/share/mlx-apple-silicon-en-20260331.html), 2026-03-31) |
| **LM Studio** | Runs GGUF and MLX models (secondary report). `mlx_lm.generate` or LM Studio are the safe local defaults | `likely` |
| **vLLM and SGLang** | Both serve multiple LoRA adapters. One secondary source says SGLang is slightly ahead at 50 or more adapters. Primary vLLM docs returned an error and were not read | `likely` |
| **Eval tools** | **Inspect** 0.3.276 (2026-10-02), MIT, credited to the UK AI Security Institute. **lm-evaluation-harness**: the releases page shows v0.4.13, but its date was unreadable; 200 or more tasks; supports vLLM, SGLang and API backends. **promptfoo** is MIT and now part of OpenAI (announced 2026-03-09; stays open source). MLflow is the open tracking option; Weights & Biases sits under CoreWeave. **Langfuse** (tracing) was acquired by ClickHouse (2026-01-16), with an MIT core and standalone cloud continuing | `verified` for Inspect, promptfoo, Langfuse ([PyPI](https://pypi.org/project/inspect-ai/), 2026-10-02; [promptfoo](https://github.com/promptfoo/promptfoo), 2026-03; [ClickHouse](https://clickhouse.com/blog/clickhouse-acquires-langfuse-open-source-llm-observability), 2026-01-16); `not verified` for the lm-eval date ([releases](https://github.com/EleutherAI/lm-evaluation-harness/releases), 2026) |
| **Hosted RL and training** | **ART** (OpenPipe agent RL, Apache-2.0): README lists Qwen 3.8 and 2.5 and Llama; Gemma 3 unsupported. CoreWeave announced buying OpenPipe on 2025-09-03 (not rechecked). **Tinker** (Thinking Machines): generally available 2025-12-12; LoRA only; lists Qwen (including Qwen3.8-27B and the Qwen3.5 series), GLM-5.3, Kimi-K2.6, DeepSeek-V3.1, gpt-oss-20b and 120b, NVIDIA Nemotron 3 (Nano 30B to Ultra 550B), and Inkling models | `verified` for Tinker's list and ART README ([Tinker](https://thinkingmachines.ai/tinker/), 2026-10-06; [ART](https://github.com/OpenPipe/ART), 2026); `likely` for OpenPipe ([TechCrunch](https://techcrunch.com/2025/09/03/coreweave-acquires-agent-training-startup-openpipe/), 2025-09-03) |

Local picks: use Unsloth or mlx-lm on a laptop, and TRL or Axolotl on rented GPUs. `likely`.

## 3. Hosted fine-tuning and serving, and what is being withdrawn

- **OpenAI is winding down fine-tuning.** Notice dated 2026-05-07: organizations that never ran fine-tuning cannot start. From 2026-07-02, organizations with no inference on a fine-tuned model in the previous 60 days cannot create jobs. On 2027-01-06 existing customers can no longer create new jobs. Inference on existing fine-tunes continues until the base model retires. o4-mini (the only model for OpenAI's reinforcement fine-tuning) and gpt-4.1-nano shut down on 2026-10-23, so OpenAI reinforcement fine-tuning is effectively gone. SFT and DPO covered only gpt-4.1 variants. `verified` ([OpenAI deprecations](https://developers.openai.com/api/docs/deprecations), 2026-05-07; [forum](https://community.openai.com/t/openai-s-self-serve-fine-tuning-availability/1380481.md), 2026-05-08).
- **Gemini API:** Google's forum says the Gemini API has no fine-tunable model (supported on Vertex only). `verified` ([Google docs](https://ai.google.dev/gemini-api/docs/model-tuning?hl=en), 2026). **Claude fine-tuning** exists only on Amazon Bedrock, documented for Claude 3 Haiku (2024-era source). `likely`.
- **Prices** (read on the dates shown; confirm before use):

| Service | Price | Date read | Confidence |
|---|---|---|---|
| Together, LoRA SFT | $0.34 per million tokens for Qwen3.5 9B and Llama 3.1 8B (DPO $0.84); minimums $4 to $60 by model size; premium models (Kimi K2.6, GLM-5.2) $15 to $40 per million | 2026-10 | `verified` ([pricing](https://www.together.ai/pricing), 2026-10) |
| Fireworks, LoRA SFT | $0.50 per million tokens up to 16B; $3 per million for 16B to 80B. Fine-tuned models serve at base-model cost; any multi-adapter surcharge is unclear | 2026-10 | `verified` ([pricing](https://fireworks.ai/pricing), 2026-10) |
| Tinker, training | Qwen3-8B $0.44 per million training tokens and $0.60 per million sampling; Qwen3.5-4B $0.737; Qwen3.5-9B $1.463; storage $0.10 per GB-month; 80 percent discount on cached prefill; no free credits mentioned. A "limited-time 50% discount" is listed for Inkling. A July 17, 2026 price increase was not confirmed | 2026-10-06 | `verified` ([Tinker models and pricing](https://tinker-docs.thinkingmachines.ai/tinker/models/), 2026-10-06) |
| RunPod GPU, per hour (community / secure) | RTX 4090 $0.34 / $0.74; L40S $0.79 / $1.09; A100 80 GB $1.19 to $1.59; H100 SXM $2.69 / $3.49; H200 $3.59 / $4.59; B200 $5.98 / $6.79 | 2026-09-27 | `verified` ([RunPod](https://www.runpod.io/pricing), 2026-09-27) |
| Hugging Face Jobs, per hour | A10G $1.00; L40S $1.80; A100 $2.50; H200 $5.00. Jobs bill per second but default to a 30-minute timeout, so set one | 2026-10 | `verified` ([HF Jobs docs](https://huggingface.co/docs/huggingface_hub/guides/jobs), 2026-10) |
| Other H100 prices, per hour | Together dedicated inference from $5.49 (range $5.49 to $8.99); Together clusters $1.99 to $3.99; Lambda H100 SXM $4.29 and B200 $6.99; Baseten dedicated $6.50; Fireworks $8 | 2026-10 | `verified` for Together and Fireworks; `likely` for Lambda and Baseten ([Lambda](https://lambda.ai/pricing), 2026-10; [Baseten](https://www.baseten.co/pricing/), 2026-10) |
| Serving a small model | Always-on L4 at $0.80 per hour on Hugging Face endpoints is about $584 a month (the arithmetic checks); Baseten L4 $0.85 per hour with scale-to-zero; Together serverless small models $0.15 to $0.30 per million input tokens. Range of roughly $0 to $600 a month depending on traffic | 2026-10 | `likely` ([HF pricing](https://huggingface.co/pricing), 2026-10) |

- Worked example (arithmetic from the vendor prices, not vendor quotes): a 5M-token job (2,000 examples of 800 tokens for 3 epochs) is under $2 raw on Together's 8B price (minimum charge $4 or more applies), about $2.50 on Fireworks up to 16B, and about $15 on Fireworks for 16B to 80B. `likely`.
- **Self-run on a rented GPU.** Unsloth's published training-memory table: 7B QLoRA about 5 GB and LoRA 16-bit about 19 GB; 8B 6 and 22 GB; 14B 8.5 and 33 GB; 32B 26 and 76 GB (CUDA figures). A 17.5 GB figure for a 30B MoE does not appear on the cited page. That page says Qwen3-30B-A3B 16-bit LoRA uses about 63 GB and that 4-bit QLoRA on MoE models "isn't recommended right now". So a 30B MoE needs an 80 GB-class GPU, and a cost estimate of $5 to $15 would be too low. No corrected estimate was found. `verified` ([faster MoE page](https://unsloth.ai/docs/basics/faster-moe), 2026; [requirements](https://unsloth.ai/docs/get-started/fine-tuning-for-beginners/unsloth-requirements), 2026).
- AWS Bedrock Custom Model Import accepts Llama, Qwen2 and 3, Mistral and gpt-oss, but not Gemma (not listed) or Qwen3.5. Not rechecked. `likely`.

## 4. What a 32 GB Apple-silicon Mac can and cannot do

No source found in the research measured training time, peak memory or speed on this class of Mac. Two measurements were later made by the project itself (below). Everything else here is from model-file sizes and general Mac guides (written for newer chips). Treat it as planning, not a benchmark. `likely` overall.

Measured, `verified` (measured on a 32 GB Apple-silicon Mac, mlx-lm 0.32.0, October 6, 2026):

- `mlx-community/Qwen3.5-4B-4bit` generates at about 94 tokens per second with a 2.6 GB peak.
- A 20-step LoRA run (rank 8, 8 layers, batch size 1) on that model completes in about 19 to 30 seconds with a 6.5 GB peak. An independent re-run reproduced the loss values exactly.

This resolves the earlier gap that no source had measured LoRA on this class of Mac and that Qwen3.5 training in mlx-lm was unconfirmed. It covers one small model and a short run, not larger models or longer jobs.

| Task | Verdict | Evidence |
|---|---|---|
| Run a 4-bit dense 27B to 30B model | Fits, but tight | Qwen3.8-27B Q4_K_M is 16.5 GB (IQ4_XS 14.3 GB); Muse Glimmer 4-bit is about 17 GB. `verified` ([Unsloth Qwen3.8-27B GGUF](https://huggingface.co/unsloth/Qwen3.8-27B-GGUF), 2026-08) |
| Run a mixture-of-experts 35B at 4-bit | Tighter | A MoE must hold all weights in memory. Qwen3.6-35B-A3B 4-bit files are 17.7 to 22.4 GB (Q4_K_M 22.1 GB). An earlier "about 9 GB" figure was wrong. `verified` ([Unsloth Qwen3.6-35B-A3B GGUF](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF), 2026) |
| GPU-usable memory | Only part of unified memory is usable by the GPU. A "75 percent" figure and a setting (`iogpu.wired_limit_mb`) to raise it come from secondary sources | `not verified` ([InsiderLLM](https://insiderllm.com/guides/fine-tuning-mac-lora-mlx/), 2026; [guide](https://mehmetbaykar.com/posts/increase-vram-apple-silicon-local-llm/), 2026) |
| LoRA on 4B to 9B models | Plausible | mlx-community 4-bit files: Qwen3.5-4B about 3.05 GB, Qwen3.5-9B about 5.95 GB, Gemma 4 12B about 6.7 GB (the 4B and 12B sizes were not re-fetched). `verified` for the 9B and for the 4B ([HF API, 9B](https://huggingface.co/api/models/mlx-community/Qwen3.5-9B-4bit?blobs=true), 2026-03-02); `likely` for the 12B. The 4-bit 4B file measured 3,034,300,695 bytes on download on October 6, 2026, and Hugging Face metadata gives 9,319,828,096 bytes for the full-precision files |
| LoRA or QLoRA on 12B to 14B | Marginal and unmeasured | Secondary guides say it fits on 32 GB. Unsloth's CUDA table (14B QLoRA about 8.5 GB) is consistent with that but is not a Mac measurement. `not verified` |
| Tune 27B to 35B locally | Do not plan on it | Treat as a rented-GPU job. `likely` |
| Run frontier open models (Kimi K3, Qwen3.8-2.4T, DeepSeek V4.x, GLM-5.3, MiMo-V2.6-Pro) | Cannot | Hundreds of GB to terabytes. Use hosted APIs or rented GPUs. `verified` ([DeepSeek V4.1-Flash card](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash), 2026-09) |
| Speed | Mac training is reported at about 2 to 4 times slower than NVIDIA | `likely` ([LLMCheck](https://llmcheck.net/guides/fine-tune-llm-mac-mlx/), 2026) |

Practical points:

- **Python.** mlx-lm 0.32.0 needs Python 3.11 or newer. An older system Python will not work. Install a version manager such as uv and make a 3.11 or newer environment. `verified`.
- **Disk.** Model files are 3 to 22 GB at 4-bit, and adapters, fused copies, GGUF exports and the Hugging Face cache come on top. Keep free space well above one model's size, or point the cache (`HF_HOME`) at an external drive. A full-precision Qwen3.5-4B is about 9.3 GB. `verified` for file sizes ([HF API](https://huggingface.co/api/models/mlx-community/Qwen3.5-4B-4bit?blobs=true), 2026-10-06).
- **A sensible first project** (a suggestion, not a sourced fact): QLoRA a Qwen3.5 4B or 9B (Apache-2.0; released 2026-03-02, `verified` from [VentureBeat](https://venturebeat.com/technology/alibabas-small-open-source-qwen3-5-9b-beats-openais-gpt-oss-120b-and-can-run), 2026-03-02) on a narrow behavior task, with 300 to 1,000 JSONL chat examples (guides say 200 to 500 clean ones can be enough), a held-out eval and a prompt-only baseline. Compare with Inspect or promptfoo, then publish the adapter. `likely`.
- Newer Apache-2.0 mid-size Qwen bases exist for cloud LoRA: Qwen3.6-35B-A3B, Qwen3.6-27B and Qwen3.8-27B. No Qwen3.6 or 3.8 small (4B or 9B) models were found, so Qwen3.5 small appears to be the latest small Qwen. `likely` ([Qwen3.6-27B](https://huggingface.co/Qwen/Qwen3.6-27B), 2026-04).

## 5. Best base models to fine-tune

- Gemma 4 (Apache-2.0, first time for Gemma, launched 2026-04-02 with E2B, E4B, 26B-A4B and 31B; the 12B model came later) and Qwen3.5 small (0.8B, 2B, 4B, 9B, Apache-2.0). `verified` ([The Decoder](https://the-decoder.com/googles-gemma-4-is-now-available-with-apache-2-0-licensing-for-the-first-time/), 2026-04-02).
- Also practical: gpt-oss-20b, Muse Glimmer 30B, Granite 4.2, Qwen3.8-27B (Unsloth lists most of these; not Granite 4.2). `likely`.
- Check each model card's license before client delivery. Qwen3.8 is the clearest case: the 27B is Apache-2.0 while the flagship has a custom license with a $50 million threshold (see [landscape.md](landscape.md)). `verified`.

## 6. Open and closed leaders at a glance (for choosing a teacher or base)

See [landscape.md](landscape.md) for the full table and scores. Short form: Chinese open models lead; Inkling, Nemotron 3 and Gemma 4 are the main US open options; Reflection's Beam (501B, Apache-2.0) was announced 2026-10-05 and is not yet downloadable. `verified`.

## 7. Open-weight teachers and license limits

- Kimi K3 and the Qwen3.8 flagship carry revenue-threshold licenses (see [landscape.md](landscape.md)), so they matter when choosing a teacher model for client work. `verified`.
- The teacher license terms of Qwen and DeepSeek for generating training data were not checked. `not verified`.

## 8. How training data is built, and terms-of-service limits

**Safer sources.** Client-owned data, human-labeled data, and open-weight teacher models with permissive licenses. Closed-model distillation carries enforcement risk. `likely`.

**Tooling in use for synthetic data:** distilabel (Argilla), Curator, NVIDIA Data Designer (formerly Gretel) and Easy Dataset. `likely` ([PremAI guide](https://www.premai.io/blog/how-to-generate-synthetic-training-data-for-llm-fine-tuning-2026-guide/), 2026).

**Terms of service.** Not legal advice.

| Provider | What the terms say | Confidence |
|---|---|---|
| Anthropic | A support article says its services cannot be used "to train or develop AI models without our written permission". The same article lists classifiers, semantic search, "information extraction tools" and "summarization tools" as permitted uses, and prohibits general chatbots, open-ended text generators and models that compete with Anthropic's. A summarizer returned one conflicting line ("Using Outputs as training targets for models"). **The two readings were not resolved. Read the article verbatim before relying on either.** Commercial Terms section D.4 (effective 2025-06-17) bars training competing models | `verified` that the article exists and contains both statements ([support article](https://support.claude.com/en/articles/12326764-can-i-use-my-outputs-to-train-an-ai-model), 2026-10-06; [Commercial Terms](https://www.anthropic.com/legal/commercial-terms), 2025-06-17); `not verified` for how to read them together |
| Google (Gemini API) | "May not use the Services to develop models that compete" (terms modified 2026-04-28) | `verified` ([Gemini API terms](https://ai.google.dev/gemini-api/terms), 2026-04-28) |
| OpenAI | Terms of Use returned an error, so the exact clause was not read. Secondary sources say outputs cannot be used to build competing models | `not verified` |

- Enforcement is real. Anthropic publicly accused DeepSeek, Moonshot and MiniMax of "distillation attacks" on 2026-02-23: about 24,000 fraudulent accounts and 16 million exchanges (DeepSeek over 150,000, Moonshot over 3.4 million, MiniMax over 13 million). `verified` ([Anthropic](https://www.anthropic.com/news/detecting-and-preventing-distillation-attacks), 2026-02-23; [TechCrunch](https://techcrunch.com/2026/02/23/anthropic-accuses-chinese-ai-labs-of-mining-claude-as-us-debates-ai-chip-exports/), 2026-02-23).
- Whether a private client model counts as "competing" under these terms was not researched. `not verified`.
- Before selling a distilled model, a lawyer's reading of the specific terms is the sensible step (general guidance).

## 9. Disagreements and gaps in this brief

- Anthropic terms: permitted extraction tools versus a conflicting summarizer line (section 8).
- Ollama on a 32 GB Mac: the blog and a secondary source differ (section 2).
- Unsloth Mac training: its own pages disagree (section 2).
- mlx-lm release: PyPI 0.32.0 on 2026-10-01 versus GitHub's release page showing v0.31.3 as newest (section 2).
- Not researched: Axolotl or TRL on Apple silicon, model merging and continued pretraining, Modal's and Lambda's fine-tuning products, and vLLM and SGLang primary documentation.
