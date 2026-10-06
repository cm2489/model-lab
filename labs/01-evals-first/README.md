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

1. Rebuild the data from the public record. The first time, this downloads about 48 MB from GovInfo.

   ```bash
   make data
   ```

   You should see (the first lines, from the kit builder's run):

   ```text
   source: GovInfo BILLSTATUS bulk data, congress 119, types hr,s,hjres,sjres,hconres,sconres
   fetched (ET): 2026-10-06T14:19:40-04:00
   bills parsed: 17007   no policy area (dropped): 396   labelled: 16611
   distinct title keys: 13088   copies folded: 3523   title keys with conflicting labels: 86
   split units (title keys joined by short title): 12411   golden candidates skipped for a near-twin title: 12
   before cleanup: train 11647  valid 1280  golden 150
   cleanup dropped (corrected-key collisions): train 7  valid 33  golden 0
   split sizes: train 11640  valid 1247  golden 150
   shared corrected keys across splits: {'golden&train': 0, 'golden&valid': 0, 'train&valid': 0}
   ```

   Then a table of every label's count in each split, and at the end:

   ```text
   labels: 31

   majority class (train): Health (11.0% of train)
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

   You should see `git status --short data evals/golden.jsonl` print nothing afterwards.

   This is the first lesson: **the test set is frozen in git.** Every score in this project uses the same 150 bills.

3. Look at three test examples:

   ```bash
   head -n 3 evals/golden.jsonl
   ```

   You should see:

   ```text
   {"id": "hconres109-119", "title": "Allowing Emancipation Hall to be used for a ceremony to dedicate the Semiquincentennial Congressional Time Capsule on Wednesday, June 24, 2026.", "label": "Congress", ...}
   {"id": "hconres121-119", "title": "Expressing the sense of the Congress that assisted suicide (sometimes referred to using other terms) puts everyone, including those most vulnerable, at risk of deadly harm.", "label": "Health", ...}
   {"id": "hr1028-119", "title": "To modify eligibility requirements for amateur sports governing organizations.", "label": "Sports and Recreation", ...}
   ```

4. Read `data/README.md`, sections "What was folded" and "The honest floor". 10 minutes.

**Check:** a Senate bill says "A bill to amend X." Its House companion says "To amend X, and for other purposes."
What happens if one lands in training and the other in the test set?

<details><summary>Answer</summary>

The test leaks: the model can memorize the answer in training and "pass" the test without learning anything. That is why the build folds the two into one title key and keeps them in one split. The first version of this kit missed it: 61 of 150 test titles had a companion in train or valid, 60 of them with the same label.

</details>

**Done when:** you can say the floor (8.0%), and why companions must share a split.

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
   hr4763-119 | Labor and Employment | https://www.congress.gov/bill/119th-congress/house-bill/4763 | To require employers to provide paid annual leave to employees, and for other purposes.
   hr3996-119 | Health | https://www.congress.gov/bill/119th-congress/house-bill/3996 | To amend title XI of the Social Security Act to establish a pilot program for testing the
   ```

2. Open each link. The URL pattern is `https://www.congress.gov/bill/119th-congress/<kind>/<number>`,
   where `<kind>` is `house-bill`, `senate-bill`, `house-joint-resolution`, `senate-joint-resolution`,
   `house-concurrent-resolution` or `senate-concurrent-resolution`.
3. On each bill page, find "Policy Area". Mark one of three:
   - **match:** Congress.gov shows the same label.
   - **differs:** it shows another label. Write both down.
   - **fair?:** it matches, but you would not have guessed it from the title. Write one word why.

   > **Not verified by the kit builder:** where "Policy Area" sits on a Congress.gov bill page.
   > Congress.gov blocked the kit builder's automated requests. The labels themselves were
   > cross-checked another way: 3,236 of 3,236 bills in a separate copy of the same public record agreed.

4. Count your marks. Write them in a note: `match __ / differs __ / fair? __`.

**Check:** you find a label you think is wrong. Do you change it in `golden.jsonl`?

<details><summary>Answer</summary>

No. The label is the official record, and the task is to predict the official record. Write the case down instead. If many labels look wrong, the task needs a new definition, and every score so far is void. One odd label is normal noise. (Changing the file would also fail the gate's checksum; see step 6.)

</details>

**Done when:** 30 bills are marked and you have your three counts.

---

<a id="step-3"></a>

## Step 3 · Score the base model, prompt only

**Do this:** run the local 4B model on all 150 golden bills. **About 45 minutes.**

1. Read the prompt the model gets: `evals/prompt.py`, the `INSTRUCTIONS` text. Then read `parse_label`
   in the same file: a reply counts only if the whole reply is one label. 5 minutes.
2. Run the eval:

   ```bash
   make eval
   ```

   It prints one line per bill (`ok`, `x` for wrong, `INV` for an unreadable reply). It takes about 70 seconds on an M1 Max.

   You should see, at the end (kit builder's run, same command with a fixed run name):

   ```text
   run: results/qwen3.5-4b-4bit-golden-baseline
   accuracy 56.7% (85/150)   macro-F1 0.541   invalid 1.3% (2)
   latency p50 0.437s  p90 0.481s   tokens/s 116.2   wall 69s
   cost per 1,000 bills: 0.0  (local run: $0 marginal cost (hardware and electricity not counted))
   ```

   Greedy decoding is deterministic. A second run gave the same 150 replies, word for word.
3. Open the score card the run wrote: `results/<your-run>/score.md`. Read "Top confusions".
4. Open `results/README.md`. Your run is a new row, under the committed baseline row.

**Why thinking is off:** Qwen3.5 thinks before it answers by default. The harness turns that off
(`enable_thinking=False` in `evals/backends.py`). With thinking on, the kit builder saw 1,500 to
2,000+ reasoning tokens and about 20 seconds per bill, and one bill ran out of room before it
answered. To try it on two bills without adding a row to your table:

```bash
uv run python -m evals.run --backend mlx --model mlx-community/Qwen3.5-4B-4bit --limit 2 --thinking --max-tokens 2048 --results-dir /tmp/think-test
```

**Check:** the 2 invalid replies were "Food and Agriculture" and "Elections and Voting". The first is
nearly a real label ("Agriculture and Food"). Why does the harness count both as wrong instead of fixing them up?

<details><summary>Answer</summary>

Fixing up means guessing what the model meant, and the guess becomes part of the score. A strict parser measures what the model actually said. Dropping invalid replies would be worse: a model that dodges hard bills would look better than one that tries.

</details>

**Done when:** you have your accuracy, invalid rate, p50 latency and tokens per second written down.

---

<a id="step-4"></a>

## Step 4 · Score a frontier model on the same set

> **Not verified by the kit builder.** This step calls a paid API with your own key. The kit
> builder had no key and spent no money. The code path is unit-tested with a fake client
> (`evals/tests/test_anthropic_backend.py`), and the spend guard below was run for real, but no request has been sent.

**Do this:** run Claude on the same 150 bills and add a priced row to the table. **About 30 minutes.**

**The cap for this step is $2.** The harness will not start a run that could cost more than you allow.
The guard protects you when you pass the real prices: it trusts the numbers you give it, and refuses zero or negative ones.

**The worst case, worked out.** At $4 per million input tokens and $20 per million output tokens:
- Each reply is capped at 512 tokens (thinking included): 512 × $20 / 1,000,000 = $0.0102 a bill.
- Input is about 250 to 440 tokens a bill (the guard assumes the high end): at most $0.0018 a bill.
- 150 bills × $0.0120 = **$1.80 at most**. Real runs should cost far less, because most replies are short.
- With the old cap of 2,048 tokens it would have been up to about $6.40. That is why the cap is 512.
- Retries are off (`max_retries=0` in `evals/backends.py`). The SDK would otherwise resend a failed
  request up to twice, which the worst case does not count. A failed request is recorded as an invalid reply instead.

1. Check today's prices at `https://www.anthropic.com/pricing`. The kit was built with Claude Opus 5.5
   at $4 per million input tokens and $20 per million output tokens (Anthropic's model table, September 25, 2026).
   If they changed, use today's numbers in every command below.

   You should see: a price for Claude Opus 5.5, input and output, per million tokens.

2. See the guard refuse a run over its cap. This sends nothing and needs no key:

   ```bash
   uv run python -m evals.run --backend anthropic --model claude-opus-5-5 --split golden --price-in 4 --price-out 20 --max-usd 1
   ```

   You should see (kit builder's run):

   ```text
   spend guard: 150 bills, max_tokens 512, no retries, worst case $1.80, cap $1.00
   error: worst case $1.80 is over --max-usd $1.00. Lower --limit or --max-tokens, or raise --max-usd.
   ```

3. Put your key in the environment for this terminal only:

   ```bash
   export ANTHROPIC_API_KEY="paste-your-key-here"   # never commit it
   ```

   You should see: nothing. `echo ${#ANTHROPIC_API_KEY}` prints a number above 0.

4. Run 5 bills first, into a scratch folder so it stays out of the table (worst case $0.06):

   ```bash
   uv run python -m evals.run --backend anthropic --model claude-opus-5-5 --limit 5 --price-in 4 --price-out 20 --max-usd 0.10 --results-dir /tmp/opus-smoke
   ```

   Expect: 5 lines, then an accuracy line. Open `/tmp/opus-smoke/*/score.md` and check "How replies ended".
   If any say `max_tokens`, replies are being cut off; stop and read the note below.

5. Run all 150 (worst case $1.80):

   ```bash
   uv run python -m evals.run --backend anthropic --model claude-opus-5-5 --split golden --price-in 4 --price-out 20 --max-usd 2
   ```

6. Open `results/README.md`. The new row shows accuracy, speed and cost next to the local rows.

**What to expect (estimates, not measured):**
- Accuracy well above 57%, but not 100%. Step 5's thin-title bills defeat any model.
- A real cost well under the $1.80 ceiling.
- A few seconds per bill, and a blank tok/s column (the API does not report it).
- If a request is refused, it counts as invalid. That is deliberate: a fallback model would score a different model under Opus's name.
- **Unverified:** whether 512 tokens is always enough. Opus 5.5 always thinks a little, and thinking counts
  against the cap. A reply cut off before its answer scores invalid and shows as `max_tokens` in "How replies ended".
  If that happens often, raising `--max-tokens` raises the worst case too, and the run will need more than $2.

The harness also refuses to send the `train` or `valid` split, or any file over 500 bills, to a paid API unless you add `--allow-large`.
If you run a model or prices the page did not document, it prints a one-line warning first.

**Check:** the frontier row shows a cost per 1,000 bills. Where does that number come from?

<details><summary>Answer</summary>

The measured input and output tokens for these 150 bills, times the prices you passed on the command line, scaled to 1,000 bills. No price is hard-coded, because prices change.

</details>

**Done when:** `results/README.md` has a frontier row beside the local rows (the committed baseline, plus your own step 3 run).

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
   65 misses out of 150. Showing 30.

    1. s181-119
       gold:  Economics and Public Finance
       model: Government Operations and Politics
       title: A bill to require agencies submit zero-based budgets.
       https://www.congress.gov/bill/119th-congress/senate-bill/181

    2. hr8633-119
       gold:  Commerce
       model: Economics and Public Finance
       title: To specify the standards governing claims of consciously parallel pricing coordination in civil actions under the Sherman Act, and to clarify the meaning of contract, combination in the form of trust or otherwise, or conspiracy under the Sherman Act.
       https://www.congress.gov/bill/119th-congress/house-bill/8633
   ```

2. Read all 30. For each one, write a short cause in your own words. One line each. Do not group yet.
3. Now group the lines. Aim for three to five groups.
4. Count each group. Name the top three.
5. For each of the top three, write one line: could a fine-tune fix this, yes or no?

**Check:** what are the top three causes?

<details><summary>Answer (the kit builder's grouping; yours may differ)</summary>

1. **The law or program in the title decides the label (14 of 30).** "Amend the Internal Revenue Code" is
   Taxation, even when the topic is housing. A Water Resources Development Act project is Water Resources
   Development. Amending the Help America Vote Act is Government Operations. **A fine-tune can learn these.**
2. **Neighbouring labels overlap (13 of 30).** Economics and Public Finance or Government Operations?
   Commerce or Economics? Both are defensible; the record picked one. **Partly fixable:** training shows which side the record usually picks.
3. **The title is too thin (3 of 30).** "Allowing Emancipation Hall to be used for a ceremony…" is Congress
   (it is about the Capitol), not Arts. Grants for after-school programs are Crime and Law Enforcement. **Mostly not fixable from the title alone.**

The 2 invalid replies sit in group 1. Both named a label that does not exist.

</details>

**Done when:** you have three named causes, each with a count and a yes-or-no on fixability.

---

<a id="step-6"></a>

## Step 6 · Add the pass/fail gate and watch it go red

**Do this:** run the gate, break it on purpose, and watch CI catch it. **About 45 minutes.**

**Start this step on the `main` branch** (`git switch main`). Sub-step 9 brings you back there.

> Sub-steps 1 to 4 were run by the kit builder. Sub-steps 5 to 10 (the GitHub part) were
> **not verified by the kit builder**: no deliberately broken pull request was opened. The same
> workflow ran green on the kit's own pull request.

1. Run the unit tests:

   ```bash
   make test
   ```

   You should see, at the end:

   ```text
   Ran 82 tests in 0.777s

   OK
   ```

2. Run the gate on the committed baseline:

   ```bash
   make gate
   ```

   You should see:

   ```text
   golden file  evals/golden.jsonl  sha256 a717155c2c2b268b...
   accuracy     0.5667  need >= 0.5660  PASS
   invalid rate 0.0133  need <= 0.0140  PASS
   gate: PASS (85/150 correct, 2 invalid)
   ```

   The bar sits just under the baseline (`Makefile`, `MIN_ACCURACY` and `MAX_INVALID`). One more miss fails it.
   The gate also checks the golden file's SHA-256 against `GOLDEN_SHA256` in the `Makefile`, so nobody can
   quietly edit the test set to match the predictions.

3. Make a branch and plant one bad prediction. This changes the second bill's answer from Health (right) to Taxation (wrong):

   ```bash
   git switch -c test/plant-bad-prediction
   sed -i '' '2s/"pred": "Health"/"pred": "Taxation"/' results/qwen3.5-4b-4bit-golden-baseline/predictions.jsonl
   ```

   You should see: no output. Then `git diff --stat results/qwen3.5-4b-4bit-golden-baseline/predictions.jsonl`
   shows `1 file changed, 1 insertion(+), 1 deletion(-)`.

4. Run the gate again:

   ```bash
   make gate
   ```

   You should see:

   ```text
   golden file  evals/golden.jsonl  sha256 a717155c2c2b268b...
   accuracy     0.5600  need >= 0.5660  FAIL
   invalid rate 0.0133  need <= 0.0140  PASS
   gate: FAIL (84/150 correct, 2 invalid)
   make: *** [gate] Error 1
   ```

5. Commit only the planted file. Your step 3 run also changed `results/README.md`; leave that out:

   ```bash
   git commit -m "Test: plant one bad prediction" results/qwen3.5-4b-4bit-golden-baseline/predictions.jsonl
   ```

   Expect: `1 file changed, 1 insertion(+), 1 deletion(-)`.

6. Push the branch:

   ```bash
   git push -u origin test/plant-bad-prediction
   ```

   Expect: a line saying the new branch was created on `origin`.

7. Open a draft pull request:

   ```bash
   gh pr create --fill --draft
   ```

   Expect: a pull request URL. If the repository is still private, the draft option may be refused
   (**unverified**: it depends on your GitHub plan). If it is, run `gh pr create --fill` instead.

8. Watch the checks:

   ```bash
   gh pr checks --watch
   ```

   Expect: the `test-and-gate` check fails, at the step "Gate on the committed baseline predictions",
   with the same FAIL lines as sub-step 4.

9. Go back to `main`, by name, whatever branch you are on now:

   ```bash
   git switch main
   ```

   Expect: `Switched to branch 'main'`, or `Already on 'main'`. The planted change stays on the test branch only.
   If git refuses because of uncommitted changes, run `git restore results/` first, then switch again.

10. Close the pull request and delete its branch:

    ```bash
    gh pr close test/plant-bad-prediction --delete-branch
    ```

    Expect: a line saying the pull request was closed, and one saying the branch was deleted.

**Check:** CI never runs a model. Then what does the gate protect?

<details><summary>Answer</summary>

The committed predictions. When you change the model or the prompt, you commit its new predictions with the change. CI re-scores them against the frozen golden set, with gold labels from the golden file, and blocks the merge if they fall below the bar. The checksum makes sure the golden file itself did not move.

</details>

**Done when:** you have seen the gate fail locally and on GitHub, and the test branch is gone.

---

<a id="step-7"></a>

## Step 7 · Publish the score table

> **Not verified by the kit builder.** Publishing reaches other people, so the kit builder did not do it.

**Do this:** make the score table public and readable in one minute. **About 40 minutes.**

1. Open `results/README.md`. Check that every row has a model, a date and a commit.

   Expect: the committed baseline, your step 3 run (same model, same score) and the frontier run.
   A commit ending in `-dirty` means code, prompt or data differed from that commit when the run happened;
   re-run that row from a clean checkout before you publish it.

2. Scan the whole working tree for API keys, tracked and untracked files alike:

   ```bash
   grep -rn -I -E "sk-ant-[A-Za-z0-9_-]{10,}" --exclude-dir=.git --exclude-dir=.venv --exclude-dir=cache --exclude='.env*' .
   ```

   Expect: no output. (`.env` files are skipped because they are gitignored and never committed.)

3. Merge your frontier-run results through a pull request, with `make test` and `make gate` green first.

   Expect: the `evals` check passes on the pull request, and `results/README.md` on `main` shows the frontier row.

4. Write three sentences in the repo's top `README.md`: the task, the two scores, the floor.
   Not in `results/README.md`: the harness rewrites that file on every run.

   Expect: someone who reads only those three sentences can say what was measured and how it compares to 8%.

5. If the repository is not public yet, make it public (GitHub, Settings, General, Danger Zone, Change visibility).
   That cannot be undone for anyone who has already cloned it.

   Expect: the repository page shows a "Public" badge. **Unverified:** the exact menu path; GitHub moves settings.

6. Share the link to `results/README.md` where you want it seen.

   Expect: the link opens without signing in.

**Check:** a reader sees "56.7%". What else must the page tell them so the number means something?

<details><summary>Answer</summary>

The test set (150 frozen bills, from where, how companions were kept out of training), the floor (8.0%), the model and its settings, the date, and the commit. Without those, a number is a rumour.

</details>

**Done when:** the table is public, and your top README says what it shows in three sentences.

---

## Teach-back

Explain to a non-technical buyer, out loud, in under two minutes:

> **Why does the test set come before the fine-tune?**

Hit these points in your own words:

- A fine-tune costs time and money. Without a test, "it feels better" is the only result.
- The test set is fixed first, so nobody can pick the questions after seeing the answers.
- The test must not overlap the training data. Near-copies (like House and Senate versions of one bill) count as overlap.
- The base model's score is the "before" picture: 57% here, against a floor of 8%.
- The failures show what to fix, and which failures no fine-tune can fix.
- The gate keeps the gain: any later change that scores worse cannot merge.
