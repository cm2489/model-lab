# Lab 0 · Setup

**You finish with:** an open model running on your own Mac, one tiny training run done, and your Mac's real speed and memory numbers written down.

**Time:** about 90 minutes, in four steps. Stop after any step.

**You need:**

- An Apple-silicon Mac with 16 GB of memory or more.
- 6 GB of free disk.
- [Homebrew](https://brew.sh), if uv is not installed yet.
- This repository on your machine. If you do not have it: `git clone https://github.com/cm2489/model-lab.git ~/Projects/model-lab`

Every "You should see" block is real output from a 2021 MacBook Pro (M1 Max, 32 GB), run on October 6, 2026. An independent agent re-ran every step from this page the same day and got the same loss values to the digit. Blocks show the last lines of the output. Your speeds will differ a little.

---

<a id="step-1"></a>
## Step 1 · Install the tools (20 min)

1. Open Terminal and go to the repository.

   ```bash
   cd ~/Projects/model-lab
   ```

2. Check for uv. If the command prints a version, skip to 4.

   ```bash
   uv --version
   ```

3. Install uv with Homebrew.

   ```bash
   brew install uv
   ```

4. Build the project's Python environment.

   ```bash
   uv sync
   ```

5. Check that the training tool loads.

   ```bash
   uv run python -c "import sys, mlx_lm; print(sys.version.split()[0], 'mlx-lm', mlx_lm.__version__)"
   ```

   **You should see**

   ```
   3.12.15 mlx-lm 0.32.0
   ```

   Your Python patch number may differ. It must start with 3.12.

6. Start your numbers file and write down which Mac you have.

   ```bash
   cp labs/00-setup/MY-NUMBERS.template.md labs/00-setup/MY-NUMBERS.md
   system_profiler SPHardwareDataType | grep -E "Model Name|Chip|Memory"
   ```

   **You should see** three lines like these. Copy them into `MY-NUMBERS.md`, with today's date.

   ```
         Model Name: MacBook Pro
         Chip: Apple M1 Max
         Memory: 32 GB
   ```

**What you just installed**

- **uv** installs Python versions and packages. It keeps everything for this project inside `.venv/` and leaves your Mac's own Python alone.
- **MLX** is Apple's library for running and training models on Apple-silicon chips.
- **mlx-lm** sits on top of MLX. It downloads, runs and fine-tunes language models.

**Check yourself.** Why does this lab use uv's Python and not the one that came with the Mac?

<details><summary>Answer</summary>

mlx-lm 0.32.0 needs Python 3.11 or newer. The Python that came with the Mac used here is 3.9.6. uv installs a newer one beside it without changing the system.

</details>

**Done when:** sub-step 5 prints a 3.12 Python and an mlx-lm version, and `MY-NUMBERS.md` has your Mac's three lines.

---

<a id="step-2"></a>
## Step 2 · Run a small model on your Mac (25 min)

1. Check your free disk space. You need at least 6 GB in the "Avail" column. Write that number in `MY-NUMBERS.md`.

   ```bash
   df -h /System/Volumes/Data
   ```

2. Download the model. It is 3.0 GB and takes a few minutes.

   ```bash
   uv run hf download mlx-community/Qwen3.5-4B-4bit
   ```

3. Predict before you run: how many words a second do you expect from a laptop? Say a number out loud.

4. Ask it a question.

   ```bash
   uv run mlx_lm.generate --model mlx-community/Qwen3.5-4B-4bit --max-tokens 160 --prompt "In two sentences, what does a 4-bit quantized model trade away, and what does it gain?"
   ```

   **You should see** something like this. The wording will differ.

   ```
   ==========
   Thinking Process:

   1.  **Analyze the Request:**
       *   Topic: 4-bit quantized models (in the context of machine learning/LLMs).
       *   Constraint: Exactly two sentences.
       ...
   ==========
   Prompt: 32 tokens, 13.314 tokens-per-sec
   Generation: 160 tokens, 93.579 tokens-per-sec
   Peak memory: 2.581 GB
   ```

   It never answered. This model thinks before it answers, and the thinking used all 160 tokens.

5. Run it again with thinking turned off.

   ```bash
   uv run mlx_lm.generate --model mlx-community/Qwen3.5-4B-4bit --max-tokens 160 --chat-template-config '{"enable_thinking": false}' --prompt "In two sentences, what does a 4-bit quantized model trade away, and what does it gain?"
   ```

   **You should see**

   ```
   ==========
   A 4-bit quantized model trades away high-precision numerical accuracy and fine-grained
   semantic nuance, which can lead to slight degradations in reasoning and factual correctness.
   In exchange, it gains significantly reduced memory footprint and faster inference speeds,
   enabling deployment on resource-constrained hardware.
   ==========
   Prompt: 34 tokens, 200.245 tokens-per-sec
   Generation: 58 tokens, 94.841 tokens-per-sec
   Peak memory: 2.555 GB
   ```

6. Write two numbers from this last run in `MY-NUMBERS.md`: Generation tokens-per-sec and Peak memory.

**Read the model's name**

`mlx-community/Qwen3.5-4B-4bit` has four parts.

| Part | Meaning |
|---|---|
| `mlx-community` | The account that published this copy. It converts models to MLX format. |
| `Qwen3.5` | The model family, made by Alibaba. |
| `4B` | About 4 billion parameters (weights). |
| `4bit` | Each weight is stored in about 4 bits, down from 16. |

**Where the license lives.** The copy you downloaded has no model card and states no license. The original, `Qwen/Qwen3.5-4B`, is tagged Apache-2.0 and ships a LICENSE file. Before you use any converted copy in real work, read the license on the original.

Download models only from accounts you can identify. Impostor accounts publish altered copies under real model names.

**Check yourself.** The download is 3.0 GB. About how big is the same model at full precision?

<details><summary>Answer</summary>

About three times bigger. The full-precision Qwen3.5-4B is 9.3 GB. Quantizing to 4 bits gives up a little accuracy and gets a model about a third of the size.

</details>

**Done when:** the model answered you with thinking off, and `MY-NUMBERS.md` has your free disk, generation speed and peak memory.

---

<a id="step-3"></a>
## Step 3 · Run a 20-step training test (30 min)

This is a smoke test. It proves training works on your Mac. It does not make a useful model.

1. Look at the training data. There are 40 examples: a bill title in, a policy area out.

   ```bash
   head -1 labs/00-setup/smoke/train.jsonl
   ```

   **You should see**

   ```
   {"messages": [{"role": "user", "content": "Which Congress.gov policy area does this bill belong to? Answer with the policy area only.\n\nBill title: RESEARCHER Act"}, {"role": "assistant", "content": "Science, Technology, Communications"}]}
   ```

2. Ask the untrained model about one real bill. The public record files this bill (S. 4043, 119th Congress) under "Armed Forces and National Security".

   ```bash
   uv run mlx_lm.generate --model mlx-community/Qwen3.5-4B-4bit --max-tokens 30 --chat-template-config '{"enable_thinking": false}' --prompt "Which Congress.gov policy area does this bill belong to? Answer with the policy area only. Bill title: Health Care for Homeless Veterans Act"
   ```

   **You should see**

   ```
   ==========
   Health and Human Services
   ==========
   ```

   That is not one of the Congress.gov policy areas. The model made up a name.

3. Predict: after 20 training steps on 40 examples, will the loss go down? Will the answer above change?

4. Train.

   ```bash
   uv run python labs/00-setup/train_smoke.py
   ```

   **You should see** these last lines. A box drawn to your terminal's width comes first.

   ```
   │    model           mlx-community/Qwen3.5-4B-4bit
   │    type            lora · 8 layers · rank 8
   │    dataset         labs/00-setup/smoke
   │    optimizer       adam · lr 1.0e-05
   │    batch · iters   1 · 20
   │    max seq         2,048
   Trainable parameters: 0.096% (4.058M/4205.750M)
     iter   train_loss     tok/s     tokens
        1    val 3.092    0.74s
        5    2.662 ▼       41      0.3k
       10    1.502 ▼       82      0.6k
       15    1.027 ▼      104      0.8k
       20    val 0.835    0.75s
       20    0.716 ▼       88      1.1k
   train ██████████████████████████████ 100% ·    20/20

   Model:       mlx-community/Qwen3.5-4B-4bit
   Wall time:   19 seconds for 20 steps (includes loading the model)
   Peak memory: 6.50 GB
   ```

5. Write five numbers in `MY-NUMBERS.md`: the two `val` losses, the `tok/s` at step 15, the wall time and the peak memory.

6. Look at what training produced.

   ```bash
   ls -l adapters/smoke
   ```

   **You should see** two files. The trained weights are `adapters.safetensors`, 16,247,908 bytes (16 MB). Write that size in `MY-NUMBERS.md`. The 3 GB model is unchanged.

7. Ask the same question, now with the adapter loaded.

   ```bash
   uv run mlx_lm.generate --model mlx-community/Qwen3.5-4B-4bit --adapter-path adapters/smoke --max-tokens 30 --chat-template-config '{"enable_thinking": false}' --prompt "Which Congress.gov policy area does this bill belong to? Answer with the policy area only. Bill title: Health Care for Homeless Veterans Act"
   ```

   **You should see**

   ```
   ==========
   Health
   ==========
   ```

   "Health" is a real policy area, so the model learned the label format. It is still the wrong one for this bill.

**Read the training output**

- **Trainable parameters: 0.096%.** LoRA froze the model and trained about 4 million added weights out of 4.2 billion.
- **val 3.092, then val 0.835.** The loss on examples it did not train on fell.
- **Peak memory 6.50 GB.** Training needed about two and a half times the memory of running.

`train_smoke.py` is a 40-line wrapper. Open it. The real command is in the note at the top of the file. The wrapper only adds the Model, Wall time and Peak memory lines.

**Check yourself.** The loss went down and the answer changed. Did the model get better at tagging bills?

<details><summary>Answer</summary>

You cannot tell yet. One example and a falling loss prove nothing about the task. You need a test set the model never trained on, scored the same way before and after. That is Lab 1.

</details>

**Done when:** your run printed a wall time and a peak memory, `adapters/smoke/adapters.safetensors` exists, and your numbers are in the file.

---

<a id="step-4"></a>
## Step 4 · Write down what you measured (15 min)

1. Open `labs/00-setup/MY-NUMBERS.md`. Check that every row of the table has your number. The reference column is the M1 Max run above.

2. Write three sentences in the file for a buyer who is not technical: what did you just do, and why does it matter that it ran on a laptop?

3. Write one thing that surprised you.

4. Delete the test adapter. It was only a smoke test.

   ```bash
   rm -rf adapters/smoke
   ```

**Check yourself.** Read your three sentences aloud. Would a buyer who has never heard the word "parameter" follow every one?

**Done when:** `labs/00-setup/MY-NUMBERS.md` has a number in every row, your three sentences and your one surprise.

**Next:** Lab 1, "Evals first". You build the test set that tells you whether a model is any good.
