# Lab 2 · First fine-tune

**Aim:** fine-tune a 4B model with LoRA and show, on your test set, what changed.

**You ship:** a fine-tuned model and its model card on Hugging Face.

**Time:** about 4 hours 45 minutes, in seven steps. Stop after any step.

**Before you start:** Lab 1 is done. You have the test set, the harness and a baseline score. Free disk is 5 GB or more.

**The one rule of this lab:** training uses batch size 1. On a 32 GB Mac, a batch of 4 pushed the machine into swap and nearly filled the disk. The reason is in step 3.

Every "You should see" block is real output from a 2021 MacBook Pro (M1 Max, 32 GB), run on October 6, 2026. Blocks show the last lines of the output.

---

<a id="step-1"></a>

## Step 1 · What LoRA changes in a model

**Do this:** work out, with numbers from your own Lab 0 run, what a fine-tune touches. **About 30 minutes.**

1. Open `labs/00-setup/MY-NUMBERS.md`. Find three things you measured: the adapter file size, the trainable percentage in the training output (0.096%), and peak memory while training.

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
   {"messages": [{"role": "user", "content": "Which Congress.gov policy area does this bill belong to? Reply with the policy area only.\n\nBill title:\nTo amend title 49, United States Code, with respect to the requirement to test drivers of commercial motor vehicles for English proficiency, and for other purposes."}, {"role": "assistant", "content": "Transportation and Public Works"}]}
   ```

3. Open `tune/prepare.py` and find the answers to these three questions. Each is a design choice you may be asked to defend.

   - Why does the training prompt leave out the list of 32 labels?
   - Why are there at most 80 examples per label, when "Health" has 1,286 available?
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

**Check yourself.** The cap gives every label at most 80 examples. What would the model learn if you trained on all 11,647 rows as they are?

<details><summary>Answer</summary>

It would see "Health" about 50 times as often as the rarest label, and it would learn to guess the common labels when unsure. Accuracy on rare labels would fall. Capping trades some total data for balance.

</details>

**Done when:** `data/lora/train.jsonl` exists and you can answer the three questions in sub-step 3 in one sentence each.

---

<a id="step-3"></a>

## Step 3 · Train: your first LoRA run

**Do this:** fine-tune the model on 1,200 examples. **About 45 minutes, of which the run is about @@TRAIN_MIN@@.**

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
@@TRAIN_OUTPUT@@
   ```

4. While it runs, open Activity Monitor and watch the Memory tab. The "Memory Pressure" graph should stay green.

5. When it ends, write down four numbers: the first and last `val` loss, the wall time and the peak memory.

**Why batch size 1.** `make tune` runs the command printed at the top of `tune/train.py`. Read it. Two settings keep this run inside a 32 GB Mac.

- `--batch-size 1 --grad-accumulation-steps 4`: the model sees one example at a time and updates its weights every four. That acts like a batch of 4 at the memory cost of 1.
- The short prompt: each example is about @@SHORT_TOKENS@@ tokens. With the label list in every example it is about 250.

These were measured on this Mac on October 6, 2026.

| Run | Peak memory | What happened |
|---|---|---|
| Batch 1, short prompt (this lab) | @@TRAIN_PEAK@@ GB | Fine |
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
@@EVAL_TUNED@@
   ```

2. Score the untuned model with the same short prompt. This shows what the fine-tune taught.

   ```bash
   uv run python -m evals.run --backend mlx --model mlx-community/Qwen3.5-4B-4bit --prompt short --split golden
   ```

   **You should see**

   ```text
@@EVAL_BASE_SHORT@@
   ```

3. Open the score table and read the three rows side by side.

   ```bash
   cat results/README.md
   ```

   | Model | Prompt | Accuracy | Invalid replies | Prompt tokens per bill |
   |---|---|---|---|---|
   | Untuned | lists all 32 labels | 56.7% | 2 | 250 |
   | Untuned | short | @@BASE_SHORT_ACC@@ | @@BASE_SHORT_INV@@ | @@SHORT_TOKENS@@ |
   | Tuned | short | @@TUNED_ACC@@ | @@TUNED_INV@@ | @@SHORT_TOKENS@@ |

4. Check your two predictions from step 1.

5. Read the tuned model's misses, the same way you read the baseline's in Lab 1.

   ```bash
   uv run python -m evals.misses results/<your tuned run folder>/predictions.jsonl
   ```

   Compare with your Lab 1 notes. Which of your three failure causes did the fine-tune fix? Which are still there?

**What the three rows say**

- Without the label list, the untuned model makes up label names. Most of its replies are invalid.
- The tuned model learned the label names. It needs no list.
- A prompt about a sixth of the length means each bill costs about a sixth as much to read. On a hosted model you pay for that difference on every request.

**Check yourself.** The tuned model was scored with a different prompt from the baseline. Is the comparison fair?

<details><summary>Answer</summary>

Yes, if you say so plainly. Each model gets the prompt it works best with, and both are scored on the same 150 bills by the same parser. The table names the prompt for every row. What would be unfair is hiding the difference, or scoring on bills the tuned model trained on.

</details>

**Done when:** `results/README.md` has the three rows and you have named which Lab 1 failure causes the fine-tune fixed.

---

<a id="step-5"></a>

## Step 5 · Change one thing and run again

**Do this:** run one experiment that changes exactly one setting. **About 45 minutes.**

1. Pick one. Change only that.

   | Experiment | Command |
   |---|---|
   | A quarter of the training | `uv run python -m tune.train --iters 300 --name quick` |
   | Twice the layers | `uv run python -m tune.train --num-layers 16 --name deep` |
   | Half the learning rate | `uv run python -m tune.train --learning-rate 5e-5 --name slow` |

2. Predict the result before you run it: better, worse or the same, and by about how much.

3. Run it. Check free disk first, as in step 3.

4. Score it. Use the name you gave it.

   ```bash
   uv run python -m evals.run --backend mlx --model mlx-community/Qwen3.5-4B-4bit --adapter-path adapters/quick --prompt short --split golden
   ```

   **You should see**, for the "quarter of the training" experiment:

   ```text
@@EVAL_QUICK@@
   ```

5. Write one sentence: what did this one change do, and would you keep it?

**Check yourself.** Your experiment scored 2 bills better out of 150. Is it better?

<details><summary>Answer</summary>

You cannot say. With 150 bills, one bill is 0.7 points, and a difference of two or three bills is inside the noise. To trust a small gain you need a bigger test set or several runs. A large gap, like untuned to tuned, is real.

</details>

**Done when:** `results/README.md` has a fourth row and you wrote your one sentence.

---

<a id="step-6"></a>

## Step 6 · Swap the base model

**Not verified by the kit builder.** The second model is a 5.2 GB download and the Mac this kit was built on had about 7 GB free that day. The commands below follow the same pattern as steps 3 and 4, but nobody has run them yet. If one fails, note what happened in `labs/02-first-fine-tune/NOTES.md`.

**Do this:** run the same fine-tune on a model from a different lab and compare. **About 45 minutes.**

1. Check free disk. You need 12 GB or more to hold both models and train.

   ```bash
   df -h /System/Volumes/Data
   ```

2. Read the license on the original, `google/gemma-4-E4B-it`, on Hugging Face. It is tagged Apache-2.0. The converted copy you are about to download is tagged "gemma". When the two disagree, the original is the one that counts. Write down what you found.

3. Download the second model.

   ```bash
   uv run hf download mlx-community/gemma-4-e4b-it-4bit
   ```

4. Score it untuned, with the label-list prompt.

   ```bash
   uv run python -m evals.run --backend mlx --model mlx-community/gemma-4-e4b-it-4bit --split golden
   ```

5. Fine-tune it with the same data and settings.

   ```bash
   uv run python -m tune.train --model mlx-community/gemma-4-e4b-it-4bit --name policy-area-gemma
   ```

6. Score the tuned version.

   ```bash
   uv run python -m evals.run --backend mlx --model mlx-community/gemma-4-e4b-it-4bit --adapter-path adapters/policy-area-gemma --prompt short --split golden
   ```

7. Put the two models side by side: untuned score, tuned score, speed, peak memory, download size, license, and who made it.

**Check yourself.** A client will not accept a model made in China. How long does it take you to switch, and what do you need to re-run?

<details><summary>Answer</summary>

About as long as this step: download, train, score. The data, the harness, the test set and the settings do not change. That is what the harness buys you. You re-run training and scoring, then compare the rows.

</details>

**Done when:** `results/README.md` has rows for both model families and you have a side-by-side table.

---

<a id="step-7"></a>

## Step 7 · Write the model card and publish

**Not verified by the kit builder.** Publishing needs your Hugging Face account and token. The command options were checked against `hf --help`. The upload itself has not been run.

**Do this:** publish the adapter with a card that states its numbers and its limits. **About 45 minutes.**

1. Copy the card template into the adapter folder. Hugging Face shows `README.md` as the model card.

   ```bash
   cp labs/02-first-fine-tune/MODEL_CARD.template.md adapters/policy-area/README.md
   ```

2. Fill in every `FILL_IN` from your own runs. The "Limits" section matters most. Use what you saw in step 4.

3. Check nothing private is in the folder. It should hold the card, `adapter_config.json`, `adapters.safetensors` and numbered checkpoint files.

   ```bash
   ls -l adapters/policy-area
   ```

4. Delete the numbered checkpoints. Only the final weights are needed.

   ```bash
   rm adapters/policy-area/0*_adapters.safetensors
   ```

5. Log in to Hugging Face. This opens a page where you create a token with write access.

   ```bash
   uv run hf auth login
   ```

6. Upload. Replace `YOUR_NAME` with your Hugging Face user name.

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

Explain to a buyer who is not technical, in under a minute: you took a free model that scored 57%, spent @@TRAIN_MIN@@ of laptop time, and got one that scores @@TUNED_ACC@@ with a prompt a sixth of the size. What did the fine-tune change, what did it not change, and how do they know the number is real?
