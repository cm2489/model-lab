# Lab 2 · First fine-tune

**Aim:** fine-tune a 4B model with LoRA and show, on your test set, what changed.

**You ship:** a fine-tuned model and its model card on Hugging Face.

**Time:** about 4 hours 40 minutes, in seven steps. Stop after any step.

**Before you start:** Lab 1 is done. You have the test set, the harness and a baseline score. Free disk is 5 GB or more for steps 1 to 5, and 25 GB for step 6.

**The one rule of this lab:** training uses batch size 1. On a 32 GB Mac, a batch of 4 pushed the machine into swap and nearly filled the disk. The reason is in step 3.

Every "You should see" block is real output from a 2021 MacBook Pro (M1 Max, 32 GB), run on October 6, 2026 (steps 1 to 5) and October 7, 2026 (step 6), Eastern Time. Blocks show the last lines of the output.

---

<a id="step-1"></a>

## Step 1 · What LoRA changes in a model

**Do this:** work out, with numbers from your own Lab 0 run, what a fine-tune touches. **About 30 minutes.**

1. Open `labs/00-setup/MY-NUMBERS.md`. Find two things you measured there: the adapter file size and peak memory while training. The third number is in your Lab 0 training output: "Trainable parameters: 0.096%".

2. Do this arithmetic on paper or in your head.

   - The model has 4,205.75 million weights. LoRA trained 4.058 million. What fraction is that?
   - The base model file is 3.0 GB. The adapter is 16 MB. How many adapters fit in the space of one model?

3. Read these two ideas. They are all the theory this lab needs.

   - **Full fine-tuning** changes every weight. You get a whole new 3 GB model for every task.
   - **LoRA** freezes every weight. Beside some layers it adds two small matrices and trains only those. The adapter file holds just the small matrices. At run time they are added on top of the frozen model.

4. Predict two things and write them down. You check both in step 4.

   - The untuned model scored 56.7% on your test set, with every label listed in the prompt. What will the tuned model score?
   - Will the tuned model still need the label list in the prompt?

**Optional reading, 15 minutes:** "LoRA Without Regret" on the Thinking Machines blog (thinkingmachines.ai/blog). If neural-network weights are hazy, do Foundations session 4 first: `foundations/sessions/s4-how-models-learn.md`.

**Check yourself.** One base model, ten clients, ten tasks. With LoRA, what do you store and what do you load?

<details><summary>Answer</summary>

One 3 GB base model and ten small adapters, about 16 MB each. You load the base once and swap the adapter per client. With full fine-tuning you would store and serve ten 3 GB models.

</details>

**Done when:** your two predictions are written down.

---

<a id="step-2"></a>

## Step 2 · Prepare the training data

**Do this:** turn the labelled bills into the chat format the training tool reads. **About 45 minutes.**

1. Build the training files.

   ```bash
   make tune-data
   ```

   **You should see**

   ```text
   train: 2341 examples, 31 labels, 26 to 80 per label
   valid: 200 examples
   golden titles in train or valid: 0
   wrote data/lora/train.jsonl and valid.jsonl
   ```

2. Read one training example.

   ```bash
   head -1 data/lora/train.jsonl
   ```

   **You should see** one line: a `user` message with a short question and a bill title, then an `assistant` message that is only the policy area.

   ```text
   {"messages": [{"role": "user", "content": "Which Congress.gov policy area does this bill belong to? Reply with the policy area only.\n\nBill title:\nTo direct the Attorney General to establish within the Department of Justice the Office of the National Coordinator to Counter Antisemitism, and for other purposes."}, {"role": "assistant", "content": "Civil Rights and Liberties, Minority Issues"}]}
   ```

3. Open `tune/prepare.py` and find the answers to these three questions. Each is a design choice you may be asked to defend.

   - Why does the training prompt leave out the list of 32 labels?
   - Why are there at most 80 examples per label, when "Health" has 1,284 available?
   - Why does the script stop if a training title is also in the golden set?

4. Count how much shorter the short prompt is. The baseline's prompt size is in its saved predictions.

   ```bash
   uv run python -c "
   import json
   rows = [json.loads(l) for l in open('results/qwen3.5-4b-4bit-golden-baseline/predictions.jsonl')]
   print('prompt tokens per bill, label-list prompt:', round(sum(r['input_tokens'] for r in rows) / len(rows)))"
   ```

   **You should see**

   ```text
   prompt tokens per bill, label-list prompt: 250
   ```

   You measure the short prompt in step 4.

**Check yourself.** The cap gives every label at most 80 examples. What would the model learn if you trained on all 11,640 rows as they are?

<details><summary>Answer</summary>

It would see "Health" about 50 times as often as the rarest label, and it would learn to guess the common labels when unsure. Accuracy on rare labels would fall. Capping trades some total data for balance.

</details>

**Done when:** `data/lora/train.jsonl` exists and you can answer the three questions in sub-step 3 in one sentence each.

---

<a id="step-3"></a>

## Step 3 · Train: your first LoRA run

**Do this:** train for 1,200 steps, one example per step and a weight update every four, so 300 updates drawn from the 2,341 examples. **About 45 minutes, of which the run is about 13 minutes.**

1. Make room. Training needs memory, and a Mac that runs short of memory writes swap files to disk.

   - Quit apps you are not using, especially browsers with many tabs.
   - Check free disk. You need 5 GB or more in the "Avail" column.

   ```bash
   df -h /System/Volumes/Data
   ```

2. Predict: the validation loss starts near 2.7. Where will it be after 1,200 steps?

3. Train.

   ```bash
   make tune
   ```

   **You should see** a box with the settings, then a loss table, then three summary lines.

   ```text
   │    model           mlx-community/Qwen3.5-4B-4bit
   │    type            lora · 8 layers · rank 8
   │    dataset         data/lora
   │    optimizer       adam · lr 1.0e-04
   │    batch · iters   1 · 1,200
   │    max seq         512
   Trainable parameters: 0.096% (4.058M/4205.750M)
     iter   train_loss     tok/s     tokens
        1    val 2.722    22.83s
      100    0.944 ▼       11      0.8k
      200    0.666 ▼       13      1.6k
      300    0.413 ▼       14      2.4k
      400    val 0.262    16.76s
      400    0.281 ▼       13      3.2k
      500    0.334 ▲       14      4.0k
      600    0.285 ▼       14      4.9k
      700    0.268 ▼       13      5.6k
      800    val 0.346    16.75s
      800    0.329 ▲       14      6.5k
      900    0.524 ▲       14      7.3k
     1000    0.382 ▼       14      8.1k
     1100    0.418 ▲       14      8.9k
     1200    val 0.162    16.74s
     1200    0.198 ▼       15      9.7k
   train ██████████████████████████████ 100% · 1,200/1,200
   Model:       mlx-community/Qwen3.5-4B-4bit
   Adapter:     adapters/policy-area
   Wall time:   13.3 minutes for 1200 steps
   Peak memory: 7.54 GB
   ```

4. While it runs, open Activity Monitor and watch the Memory tab. The "Memory Pressure" graph should stay green.

5. When it ends, write down four numbers: the first and last `val` loss, the wall time and the peak memory.

**Why batch size 1.** `make tune` runs the command printed at the top of `tune/train.py`. Read it. Two settings keep this run inside a 32 GB Mac.

- `--batch-size 1 --grad-accumulation-steps 4`: the model sees one example at a time and updates its weights every four. That acts like a batch of 4 at the memory cost of 1.
- The short prompt: each training example is about 70 tokens with its reply. With the label list in every example it is about 250.

These were measured on this Mac on October 6, 2026.

| Run | Peak memory | What happened |
|---|---|---|
| Batch 1, short prompt (this lab) | 7.5 GB | Fine |
| Batch 2, label-list prompt, 8 layers | 22.8 GB | Ran, at about 4 seconds a step |
| Batch 4, short prompt, 8 layers | not recorded | Heavy swap. Free disk fell from 18 GB to 4 GB. Stopped by hand. |
| Batch 4, label-list prompt, 16 layers | none | Crashed: "Insufficient Memory" |

**Check yourself.** Your loss table shows `train_loss` bouncing up and down between reports while `val` falls. Is the run broken?

<details><summary>Answer</summary>

No. With batch size 1 each report averages few examples, so the training loss is noisy. The validation loss is measured on the same 100 examples each time. Trust the trend in `val`.

</details>

**Done when:** `adapters/policy-area/adapters.safetensors` exists and your four numbers are written down.

---

<a id="step-4"></a>

## Step 4 · Score the tuned model

**Do this:** put the tuned model through the same test as the baseline. **About 30 minutes.**

1. Score the tuned model on the golden set. It gets the short prompt it was trained with.

   ```bash
   make eval-tuned
   ```

   **You should see** 150 progress lines, then

   ```text
   run: results/qwen3.5-4b-4bit-tuned-golden
   accuracy 74.7% (112/150)   macro-F1 0.749   invalid 0.7% (1)
   latency p50 0.215s  p90 0.27s   tokens/s 96.6   wall 35s
   cost per 1,000 bills: 0.0  (local run: $0 marginal cost (hardware and electricity not counted))
   ```

2. Score the untuned model with the same short prompt. This shows what the fine-tune taught.

   ```bash
   uv run python -m evals.run --backend mlx --model mlx-community/Qwen3.5-4B-4bit --prompt short --split golden --run-name qwen3.5-4b-4bit-golden-short-prompt
   ```

   **You should see**

   ```text
   run: results/qwen3.5-4b-4bit-golden-short-prompt
   accuracy 10.7% (16/150)   macro-F1 0.087   invalid 86.7% (130)
   latency p50 0.182s  p90 0.221s   tokens/s 141.8   wall 30s
   cost per 1,000 bills: 0.0  (local run: $0 marginal cost (hardware and electricity not counted))
   ```

3. Open the score table and read the rows side by side. The table below is the summary; the full table is `results/README.md`, and each run's `score.md` has its token counts under "Average tokens per bill".

   ```bash
   cat results/README.md
   ```

   | Model | Prompt | Accuracy | Invalid replies | Prompt tokens per bill |
   |---|---|---|---|---|
   | Untuned | lists all 32 labels | 56.7% | 2 | 250 |
   | Untuned | short | 10.7% | 130 | 65 |
   | Tuned | short | 74.7% | 1 | 65 |

4. Check your two predictions from step 1.

5. Read the tuned model's misses, the same way you read the baseline's in Lab 1.

   ```bash
   uv run python -m evals.misses results/<your tuned run folder>/predictions.jsonl
   ```

   Compare with your Lab 1 notes. Which of your three failure causes did the fine-tune fix? Which are still there?

**What the three rows say**

- Without the label list, the untuned model makes up label names. Most of its replies are invalid.
- The tuned model learned the label names. It needs no list.
- The short prompt is about a quarter of the length (65 tokens against 250), so each bill costs about a quarter as much to read. On a hosted model you pay for that difference on every request.

**Check yourself.** The tuned model was scored with a different prompt from the baseline. Is the comparison fair?

<details><summary>Answer</summary>

Yes, if you say so plainly. Each model gets the prompt it works best with, and both are scored on the same 150 bills by the same parser. The table names the prompt for every row. What would be unfair is hiding the difference, or scoring on bills the tuned model trained on.

</details>

**Done when:** your tuned run matched the committed one (`git diff --stat results/` prints nothing, or shows exactly what differed) and you have named which Lab 1 failure causes the fine-tune fixed.

---

<a id="step-5"></a>

## Step 5 · Change one thing and run again

**Do this:** run one experiment that changes exactly one setting. **About 45 minutes.**

1. Pick one. Change only that.

   | Experiment | Command | Run by the kit builder? |
   |---|---|---|
   | A quarter of the training | `uv run python -m tune.train --iters 300 --name quick` | Yes. Output below. |
   | Twice the layers | `uv run python -m tune.train --num-layers 16 --name deep` | No. Not verified. Expect more memory; watch Activity Monitor and stop the run if pressure turns red. |
   | Half the learning rate | `uv run python -m tune.train --learning-rate 5e-5 --name slow` | No. Not verified. |

2. Predict the result before you run it: better, worse or the same, and by about how much.

3. Run it. Check free disk first, as in step 3.

4. Score it. Use the name you gave it.

   ```bash
   uv run python -m evals.run --backend mlx --model mlx-community/Qwen3.5-4B-4bit --adapter-path adapters/quick --prompt short --split golden --run-name qwen3.5-4b-4bit-tuned-quick-golden
   ```

   Name the run after the adapter, as above, so the table shows which adapter each row scores.

   **You should see**, for the "quarter of the training" experiment:

   ```text
   run: results/qwen3.5-4b-4bit-tuned-quick-golden
   accuracy 54.0% (81/150)   macro-F1 0.490   invalid 14.7% (22)
   latency p50 0.227s  p90 0.293s   tokens/s 82.1   wall 40s
   cost per 1,000 bills: 0.0  (local run: $0 marginal cost (hardware and electricity not counted))
   ```

5. Write one sentence: what did this one change do, and would you keep it?

**Check yourself.** Your experiment scored 2 bills better out of 150. Is it better?

<details><summary>Answer</summary>

You cannot say. With 150 bills, one bill is 0.7 points, and a difference of two or three bills is inside the noise. To trust a small gain you need a bigger test set or several runs. A large gap, like untuned to tuned, is real.

</details>

**Done when:** `results/README.md` has a row for your experiment and you wrote your one sentence.

---

<a id="step-6"></a>

## Step 6 · Swap the base model

Every block in this step was run on October 8, 2026 (Eastern), on the same M1 Max, by the kit builder, and re-run from this page the same morning by an agent that did not write it: the same scores, the same losses to the digit, and the same reply on all 150 test bills. Only timings moved (training 6.6 minutes against 6.8).

**You need:** `data/lora/` from step 2 (`make tune-data`). It is not in the repository; a fresh clone must run step 2 first.

**Do this:** convert a model from a different lab yourself, run the same fine-tune on it and compare. **About 40 minutes, of which the download is about 9 minutes and training about 7.**

1. Check free disk. You need 25 GB or more: 16 GB for the original, 4 GB for your converted copy, and room to train.

   ```bash
   df -h /System/Volumes/Data
   ```

   **You should see** 25 GB or more in the "Avail" column. The kit builder had 64 GB.

   ```text
   Filesystem      Size    Used   Avail Capacity iused ifree %iused  Mounted on
   /dev/disk3s5   460Gi   371Gi    64Gi    86%    5.6M  673M    1%   /System/Volumes/Data
   ```

2. Read the license on the original, `google/gemma-4-E4B-it`, on Hugging Face. Converted copies on the Hub carry their own license tags, and they can differ from the original's. That is why this lab converts from the original: the license you work under is Google's and nothing else's.

   ```bash
   curl -s https://huggingface.co/api/models/google/gemma-4-E4B-it | python3 -c 'import json,sys; print(json.load(sys.stdin).get("cardData",{}).get("license"))'
   ```

   **You should see**

   ```text
   apache-2.0
   ```

3. Download the original. It is one weights file of 15.99 GB, in full precision.

   ```bash
   uv run hf download google/gemma-4-E4B-it
   ```

   **You should see** the folder it saved to. It took the kit builder 8 minutes 47 seconds on a home connection. A warning about unauthenticated requests is about rate limits; the download works without a token.

   ```text
   path=~/.cache/huggingface/hub/models--google--gemma-4-E4B-it/snapshots/ee0ef6023621cff504d758262d4e04895a5af4a2
   ```

4. Convert it to a 4-bit MLX copy in `models/`. The folder is in `.gitignore`; weights never go in git.

   ```bash
   uv run mlx_lm.convert --hf-path google/gemma-4-E4B-it --mlx-path models/gemma-4-e4b-it-4bit -q --q-bits 4 --q-group-size 64
   du -sh models/gemma-4-e4b-it-4bit
   ```

   **You should see**, after about 15 seconds,

   ```text
   [INFO] Loading
   [INFO] Using dtype: bfloat16
   [INFO] Quantizing
   [INFO] Quantized model with 4.501 bits per weight.
   3.9G	models/gemma-4-e4b-it-4bit
   ```

   `-q` turns on 4-bit quantization. `--q-bits 4 --q-group-size 64` are the settings the `mlx-community` copy states in its `config.json`, so your copy is quantized the same way. The weights file is 4.20 GB. Gemma 4 E4B also reads images and audio; `mlx_lm.convert` keeps only the text model, which is all this task uses.

   Check that it loads and answers:

   ```bash
   uv run mlx_lm.generate --model models/gemma-4-e4b-it-4bit --max-tokens 40 --prompt "In one sentence, what is a bill's policy area?"
   ```

   **You should see**

   ```text
   ==========
   <|channel>thought
   1.  **Analyze the Request:** The user wants to know the "policy area" of a bill, and the answer must be in "one sentence."
   2.  **
   ==========
   Prompt: 29 tokens, 20.276 tokens-per-sec
   Generation: 40 tokens, 75.432 tokens-per-sec
   Peak memory: 4.305 GB
   ```

   It starts thinking and runs out of its 40 tokens. That is fine: the model loads and writes. The harness turns thinking off.

5. Score it untuned, with the label-list prompt.

   ```bash
   uv run python -m evals.run --backend mlx --model models/gemma-4-e4b-it-4bit --split golden --run-name gemma-4-e4b-it-4bit-own-golden-baseline
   ```

   **You should see** 150 progress lines, then

   ```text
   run: results/gemma-4-e4b-it-4bit-own-golden-baseline
   accuracy 60.0% (90/150)   macro-F1 0.590   invalid 1.3% (2)
   latency p50 0.32s  p90 0.354s   tokens/s 94.9   wall 51s
   cost per 1,000 bills: 0.0  (local run: $0 marginal cost (hardware and electricity not counted))
   ```

   In `results/README.md` the Model column reads `models/gemma-4-e4b-it-4bit` (converted here from `google/gemma-4-E4B-it`). The harness reads the source from the `README.md` that `mlx_lm.convert` wrote.

6. Fine-tune it with the same data and settings.

   ```bash
   uv run python -m tune.train --model models/gemma-4-e4b-it-4bit --name policy-area-gemma-own
   ```

   **You should see** the same settings box with the new model name, then

   ```text
   Trainable parameters: 0.047% (3.473M/7463.013M)
     iter   train_loss     tok/s     tokens
        1    val 11.766    19.43s
      100    1.948 ▼       17      0.6k
      200    0.479 ▼       22      1.2k
      300    0.415 ▼       22      1.8k
      400    val 0.277    18.78s
      400    0.327 ▼       22      2.3k
      500    0.239 ▼       23      2.9k
      600    0.222 ▼       23      3.5k
      700    0.208 ▼       21      4.1k
      800    val 0.176    18.83s
      800    0.208 ▼       22      4.7k
      900    0.205 ▼       22      5.3k
     1000    0.214 ▲       22      5.9k
     1100    0.189 ▼       21      6.4k
     1200    val 0.191    20.93s
     1200    0.197 ▲       22      7.0k
   train ██████████████████████████████ 100% · 1,200/1,200
   Model:       models/gemma-4-e4b-it-4bit
   Adapter:     adapters/policy-area-gemma-own
   Wall time:   6.8 minutes for 1200 steps
   Peak memory: 5.11 GB
   ```

   Two numbers differ from Qwen. The first `val` loss is 11.8, not 2.7, and it falls below 0.3 by step 400. The model counts 7,463 million weights, though its name says 4B. Google's model card explains: the "E" means "effective", and many of those weights are per-layer lookup tables, not weights the model computes with.

7. Score the tuned version.

   ```bash
   uv run python -m evals.run --backend mlx --model models/gemma-4-e4b-it-4bit --adapter-path adapters/policy-area-gemma-own --prompt short --split golden --run-name gemma-4-e4b-it-4bit-own-tuned-golden
   ```

   **You should see** 150 progress lines, then

   ```text
   run: results/gemma-4-e4b-it-4bit-own-tuned-golden
   accuracy 70.7% (106/150)   macro-F1 0.684   invalid 0.0% (0)
   latency p50 0.165s  p90 0.224s   tokens/s 83.0   wall 29s
   cost per 1,000 bills: 0.0  (local run: $0 marginal cost (hardware and electricity not counted))
   ```

8. Put the two models side by side: untuned score, tuned score, speed, peak memory, download size, license, and who made it.

   | | Qwen3.5-4B | Gemma 4 E4B |
   |---|---|---|
   | Made by | Alibaba (Qwen team) | Google |
   | Copy you run | `mlx-community/Qwen3.5-4B-4bit` | `models/gemma-4-e4b-it-4bit`, converted here |
   | Untuned, label-list prompt | 56.7% (2 invalid) | 60.0% (2 invalid) |
   | Tuned, short prompt | 74.7% (1 invalid) | 70.7% (0 invalid) |
   | Speed untuned, tokens/s | 116 | 95 |
   | Speed tuned, tokens/s | 97 | 83 |
   | Training wall time | 13.3 minutes | 6.8 minutes |
   | Training peak memory | 7.54 GB | 5.11 GB |
   | Download (weights file) | 3.03 GB | 15.99 GB original, 4.20 GB after conversion |
   | License, original | Apache-2.0 | Apache-2.0 |

   The Qwen download size comes from the Hugging Face API on October 7, 2026. Speeds come from `results/README.md`.

   The `mlx-community/gemma-4-e4b-it-4bit` copy scored 60.0% untuned and 70.7% tuned (the `gemma-4-e4b-it-4bit-golden-baseline` and `gemma-4-e4b-it-4bit-tuned-golden` rows). Your copy scores the same, and gives the same reply on all 150 bills in both runs: no difference at all, let alone one outside noise.

**What the table says**

- Gemma starts 3.3 points ahead and ends 4 points behind. Both gaps are 5 or 6 bills out of 150: inside the noise you met in step 5.
- The big gap is untuned to tuned, and both families show it.
- Gemma trained in half the time on less memory, but answers more slowly.
- Converting it yourself costs a 16 GB download and 15 seconds. It buys a copy whose license you read at the source.

**Check yourself.** A client will not accept a model made in China. How long does it take you to switch, and what do you need to re-run?

<details><summary>Answer</summary>

About as long as this step: download, convert, train, score. The data, the harness, the test set and the settings do not change. That is what the harness buys you. You re-run training and scoring, then compare the rows.

</details>

**Done when:** `results/README.md` has rows for both model families, including your own converted Gemma, and you have a side-by-side table.

---

<a id="step-7"></a>

## Step 7 · Write the model card and publish

**Not verified by the kit builder.** Publishing needs your Hugging Face account and token. The command options were checked against `hf --help`. The upload itself has not been run.

**Do this:** publish the adapter with a card that states its numbers and its limits. **About 45 minutes.**

1. Copy the card template into the adapter folder. Hugging Face shows `README.md` as the model card.

   ```bash
   cp labs/02-first-fine-tune/MODEL_CARD.template.md adapters/policy-area/README.md
   ```

2. Fill in every `FILL_IN` from your own runs. Where each one lives:

   - Accuracy, macro-F1, invalid count and seconds per bill: the row in `results/README.md`.
   - Prompt tokens per bill: "Average tokens per bill" in that run's `score.md`.
   - The frontier-model row: the Lab 1 step 4 run, if you did it. Leave the row out if you did not.
   - Your two worst labels: the "Per label" section of the tuned run's `score.md`.
   - Training examples (2,341) and steps (1,200): the `make tune-data` and `make tune` output.
   - Adapter size: `ls -l adapters/policy-area`.
   - The "Limits" section matters most. Use what you saw in step 4.

3. Check nothing private is in the folder. It should hold the card, `adapter_config.json`, `adapters.safetensors` and numbered checkpoint files.

   ```bash
   ls -l adapters/policy-area
   ```

4. Delete the numbered checkpoints. Only the final weights are needed.

   ```bash
   rm adapters/policy-area/0*_adapters.safetensors
   ```

5. Log in to Hugging Face. The command's help says it logs in from your browser or with a token from huggingface.co/settings/tokens. The exact flow is not verified by the kit builder.

   ```bash
   uv run hf auth login
   ```

6. Upload. Replace `YOUR_NAME` with your Hugging Face user name. The repository is public the moment this finishes, so check the card first, or add `--private` and make it public after step 7.

   ```bash
   uv run hf upload YOUR_NAME/qwen3.5-4b-policy-area-lora adapters/policy-area .
   ```

7. Open the page it prints. Read your card as a stranger would. Fix what is unclear and upload again.

8. Tell your tutor the link. `/lab` records it as your shipped artifact.

**Check yourself.** Why does the card list what the model is bad at?

<details><summary>Answer</summary>

Because the reader will find out anyway, and a card that names its limits is one they can trust on the rest. For a hiring manager or a client, the limits section shows you tested the thing instead of only training it.

</details>

**Done when:** the model page is public, its card has no `FILL_IN` left, and the link is logged.

---

## Teach-back

Explain to a buyer who is not technical, in under a minute: you took a free model that scored 57%, spent 13 minutes of laptop time, and got one that scores 74.7% with a prompt a quarter of the size. What did the fine-tune change, what did it not change, and how do they know the number is real?
