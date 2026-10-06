# Session 5: Tokenization: how text becomes numbers

**Time:** about 150 minutes (the original estimate, not measured here).  
**Core question:** What does an LLM actually see when you type — and why does that explain its weirdest failures?

**Aim:** Predict three specific LLM failure modes from tokenization alone, then verify each prediction against a real tokenizer.

**How to use this page:** read each block, then answer its check question before you open the hint and answer. Everything marked "details" is closed on purpose. Try first.

## Lesson

### 1. Models never see letters

#### The core fact

Here is the fact this whole session unpacks: a language model never sees your words, and never sees letters. Before your text reaches the network, a separate component — the **tokenizer** — chops it into chunks called **tokens** and replaces each chunk with an integer ID from a fixed vocabulary. The model receives only the sequence of IDs (which it then maps to vectors called embeddings — its actual working material). Karpathy opens his tokenizer lecture by calling tokenization his least favorite part of working with LLMs, precisely because so much hidden weirdness lives here — and then spends two hours showing why you can't skip it.

#### What a token looks like

What does a token look like? Not a letter, usually not a whole word — typically a *chunk*: 'tokenization' might split into 'token' + 'ization'; common words like ' the' (note the leading space — spaces belong to tokens!) are single tokens; rare words shatter into several pieces. As a rough English average, a token is on the order of three-quarters of a word.

#### What follows from this

Now the consequence that surprises everyone the first time. Ask a model to count the letters in 'strawberry.' You see ten letters; the model may see something like two or three opaque chunks — and the IDs it receives carry no internal letter structure whatsoever. The spelling of what's inside a token is not directly visible to the model; anything it knows about letters inside chunks, it had to absorb statistically from training data. It's like asking someone to count the Lego studs inside a glued-shut box: they can estimate from experience with similar boxes, but they cannot look.

Rule for the week: whenever an LLM fails at something that seems character-trivial, your FIRST hypothesis is now 'what did the tokenizer do to this input?'

**Check:** A model confidently miscounts the r's in 'strawberry.' Without blaming 'model stupidity,' give the mechanistic explanation.

<details>
<summary>Hint and answer</summary>

**Hint:** What unit does the model receive — and is the letter 'r' visible anywhere in that unit?

**Answer:** The tokenizer hands the model 'strawberry' as one or a few opaque token IDs, not eleven characters (ten letters). The IDs expose no internal letter structure, so the model must infer spelling statistically from training data rather than inspecting the string — and that inference can be wrong.

</details>

### 2. BPE: building a vocabulary by merging

#### Where the vocabulary comes from

Where does the token vocabulary come from? The dominant algorithm — the one Karpathy builds from scratch in the lecture — is **Byte Pair Encoding (BPE)**, and its logic is pleasingly mechanical.

#### How merging works

Start with a base vocabulary that can represent anything: in GPT-style tokenizers, the 256 possible byte values, so no text in any language or symbol system is ever unrepresentable — at worst it's a long sequence of single bytes. Now take a large training corpus of text and iterate: find the **most frequent adjacent pair** of tokens in the corpus, merge that pair into a brand-new token, add it to the vocabulary, replace all occurrences, and repeat. Early merges capture glue like 't'+'h' → 'th'; later merges assemble whole common words and fragments. Each merge is a small act of compression — frequent sequences earn short representations. Stop when you hit your vocabulary budget: GPT-2 stopped at 50,257 tokens; later OpenAI tokenizers run around 100k; modern vocabularies generally sit in the tens-of-thousands to low-hundreds-of-thousands range.

#### Two properties that matter

Two properties matter enormously downstream. First, the tokenizer is trained **separately** from the model, on its own corpus, *before* model training — then frozen. It's a preprocessing artifact with its own biases baked in, and the model is stuck with them forever. Second, frequency in the tokenizer's corpus decides everything: common English words become single crisp tokens; rare words, names, and under-represented languages get fragmented into many small pieces. The vocabulary is a frozen mirror of what was common in one particular pile of text at one particular time.

Keep that 'frozen mirror' image — the next two blocks are entirely about what happens when reality and the mirror disagree.

**Check:** In a BPE training run, the pair ('in', 'g') is currently the most frequent adjacent pair in the corpus. What exactly happens next, and what's the corpus-wide effect?

<details>
<summary>Hint and answer</summary>

**Hint:** BPE's loop is three verbs: find, merge, replace. Apply them to this pair.

**Answer:** A new token 'ing' is created and added to the vocabulary, and every adjacent occurrence of 'in'+'g' in the corpus is replaced by it. Corpus-wide, every word ending in -ing now ends in one token instead of two — compression — and future merge counts are computed on this updated corpus.

</details>

### 3. Failure catalog I: spelling and arithmetic

Now cash in the mechanism for predictions. Karpathy's lecture includes a running list of LLM oddities that all trace back to tokenization; here are the two most famous families.

#### Spelling and counting

**Character-level tasks.** Spelling words backward, counting letters, finding the third character, acrostics — all require seeing characters, and the model doesn't. 'lollipop' might be two tokens; reversing it requires decomposing chunks into letters the model never directly observes. Models often do okay on common words (they've absorbed spelling facts from training text — dictionaries, spelling bees, rhymes) and then fail abruptly on rare words where no such statistical residue exists. A revealing trick from the lecture era: models get *better* at these tasks if you space out the letters first — 'l o l l i p o p' — because each letter becomes its own token and is suddenly visible.

#### Arithmetic

**Arithmetic.** Numbers get chunked arbitrarily by the same frequency logic as words: a number like 1234567 might split as '123'+'4567' while a nearby number splits completely differently. So the digit-by-digit alignment that grade-school addition depends on — line up the ones column, carry the one — is scrambled at the representation level. The model can't reliably 'see' ones, tens, hundreds as positions; it sees frequency-driven chunks whose boundaries ignore place value. Models still learn approximate arithmetic statistically, and tooling improvements (and letting models use calculators/code) help — but the underlying representational awkwardness is a tokenizer artifact, not a reasoning deficit.

The practical skill here isn't memorizing the catalog — it's the inference pattern: *representation explains failure*. When a client hits a weird LLM behavior, the professional move is to check what the model actually received, not to shrug about 'hallucination.'

**Check:** Predict: will an LLM be more reliable reversing 'banana' or reversing 'qzxvnt'? Then explain why spacing the letters out ('q z x v n t') changes the situation.

<details>
<summary>Hint and answer</summary>

**Hint:** The model can't look inside tokens — so where could knowledge of a word's spelling possibly come from? What kind of word has lots of that?

**Answer:** 'banana' — it's common, so spelling facts about it pervade training data even though the model can't see its letters. 'qzxvnt' is rare, with no statistical residue to lean on. Spacing letters makes each character its own token, so the letter sequence becomes directly visible and the task stops depending on memorized spelling.

</details>

### 4. Failure catalog II: the non-English tax and glitch tokens

Two subtler failure families complete the catalog.

#### The non-English tax

**The non-English tax.** BPE merges are earned by frequency in the tokenizer's training corpus — which has historically been heavily English. Result: English text gets long, efficient tokens, while the same meaning in Thai, Hindi, or even German fragments into many more, smaller tokens. Karpathy demonstrates this concretely: a sentence that costs N tokens in English can cost several times that in another language. The consequences are commercial, not just academic — API billing is per token, so non-English users literally pay more per sentence; context windows are measured in tokens, so non-English documents 'fill up' the model's working memory faster; and more-fragmented text is generally harder to model. When a future client asks why their multilingual deployment behaves worse and costs more, this is frequently a chunk of the answer.

#### Glitch tokens

**Glitch tokens.** The famous case: 'SolidGoldMagikarp', a Reddit username that became a single token (documented in 2023 by researchers probing GPT-2/GPT-3-era tokenizers). The mechanism, as Karpathy explains it: the *tokenizer's* training corpus contained this string often enough to earn it a dedicated token — but the *model's* training corpus (a different dataset!) barely contained it. The token therefore sat in the vocabulary with an embedding that was essentially never trained — uninitialized real estate. Prompted with such tokens, models produced bizarre behavior: evasion, insults, unrelated tangents. The deep lesson isn't the comedy; it's the architecture: tokenizer and model are trained on **different data at different times**, and the seams between them are where systems tear. That 'mismatched training between components' failure shape recurs throughout agentic AI, so file the pattern, not just the anecdote.

**Check:** Your client's Hindi-language chatbot costs ~3x more per conversation than the English one and hits context limits sooner. Connect both symptoms to one mechanism.

<details>
<summary>Hint and answer</summary>

**Hint:** Both billing and context windows are denominated in the same unit. What determines how many of that unit a sentence needs?

**Answer:** The tokenizer's BPE merges were learned mostly from English text, so Hindi gets few merges and fragments into many small tokens. Same meaning → more tokens → higher per-token billing AND faster consumption of the token-denominated context window. One cause, both symptoms.

</details>

### 5. Vocabulary size: a real engineering tradeoff

#### The vocabulary question

Last piece: why not just fix all this with a much bigger vocabulary — every word, every number, every language fully covered? Because vocabulary size is a genuine engineering tradeoff, and seeing both sides of it is a good test of whether the whole session has landed.

#### Bigger or smaller

**Push the vocabulary bigger** and sequences get shorter: more text fits in a context window, each forward pass covers more meaning, attention (wait for S6) has fewer positions to relate. But costs mount. Every token needs an embedding vector, and the model's output layer must score every vocabulary entry at every step — both grow linearly with vocabulary size. Worse, with more tokens, each individual token appears more rarely in the training data, so each embedding gets less training signal — push far enough and you're manufacturing thousands of mini-SolidGoldMagikarps: tokens too rare to learn well. **Push the vocabulary smaller** and every embedding is richly trained and the model layers shrink — but text balloons into long sequences, burning context and compute per unit of meaning (the extreme — raw bytes, vocabulary of 256 — is appealingly clean and Karpathy notes the research interest, but sequences get brutally long).

#### Where practitioners land

So practitioners settle in the tens-of-thousands to ~100k+ range — not a law of nature, just the current balance point of compression versus learnability. GPT-2 used 50,257; the cl100k family runs around 100k.

#### The week so far

Zoom out on the week so far: S3 gave you the machine, S4 gave you how its dials get set, and now S5 gives you what the machine actually reads. One sentence ties it together: **a language model is a trained function over token IDs** — and every word of that sentence now means something precise to you.

**Check:** A PM proposes 10x-ing the vocabulary so every English word and every 4-digit number gets its own token. Give one real benefit and the two costs that kill the naive version of this plan.

<details>
<summary>Hint and answer</summary>

**Hint:** Follow each new token to its two obligations: a row in the embedding table, and enough training appearances to make that row meaningful.

**Answer:** Benefit: shorter sequences — more content per context window and per forward pass. Costs: (1) embedding table and output layer grow with vocabulary, inflating model size and per-step compute; (2) each rare token now appears too seldom in training to learn a good embedding — mass-producing undertrained, glitch-prone tokens.

</details>

## Quiz

**1. An LLM reliably reverses 'banana' but mangles reversing 'pneumonoultramicroscopic'. Which explanation fits the tokenization story?**

- A. Longer words exceed the model's context window
- B. Common words leave spelling traces in training data the model can lean on; rare words tokenize into opaque chunks with no such statistical residue to compensate
- C. The model's reversing circuit only handles six letters
- D. Rare words are filtered out of the vocabulary entirely

<details>
<summary>Answer and explanation</summary>

**Correct: B.** Common words leave spelling traces in training data the model can lean on; rare words tokenize into opaque chunks with no such statistical residue to compensate

The model never sees letters in either word — but 'banana' is common enough that its spelling is statistically absorbed from training text. The rare word offers no such crutch, exposing the underlying representational blindness. (Spacing the letters out would fix it by making each letter a visible token.)

</details>

**2. A model adds 23,405 + 8,997 incorrectly, despite 'knowing' arithmetic rules when asked to explain them. What's the tokenizer-level account?**

- A. The numbers exceed the vocabulary's maximum integer
- B. Addition requires digit-position alignment (ones, tens, carry), but BPE chunks digits by frequency into arbitrary groups, scrambling place-value structure at the representation level
- C. Math symbols like '+' aren't tokenizable
- D. The model wasn't trained on any numbers

<details>
<summary>Answer and explanation</summary>

**Correct: B.** Addition requires digit-position alignment (ones, tens, carry), but BPE chunks digits by frequency into arbitrary groups, scrambling place-value structure at the representation level

The same frequency-driven chunking that handles words also carves numbers — '23405' may split as '234'+'05' while '8997' splits differently — so the column-wise alignment grade-school addition needs simply isn't represented cleanly. Knowing the rules verbally and seeing usable digit positions are different capacities.

</details>

**3. During BPE training, what single criterion decides which new token gets created next?**

- A. Whichever merge produces the most linguistically meaningful unit
- B. Whichever adjacent token pair currently occurs most frequently in the training corpus
- C. Alphabetical order of candidate pairs
- D. Whichever pair the model's loss function prefers

<details>
<summary>Answer and explanation</summary>

**Correct: B.** Whichever adjacent token pair currently occurs most frequently in the training corpus

BPE is purely statistical: find the most frequent adjacent pair, merge, replace, repeat. No linguistics, and no model involvement — the tokenizer is trained separately, before the model, and frozen. That separateness is exactly what makes glitch tokens possible.

</details>

**4. What combination of circumstances produced 'SolidGoldMagikarp'-style glitch behavior?**

- A. Hackers inserted adversarial tokens into the vocabulary
- B. The string was frequent in the TOKENIZER's training data (earning a dedicated token) but nearly absent from the MODEL's training data — leaving an essentially untrained embedding that produces erratic behavior when invoked
- C. The token was too long for the embedding layer
- D. The model was fine-tuned to avoid Reddit usernames

<details>
<summary>Answer and explanation</summary>

**Correct: B.** The string was frequent in the TOKENIZER's training data (earning a dedicated token) but nearly absent from the MODEL's training data — leaving an essentially untrained embedding that produces erratic behavior when invoked

Two components, two corpora, one seam: the tokenizer's corpus (with lots of Reddit) granted the username a token; the model's corpus barely contained it, so its embedding never got trained. Prompting with it dropped the model onto uninitialized real estate. File the general pattern: mismatched training between pipeline components.

</details>

**5. Your team doubles the tokenizer vocabulary from 50k to 100k for a new model. Which row correctly pairs a benefit with a cost?**

- A. Benefit: shorter token sequences per document. Cost: larger embedding/output layers and less training signal per rare token
- B. Benefit: the model can finally read non-English text. Cost: slower tokenizer training
- C. Benefit: arithmetic becomes exact. Cost: spelling gets worse
- D. Benefit: embeddings get smaller. Cost: sequences get longer

<details>
<summary>Answer and explanation</summary>

**Correct: A.** Benefit: shorter token sequences per document. Cost: larger embedding/output layers and less training signal per rare token

Bigger vocab = more text compressed per token (shorter sequences, roomier effective context) but a bigger embedding table, a bigger output layer to score, and rarer per-token appearances in training — pushing toward undertrained, glitch-prone tokens. It's a balance point, not a free win.

</details>

**6. A prompt works perfectly, but adding a trailing space before the model's expected completion degrades output quality. Your first hypothesis as the engineer in the room?**

- A. The API is silently truncating the prompt
- B. The space changed tokenization — token boundaries shifted (spaces typically attach to the following word's token), so the model is conditioning on a different, rarer ID sequence than it usually sees
- C. The model interprets whitespace as a stop signal
- D. Trailing spaces increase the temperature parameter

<details>
<summary>Answer and explanation</summary>

**Correct: B.** The space changed tokenization — token boundaries shifted (spaces typically attach to the following word's token), so the model is conditioning on a different, rarer ID sequence than it usually sees

Spaces are part of tokens (' the' vs 'the' are different IDs). A trailing space can strand the model in a token context that rarely occurs in training data. Karpathy demonstrates exactly this class of issue — and 'check what the tokenizer did' is the professional first move for any whitespace-sensitive bug.

</details>

## Produce task

Open a real tokenizer visualizer (e.g. Tiktokenizer at https://tiktokenizer.vercel.app, used in Karpathy's lecture, or OpenAI's tokenizer page). BEFORE touching it, write three predictions in your notes, each naming a failure mode and its mechanism: (1) predict roughly how 'strawberry' and a rare word like 'qzxvnt' will tokenize and what that implies for letter-counting; (2) predict whether a 10-digit number splits into clean digit groups, and what that implies for arithmetic; (3) predict the token-count ratio between one English sentence and its translation in a non-Latin-script language (use any translator for the translation). THEN verify all three, paste the actual token splits into the note, and score your predictions — including at least one thing that surprised you.

**What to hand in:** A note 'Tokenizer lab' with three written predictions, the actual observed token splits, a verified/falsified verdict per prediction, and one recorded surprise.

**Success criteria:**

- All three predictions written BEFORE opening the tokenizer (generation effect — timestamp or honor system).
- Each prediction names the mechanism (token opacity, arbitrary number chunking, frequency-driven merges), not just the expected outcome.
- Actual token boundaries pasted/screenshotted for all three experiments.
- Each prediction explicitly scored as confirmed or falsified, with one sentence on any miss.
- The note states the model-relevant moral in one closing line: the model sees IDs, not characters.

## Teach-back

A client escalates: 'Your AI can't even count the letters in a word — how can we trust it with our contracts?' Give the 2-minute plain-language response: explain what the model actually receives (the glued-shut Lego box, or your own analogy), why letter-counting is therefore a misleading benchmark, and name one task category where this limitation genuinely matters for their use case versus the many where it doesn't. Reassure without overclaiming.

## Sources

- [Andrej Karpathy — 'Let's build the GPT Tokenizer'](https://www.youtube.com/watch?v=zduSFxRajkE) (2h13m video — ~60-75 min at the suggested depth). The primary source: Karpathy builds a BPE tokenizer from scratch and demonstrates every failure mode in this session live. Watch the first ~45 minutes (intro, weirdness catalog, BPE mechanics) carefully; the deep implementation middle can be skimmed; do catch his closing recommendations.

Link status is in [SOURCES.md](../SOURCES.md).
