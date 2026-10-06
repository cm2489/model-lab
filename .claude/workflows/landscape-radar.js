export const meta = {
  name: 'landscape-radar',
  description: 'Refresh the open-weight landscape research: seven topics, each checked by an independent verifier. Read-only.',
  phases: [
    { title: 'Research', detail: '7 web research topics, Sonnet 5.5', model: 'sonnet' },
    { title: 'Verify', detail: 'independent refutation pass per topic, Opus 5.5', model: 'opus' },
  ],
}

// Landscape radar: seven research topics, each checked by an independent verifier. Read-only.
// Run it with args { today: 'YYYY-MM-DD', profile: '<optional: who the research is for>' }.
// Keep personal details out of this file. Pass them in args.profile at run time.

const TODAY = (args && args.today) || 'unknown (the caller did not pass args.today; find the date from a fetched page and say so)'
const RULES = `Today is ${TODAY}. Your training knowledge is months stale on this fast-moving subject: treat memory as a lead, never as a fact. Every claim about 2025-2026 must come from a page you fetched in this session. Load web tools first with ToolSearch query "select:WebSearch,WebFetch" (use WebSearch mode "extended" when a standard search is thin or outdated). Prefer primary sources: lab blogs, Hugging Face model cards, official docs, arXiv, live job postings, reputable press. Record URL and publication date for each source. Rate each finding: "verified" (you read a primary or reputable source this session), "likely" (secondary source only), or "unverified" (could not confirm; say why in detail). Never guess: unknowns go in gaps. You are a subagent: read-only. Do not create, edit or delete any file, do not ask the user anything, do not publish anything, do not open a browser window. Keep each finding's detail under 90 words. Return at most 20 findings, the most decision-relevant first.`

const PROFILE = (args && args.profile) || `Who this is for: a solo builder who ships products with coding agents (TypeScript first, working Python), understands LLMs at an intuitive level, and wants to customize open-weight models for their own use, for clients and as portfolio evidence. Hardware: a 32 GB Apple-silicon Mac. Prefer free resources, short loops and public artifacts.`

const FINDINGS_SCHEMA = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          claim: { type: 'string' },
          detail: { type: 'string' },
          confidence: { type: 'string', enum: ['verified', 'likely', 'unverified'] },
          sources: {
            type: 'array',
            items: {
              type: 'object',
              properties: { url: { type: 'string' }, title: { type: 'string' }, date: { type: 'string' } },
              required: ['url'],
            },
          },
        },
        required: ['claim', 'detail', 'confidence', 'sources'],
      },
    },
    recommendations: { type: 'array', items: { type: 'string' } },
    gaps: { type: 'array', items: { type: 'string' } },
  },
  required: ['summary', 'findings', 'recommendations', 'gaps'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          claim: { type: 'string' },
          verdict: { type: 'string', enum: ['confirmed', 'corrected', 'refuted', 'unverifiable'] },
          correction: { type: 'string' },
          sources: {
            type: 'array',
            items: {
              type: 'object',
              properties: { url: { type: 'string' }, title: { type: 'string' }, date: { type: 'string' } },
              required: ['url'],
            },
          },
        },
        required: ['claim', 'verdict', 'correction', 'sources'],
      },
    },
    missed: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          claim: { type: 'string' },
          detail: { type: 'string' },
          sources: {
            type: 'array',
            items: {
              type: 'object',
              properties: { url: { type: 'string' }, title: { type: 'string' }, date: { type: 'string' } },
              required: ['url'],
            },
          },
        },
        required: ['claim', 'detail', 'sources'],
      },
    },
    overallReliability: { type: 'string' },
  },
  required: ['verdicts', 'missed', 'overallReliability'],
}

const TOPICS = [
  {
    key: 'models',
    title: 'Open-weight model landscape: who has shipped what, as of today',
    ask: `Catalogue the open-weight model families that matter as of today. For each: lab, country, latest release name and date, sizes (parameters), modality, license (Apache-2.0 / MIT / custom, and any commercial-use restriction), headline capability, and the hardware needed to run it.
Cover Chinese labs (Alibaba Qwen, DeepSeek, Moonshot Kimi, Zhipu / Z.ai GLM, MiniMax, Tencent, ByteDance, Baidu and any newcomer), US labs (OpenAI gpt-oss and any successor, Meta Llama and its current open/closed stance, Google Gemma, Microsoft Phi, NVIDIA Nemotron, IBM Granite, Apple, xAI, Reflection AI, and Anthropic's stance), and others (Mistral, Cohere, and notable non-US/non-China labs).
Also answer: (a) which models are the default picks for small-scale fine-tuning (up to about 30B parameters) and which small or edge models matter; (b) the notable open non-LLM models in brief: image and video generation, speech-to-text, text-to-speech, embeddings and rerankers, OCR/document models, vision-language-action; (c) terminology: open-weight versus open-source (OSI Open Source AI Definition) and the license traps a practitioner doing client work must know.`,
  },
  {
    key: 'dynamics',
    title: 'US versus China in open-weight models, and the open versus closed gap, as of today',
    ask: `The user believes "US models are catching up to Chinese models" in open weights. Test that claim with evidence. Cover: (a) the 2025-2026 timeline of who led open-weight releases and when US labs responded; (b) current standings on independent leaderboards and usage data: Artificial Analysis open-weights rankings, LMArena, Hugging Face downloads and trending, OpenRouter token share, the ATOM Project, any a16z / OpenRouter / Stanford AI Index 2026 / State of AI Report 2026 data; (c) how many months open-weight models trail the closed frontier now and the trend; (d) policy drivers: the US AI Action Plan stance on open models, chip export controls, China's open strategy, EU AI Act obligations for open general-purpose models, and any 2026 US federal or state action; (e) restrictions or distrust of Chinese-origin models in US enterprise and government (bans, security findings, procurement rules) and how businesses treat model provenance; (f) what this means for a US practitioner choosing a base model for client work. Give dated evidence on both sides and say plainly whether the user's belief is right, partly right or wrong.`,
  },
  {
    key: 'toolchain',
    title: 'The practical toolchain and methods for customizing open-weight models, as of today',
    ask: `Cover: (a) the customization ladder and when each rung is the right call in 2026: prompt and context engineering, RAG, tool use, prompt optimization (DSPy / GEPA), LoRA / QLoRA / DoRA, full fine-tuning, distillation, reinforcement fine-tuning (GRPO, RFT), continued pretraining, model merging. State the current practitioner consensus on when fine-tuning is and is not worth it; (b) current status of the tools: Unsloth, Axolotl, Hugging Face Transformers / PEFT / TRL, MLX and mlx-lm on Apple silicon, llama.cpp and GGUF, Ollama, LM Studio, vLLM, SGLang, synthetic data tools, eval tools (Inspect, promptfoo, lm-evaluation-harness and others), experiment tracking, OpenPipe ART, Thinking Machines Tinker, and hosted fine-tuning and serving (Together, Fireworks, Baseten, Modal, RunPod, Lambda, Hugging Face Jobs and Endpoints, OpenAI fine-tuning, AWS Bedrock custom model import and others). Note anything deprecated, acquired or newly dominant in 2026; (c) real dollar costs now: GPU hourly prices, the typical cost to LoRA fine-tune a 4B, 12B and 30B model, and the cost to serve a small custom model for a client; (d) exactly what the hardware in the profile can do locally: which model sizes it can run for inference and which it can LoRA fine-tune with MLX, with the disk constraint called out; (e) how training datasets are built in practice, including the terms-of-service limits on training with outputs from closed models (OpenAI, Anthropic, Google); (f) the shortest credible first project: a first fine-tune a beginner can finish in a weekend, with the tool, model and steps named.`,
  },
  {
    key: 'market',
    title: 'Market demand for open-weight model customization skills: jobs and paying customers, this half-year',
    ask: `Be skeptical and include counter-evidence. Cover: (a) jobs: do Solutions Engineer, Forward-Deployed Engineer, Applied AI and AI Engineer postings in this half-year ask for fine-tuning, open-model or inference skills? Fetch several live postings (for example Together AI, Fireworks, Baseten, Modal, Hugging Face, NVIDIA, CoreWeave, Databricks, Anyscale, Cohere, Mistral, OpenAI, Anthropic) and quote the relevant requirement lines; give salary ranges where posted; (b) business demand: who actually pays for customized or private models (SMBs, regulated industries, on-premises buyers), what services are sold (private AI deployments, fine-tuned niche models, local AI appliances, evals), price points, and how realistic this is for a solo consultant today; (c) the counter-case: evidence that most businesses are better served by a frontier API plus RAG, and where fine-tuning still wins (cost at volume, latency, privacy, narrow tasks, structured output, on-device); (d) portfolio: which artifacts hiring managers and clients value (a published fine-tune with model card and evals, a write-up, a demo, open-source contributions); (e) any certification or course with real hiring signal. End with a ranked list of the three most cash-relevant ways for the person in the profile to use this skill within six months.`,
  },
  {
    key: 'quantum',
    title: 'Quantum computing and its convergence with AI/ML, as of today',
    ask: `Cover: (a) the state of quantum hardware as of today: the main 2025-2026 milestones (Google, IBM, Quantinuum, Microsoft, neutral-atom firms such as QuEra / Atom Computing / Pasqal, IonQ, PsiQuantum, DARPA Quantum Benchmarking Initiative), logical-qubit counts, credible claims of quantum advantage, and expert timelines for useful fault-tolerant machines; (b) AI for quantum: what is real today (neural decoders for error correction such as AlphaQubit, circuit optimization, calibration, NVIDIA CUDA-Q / NVQLink and similar); (c) quantum for AI (quantum machine learning): an honest assessment including dequantization results, barren plateaus and the data-loading problem, with named expert views, and any credible near-term advantage; (d) hybrid quantum-HPC-AI centers and what the large AI and chip companies are doing; (e) relevance for the person in the profile from 2026 to 2030: literacy versus practitioner depth, job market size, and whether post-quantum cryptography migration (NIST standards and deadlines) is the more practical adjacent topic; (f) the best free resources to reach literacy and the hours needed. Answer the user's question directly: how and when are the AI/ML and quantum worlds converging, with the uncertainty stated.`,
  },
  {
    key: 'frontier',
    title: 'Frontier scan: what else belongs on an AI learning roadmap for a builder, FDE candidate and founder, this month',
    ask: `Scan what is rising in the AI world as of today and rank what belongs on a 6 to 18 month learning roadmap for the person in the profile. Consider at least: agent engineering and harnesses, context engineering, evals and observability, agent protocols (MCP, A2A) and agent commerce / payments, AI security (prompt injection, agent permissions, red teaming), interpretability, inference optimization and economics, on-device and edge AI, voice and realtime agents, multimodal and video generation, computer-use agents, world models, robotics / physical AI / vision-language-action models, AI for science, synthetic data, continual learning and memory, AI governance and compliance (EU AI Act timelines, US state laws), compute / energy / datacenters / chips, sovereign AI, and the reinforcement-learning revival. Use evidence from the last 12 months: the newest State of AI Report and Stanford AI Index, hiring and funding data, major lab releases. For each of the top 12: what it is in one line, why now (dated evidence), relevance to jobs and to a founder, the cost to become literate versus proficient, and a verdict of learn now / track / ignore for now. Put the topics you would tell him to ignore in recommendations with the reason.`,
  },
  {
    key: 'resources',
    title: 'Learning resources and course design for going from API builder to open-weight model customizer, this month',
    ask: `Cover: (a) the best current resources, free first, for going from "builder who calls APIs" to "can fine-tune, evaluate and deploy open-weight models". Check each is live and current and note its last update: Hugging Face LLM Course and smol-course, Unsloth docs and notebooks, Karpathy Zero to Hero / nanochat / Eureka Labs, Raschka "Build a Large Language Model (From Scratch)" and "Build a Reasoning Model", Chip Huyen "AI Engineering", fast.ai, DeepLearning.AI short courses on fine-tuning, Stanford CS336, Maxime Labonne's LLM course and "LLM Engineer's Handbook", the Hamel Husain / Shreya Shankar evals course, MLX examples, Google Gemma cookbook, OpenAI gpt-oss fine-tuning guides, and any strong resource new this year; (b) the learning-science evidence for adults doing technical self-study, including what is known for adults with attention difficulties: retrieval practice, spacing, project-based learning, session length, accountability and public commitment, with citations; (c) what makes Duolingo-style apps work, their documented limits for technical skills (recognition versus production) and the evidence on why self-built learning systems get abandoned; (d) concrete design recommendations for a course app this person will actually use; (e) a proposed 12-week sequence at about 6 to 8 hours per week where every two weeks ends in a public artifact (for example a published fine-tune with a model card and evals).`,
  },
]

const researchPrompt = t => `Research topic: ${t.title}

${PROFILE}

${t.ask}

${RULES}`

const verifyPrompt = (t, r) => `You are an independent verifier. You did not do this research and you should not trust it. Topic: ${t.title}

${RULES}

Your job: try to refute or correct the findings below. Independently search and fetch sources for every finding rated "likely" or "unverified", and for at least the eight most consequential findings rated "verified" (the ones a person would act on: model names and release dates, licenses, prices, rankings, timelines, job requirements). Do not just re-open the researcher's link: look for a second source and for contradicting or more recent evidence as of today. Then look for what the researcher missed: a major release, a newer development, a contradicting data point. Return a verdict per checked claim (correction is an empty string when confirmed), the missed items, and one paragraph on overall reliability. Default to "unverifiable" when you cannot confirm.

Researcher's summary: ${r.summary}

Researcher's findings (JSON):
${JSON.stringify(r.findings)}

Researcher's stated gaps: ${JSON.stringify(r.gaps)}`

const research = await pipeline(
    TOPICS,
    t => agent(researchPrompt(t), { label: `research:${t.key}`, phase: 'Research', model: 'sonnet', effort: 'high', schema: FINDINGS_SCHEMA }),
    (r, t) => {
      if (!r) return { topic: t.key, research: null, verification: null }
      return agent(verifyPrompt(t, r), { label: `verify:${t.key}`, phase: 'Verify', model: 'opus', effort: 'high', schema: VERDICT_SCHEMA })
        .then(v => ({ topic: t.key, research: r, verification: v }))
    },
  )

const failed = research.map((x, i) => (!x || !x.research || !x.verification) ? TOPICS[i].key : null).filter(Boolean)
if (failed.length) log(`Incomplete topics (research or verification missing): ${failed.join(', ')}`)

return { today: TODAY, research, failed }
