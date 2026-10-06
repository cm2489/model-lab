# Lab 1 · Evals first

**Aim:** build a test set and prove, with numbers, how good a model is at one task.

**You ship:** a public eval harness with a pass/fail gate.

**Time:** about 4 hours 40 minutes, in seven steps. Each step stands alone. Stop after any of them.

**The task:** read a US bill's official title and name its policy area: one of 32 fixed labels
from Congress.gov, such as "Health" or "Taxation".

**Why first:** you cannot know a fine-tune helped unless a test set says so. Lab 2 fine-tunes a
model. This lab builds the ruler you will measure it with.

**Before you start:** `uv sync` has run in the repo, and the model
`mlx-community/Qwen3.5-4B-4bit` (3 GB) is downloaded. If it is not, step 3 downloads it the first time.

---

<a id="step-1"></a>

## Step 1 · Meet the task and the data

**Do this:** rebuild the dataset and read what it says. **About 30 minutes.**

1. Rebuild the data from the public record:

   ```bash
   make data
   ```

   You should see (the first lines, from the kit builder's run):

   ```text
   source: GovInfo BILLSTATUS bulk data, congress 119, types hr,s,hjres,sjres,hconres,sconres
   fetched (ET): 2026-10-06T14:19:40-04:00
   bills parsed: 17007   no policy area (dropped): 396   labelled: 16611
   distinct normalized titles: 16261   duplicate-title bills folded: 350   title groups with conflicting labels: 19
   split sizes: train 14498  valid 1613  golden 150
   shared normalized titles across splits: {'train&valid': 0, 'train&golden': 0, 'valid&golden': 0}
   ```

   Then a table of every label's count in each split, and at the end:

   ```text
   labels: 31
   majority class (train): Health (11.4% of train)
   majority-class baseline on golden: 12/150 = 8.0%
   ```

   Your numbers will be a little different. The record changes every day.

2. See whether your rebuild changed the committed files:

   ```bash
   git status --short data evals/golden.jsonl
   ```

   If it lists files, the public record moved since the kit was built. Put the committed files back:

   ```bash
   git restore data/train.jsonl data/valid.jsonl evals/golden.jsonl
   ```

   This is the first lesson: **the test set is frozen in git.** Every score in this project uses the same 150 bills.

3. Look at three test examples:

   ```bash
   head -n 3 evals/golden.jsonl
   ```

   You should see:

   ```text
   {"id": "hconres54-119", "title": "Expressing support for designation of the first Friday of October as \"Manufacturing Day\".", "label": "Commerce", ...}
   {"id": "hjres143-119", "title": "Enabling Congress to advance important policies.", "label": "Congress", ...}
   {"id": "hr10042-119", "title": "To direct the Director of the National Science Foundation to complete workshops related to the integration of artificial intelligence into classrooms, and for other purposes.", "label": "Science, Technology, Communications", ...}
   ```

4. Read `data/README.md`, sections "The honest floor" and "Is title-only too easy or too hard?". 5 minutes.

**Check:** a model scores 8% on the golden set. Is that good?

<details><summary>Answer</summary>

No. Answering "Health" for every bill scores 8.0%. A model has to beat that floor before it has learned anything.

</details>

**Done when:** you can say the floor (8.0%) and why the test set lives in git.

---

<a id="step-2"></a>

## Step 2 · Build the golden test set

**Do this:** check 30 golden labels by hand against Congress.gov. **About 45 minutes.**

The script already picked the 150 golden bills. Your job is to trust them, or find out why not.

1. Print 30 golden bills (the same 30 for everyone):

   ```bash
   uv run python -c "import json,random; rows=[json.loads(l) for l in open('evals/golden.jsonl')]; random.Random(1).shuffle(rows); [print(r['id'], '|', r['label'], '|', r['url'], '|', r['title'][:90]) for r in rows[:30]]"
   ```

   You should see 30 lines. The first two:

   ```text
   hr5024-119 | Transportation and Public Works | https://www.congress.gov/bill/119th-congress/house-bill/5024 | ...
   hr4299-119 | Health | https://www.congress.gov/bill/119th-congress/house-bill/4299 | ...
   ```

   > **Not verified by the kit builder:** where "Policy Area" sits on a Congress.gov bill page.
   > Congress.gov blocked the kit builder's automated requests. The labels themselves were
   > cross-checked another way: 3,236 of 3,236 bills in a separate copy of the same public record agreed.

2. Open each link. The URL pattern is `https://www.congress.gov/bill/119th-congress/<kind>/<number>`,
   where `<kind>` is `house-bill`, `senate-bill`, `house-joint-resolution`, `senate-joint-resolution`,
   `house-concurrent-resolution` or `senate-concurrent-resolution`.
3. On each bill page, find "Policy Area". Mark one of three:
   - **match:** Congress.gov shows the same label.
   - **differs:** it shows another label. Write both down.
   - **fair?:** it matches, but you would not have guessed it from the title. Write one word why.
4. Count your marks. Write them in a note: `match __ / differs __ / fair? __`.

**Check:** you find a label you think is wrong. Do you change it in `golden.jsonl`?

<details><summary>Answer</summary>

No. The label is the official record, and the task is to predict the official record. Write the case down instead. If many labels look wrong, the task needs a new definition, and every score so far is void. One odd label is normal noise.

</details>

**Done when:** 30 bills are marked and you have your three counts.

---

<a id="step-3"></a>

## Step 3 · Score the base model, prompt only

**Do this:** run the local 4B model on all 150 golden bills. **About 45 minutes.**

1. Read the prompt the model gets: `evals/prompt.py`, the `INSTRUCTIONS` text. 3 minutes.
2. Run the eval:

   ```bash
   make eval
   ```

   It prints one line per bill (`ok`, `x` for wrong, `INV` for an unreadable reply). It takes about 70 seconds on an M1 Max.

   You should see, at the end (kit builder's run, same command with a fixed run name):

   ```text
   run: results/qwen3.5-4b-4bit-golden-baseline
   accuracy 59.3% (89/150)   macro-F1 0.600   invalid 0.0% (0)
   latency p50 0.447s  p90 0.489s   tokens/s 116.2   wall 70s
   cost per 1,000 bills: 0.0  (local run: $0 marginal cost (hardware and electricity not counted))
   ```

   Greedy decoding is deterministic. A second run gave the same 150 answers.
3. Open the score card the run wrote: `results/<your-run>/score.md`. Read "Top confusions".
4. Open `results/README.md`. Your run is a new row in the table.

**Why thinking is off:** Qwen3.5 thinks before it answers by default. The harness turns that off
(`enable_thinking=False` in `evals/backends.py`). With thinking on, the kit builder saw 1,500 to
2,000+ reasoning tokens and about 20 seconds per bill, and one bill ran out of room before it
answered. Try it on two bills if you are curious:
`uv run python -m evals.run --backend mlx --model mlx-community/Qwen3.5-4B-4bit --limit 2 --thinking --max-tokens 2048`.

**Check:** the model never gave an invalid reply. Why does the harness still count invalid replies, and as wrong?

<details><summary>Answer</summary>

Because dropping them would inflate accuracy. A model that dodges hard bills would look better than one that tries. Every bill in the test set must count.

</details>

**Done when:** you have your accuracy, invalid rate, p50 latency and tokens per second written down.

---

<a id="step-4"></a>

## Step 4 · Score a frontier model on the same set

> **Not verified by the kit builder.** This step calls a paid API with your own key. The kit
> builder had no key and spent no money. The code path is unit-tested with a fake client
> (`evals/tests/test_anthropic_backend.py`), but no real request has been sent.

**Do this:** run Claude on the same 150 bills and add a priced row to the table. **About 30 minutes.**

1. Check today's prices at `https://www.anthropic.com/pricing`. The kit was built with Claude Opus 5.5
   at $4 per million input tokens and $20 per million output tokens (Anthropic's model table, September 25, 2026).
   Use what the page says today.
2. Put your key in the environment for this terminal only:

   ```bash
   export ANTHROPIC_API_KEY=...   # paste your key; never commit it
   ```

3. Run 5 bills first, to see it work. This writes to a scratch folder, so it stays out of the table:

   ```bash
   uv run python -m evals.run --backend anthropic --model claude-opus-5-5 --limit 5 --price-in 4 --price-out 20 --results-dir /tmp/opus-smoke
   ```

4. Run all 150:

   ```bash
   uv run python -m evals.run --backend anthropic --model claude-opus-5-5 --split golden --price-in 4 --price-out 20
   ```

5. Open `results/README.md`. The new row shows accuracy, speed and cost side by side with the local model.

**What to expect (estimates, not measured):**
- Accuracy well above 59%, but not 100%. Step 5's thin-title bills defeat any model.
- Cost under about $2 for 150 bills. Opus 5.5 always thinks a little; those thinking tokens bill as output and are counted.
- A few seconds per bill, and a blank tok/s column (the API does not report it).
- If a request is refused, it counts as invalid. That is deliberate: a fallback model would score a different model under Opus's name.

**Check:** the frontier row shows a cost per 1,000 bills. Where does that number come from?

<details><summary>Answer</summary>

The measured input and output tokens for these 150 bills, times the prices you passed on the command line, scaled to 1,000 bills. No price is hard-coded, because prices change.

</details>

**Done when:** `results/README.md` has two rows: the local model and the frontier model.

---

<a id="step-5"></a>

## Step 5 · Read 30 failures

**Do this:** read 30 misses, sort them into groups, name the top three causes. **About 45 minutes.**

1. Print 30 misses (shuffled with a fixed seed, so it is the same 30 each time):

   ```bash
   uv run python -m evals.misses results/qwen3.5-4b-4bit-golden-baseline/predictions.jsonl --n 30
   ```

   You should see:

   ```text
   61 misses out of 150. Showing 30.

    1. hr317-119
       gold:  Taxation
       model: Health
       title: To amend the Internal Revenue Code of 1986 to create health freedom accounts available to all individuals.
       https://www.congress.gov/bill/119th-congress/house-bill/317

    2. hr7771-119
       gold:  Government Operations and Politics
       model: Armed Forces and National Security
       title: To amend the Defense Production Act of 1950 to require the Chairperson of the Defense Production Act Committee to maintain a database of actions, and for other purposes.
       https://www.congress.gov/bill/119th-congress/house-bill/7771
   ```

2. Read all 30. For each one, write a short cause in your own words. One line each. Do not group yet.
3. Now group the lines. Aim for three to five groups.
4. Count each group. Name the top three.
5. For each of the top three, write one line: could a fine-tune fix this, yes or no?

**Check:** what are the top three causes?

<details><summary>Answer (the kit builder's grouping; yours may differ)</summary>

1. **Missed a Congress.gov convention (14 of 30).** The title names the law, and the law decides the label.
   "Amend the Internal Revenue Code" is Taxation, even when the topic is health. Title 38 (veterans) is
   Armed Forces. Title 5 (federal staff) is Government Operations. **A fine-tune can learn these.**
2. **Neighbouring labels overlap (12 of 30).** Families or Social Welfare? International Affairs or Armed
   Forces? Both are defensible; the record picked one. **Partly fixable:** training shows which side the record usually picks.
3. **The title is too thin (4 of 30).** "Establish the America's Living Library Project" is Public Lands. Nothing in
   the title says so. **Not fixable from the title alone.**

The first group is why Lab 2 should help: 14 of 30 misses follow rules that the training data shows thousands of times.

</details>

**Done when:** you have three named causes, each with a count and a yes-or-no on fixability.

---

<a id="step-6"></a>

## Step 6 · Add the pass/fail gate and watch it go red

**Do this:** run the gate, break it on purpose, and watch CI catch it. **About 45 minutes.**

> Sub-steps 1 to 4 were run by the kit builder. Sub-steps 5 to 8 (GitHub going red on your
> pull request) were **not verified by the kit builder**: no deliberately broken pull request was opened.
> The same workflow ran green on the kit's own pull request.

1. Run the unit tests:

   ```bash
   make test
   ```

   You should see, at the end:

   ```text
   Ran 41 tests in 0.962s

   OK
   ```

2. Run the gate on the committed baseline:

   ```bash
   make gate
   ```

   You should see:

   ```text
   accuracy     0.5933  need >= 0.5930  PASS
   invalid rate 0.0000  need <= 0.0000  PASS
   gate: PASS (89/150 correct, 0 invalid)
   ```

   The bar sits just under the baseline (`Makefile`, `MIN_ACCURACY`). One more miss fails it.

3. Make a branch and plant one bad prediction. This changes the first bill's answer from Commerce (right) to Health (wrong):

   ```bash
   git switch -c test/plant-bad-prediction
   sed -i '' '1s/"pred": "Commerce"/"pred": "Health"/' results/qwen3.5-4b-4bit-golden-baseline/predictions.jsonl
   ```

4. Run the gate again:

   ```bash
   make gate
   ```

   You should see:

   ```text
   accuracy     0.5867  need >= 0.5930  FAIL
   invalid rate 0.0000  need <= 0.0000  PASS
   gate: FAIL (88/150 correct, 0 invalid)
   make: *** [gate] Error 1
   ```

5. Commit and push the branch:

   ```bash
   git commit -am "Test: plant one bad prediction"
   git push -u origin test/plant-bad-prediction
   ```

6. Open a pull request: `gh pr create --fill --draft`.
7. Watch the "evals" check: `gh pr checks --watch`. Expect it to fail at "Gate on the committed baseline predictions", with the same FAIL lines as sub-step 4.
8. Clean up: `gh pr close --delete-branch`, then `git switch main`.

**Check:** CI never runs a model. Then what does the gate protect?

<details><summary>Answer</summary>

The committed predictions. When you change the model or the prompt, you commit its new predictions with the change. CI re-scores them against the frozen golden set, with gold labels from the golden file, and blocks the merge if they fall below the bar.

</details>

**Done when:** you have seen the gate fail locally and on GitHub, and the branch is gone.

---

<a id="step-7"></a>

## Step 7 · Publish the score table

> **Not verified by the kit builder.** Publishing reaches other people, so the kit builder did not do it.

**Do this:** make the score table public and readable in one minute. **About 40 minutes.**

1. Open `results/README.md` on GitHub. Check that every row has a model, a date and a commit. 5 minutes.
2. Check for secrets before anything goes public:

   ```bash
   git grep -n -I -E "sk-ant|ANTHROPIC_API_KEY=" -- . ':!labs/01-evals-first/README.md'
   ```

   Expect no output.
3. Merge your frontier-run results through a pull request (`make test` and `make gate` green first).
4. Write three sentences in the repo's top `README.md`: the task, the two scores, the floor.
   Not in `results/README.md`: the harness rewrites that file on every run.
5. If the repository is not public yet, make it public (GitHub, Settings, General, Danger Zone, Change visibility).
   That cannot be undone for anyone who has already cloned it.
6. Share the link to `results/README.md` where you want it seen.

**What to expect:** a public page with two rows and a floor of 8%. Anyone can rerun the local row with `make eval`.

**Check:** a reader sees "59.3%". What else must the page tell them so the number means something?

<details><summary>Answer</summary>

The test set (150 frozen bills, from where, stratified how), the floor (8.0%), the model and its settings, the date, and the commit. Without those, a number is a rumour.

</details>

**Done when:** the table is public, and your top README says what it shows in three sentences.

---

## Teach-back

Explain to a non-technical buyer, out loud, in under two minutes:

> **Why does the test set come before the fine-tune?**

Hit these points in your own words:

- A fine-tune costs time and money. Without a test, "it feels better" is the only result.
- The test set is fixed first, so nobody can pick the questions after seeing the answers.
- The base model's score is the "before" picture: 59% here, against a floor of 8%.
- The failures show what to fix, and which failures no fine-tune can fix.
- The gate keeps the gain: any later change that scores worse cannot merge.
