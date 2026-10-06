# Session 6: Transformers & attention

**Time:** about 150 minutes (the original estimate, not measured here).  
**Core question:** Why did one 2017 architecture change make modern AI possible?

**Aim:** Explain Q/K/V attention with your own tested analogy, and justify the title 'Attention Is All You Need' to a non-technical stakeholder.

**How to use this page:** read each block, then answer its check question before you open the hint and answer. Everything marked "details" is closed on purpose. Try first.

## Lesson

### 1. Before transformers: the RNN bottleneck

#### The before picture

To feel why 2017 mattered, you need the 'before' picture. Through the mid-2010s, the dominant architecture for language was the **recurrent neural network (RNN)** and its refinements. An RNN reads a sentence the intuitive way: one token at a time, left to right, maintaining a running summary — a fixed-size 'hidden state' — that it updates at each step. Token in, summary updated, next token. By the end of the sentence, everything the network knows about it must live in that one summary vector.

Two structural problems follow, and the Attention Is All You Need authors call out both.

#### The forgetting problem

**The forgetting problem.** A fixed-size summary is a bottleneck: by token 400 of a long document, the influence of token 3 has been squeezed, overwritten, and diluted through hundreds of updates. Relating words across long distances — a pronoun on page two to its referent on page one — degrades with distance. Refinements (LSTMs, and attention bolted onto RNNs as a helper) eased this without curing it.

#### The parallelism problem

**The parallelism problem** — quieter, and ultimately the killer. Each step's computation needs the previous step's output, so processing is inherently **sequential**: you cannot compute step 400 until step 399 finishes. But the hardware revolution of the era was GPUs, which are spectacular at doing millions of things *simultaneously* and unimpressive at long dependent chains. RNNs were architecturally mismatched with the only hardware capable of training at scale: within each sequence, the work couldn't be spread out.

Hold both problems in mind as the design constraints. The transformer is what you get if you ask: can we relate every token to every other token *directly* — no distance decay — using only operations that can all happen *at once*?

**Check:** Of the two RNN problems — forgetting over distance and sequential processing — which one ultimately blocked SCALE, and why exactly does a GPU care?

<details>
<summary>Hint and answer</summary>

**Hint:** One problem hurts quality; the other dictates how much hardware you can usefully throw at training. Which is which?

**Answer:** The sequential problem. Each RNN step depends on the previous step's output, forming a dependency chain that can't be parallelized within a sequence. GPUs derive their power from doing massive numbers of independent operations simultaneously; a long dependent chain leaves that capacity idle, so training couldn't exploit the era's only scalable hardware.

</details>

### 2. Attention: every word polls every other word

#### Self-attention

The transformer's core operation — **self-attention** — answers the forgetting problem with brute directness: instead of relaying information through a chain of summaries, let every token look at every other token *directly*, in one step. Token 3 to token 400: one hop, same as next-door neighbors. Distance stops mattering structurally.

#### What it is for

What's it for? Words don't carry fixed meanings — context assigns them. 'Bank' near 'river' versus near 'loan'; 'it' meaning whatever it points back to. After tokenization (S5), each token starts as an embedding that's essentially context-free — 'bank' arrives ambiguous. Attention is the machinery that lets each token **update its own representation by selectively absorbing information from relevant other tokens**. The 3Blue1Brown attention chapter frames it exactly this way: attention moves information between positions so each embedding comes to reflect its actual meaning *in this sentence*.

#### A worked example

Jay Alammar's running example makes it concrete: 'The animal didn't cross the street because it was too tired.' What does 'it' refer to? You resolve this instantly: animal (streets aren't tired). For the model, when the token 'it' is processed, attention computes a relevance score between 'it' and every other token in the sentence; 'animal' scores high; and 'it''s representation is updated to incorporate a large helping of 'animal''s content. The pronoun's vector literally becomes more animal-flavored. (Swap 'tired' for 'wide' and the same machinery should bind 'it' to 'street' instead — the scores are computed fresh from the actual sentence.)

The word 'attention' is apt: a learned, differentiable way of deciding *what to look at* when interpreting each position. The next block opens the hood on how those relevance scores actually get computed.

**Check:** In 'The trophy didn't fit in the suitcase because it was too big,' what should attention do when processing 'it' — and what changes if 'big' becomes 'small'?

<details>
<summary>Hint and answer</summary>

**Hint:** Ask first what a human resolves 'it' to in each variant, then describe attention's job as: make the pronoun's vector absorb the right noun's content.

**Answer:** 'it' should score high relevance with 'trophy' (things that are too big don't fit) and absorb its content, binding the pronoun to trophy. With 'small,' the sensible referent flips to 'suitcase' — and attention scores, computed fresh from this sentence's actual tokens, should shift accordingly. Same machinery, context-dependent outcome.

</details>

### 3. Q, K, V: the matching machinery

#### Relevance by matching

How does the model compute 'relevance' between tokens? Through three vectors derived from each token, with roles worth memorizing cold: **Query**, **Key**, and **Value**.

#### The filing-system analogy

The cleanest analogy: a well-organized filing system. Every token simultaneously plays two parts — searcher and searchee. As a searcher, it issues a **Query**: 'here's what I'm looking for.' (The token 'it' effectively queries: anyone here a singular noun an adjective could describe?) As a searchee, every token displays a **Key** — the label on its folder: 'here's what I am, for matching purposes' ('animal': singular noun, agent of the sentence). Compare a query against all keys and you get relevance scores. Then the third piece: the **Value** is what's *inside* the folder — the content a token actually contributes once selected. The label gets you matched; the contents are what you take away. Keys advertise; values deliver.

#### Where Q, K and V come from

Where do these three vectors come from? Nobody writes them. Each token's embedding is multiplied by three **learned weight matrices** — W_Q, W_K, W_V — producing its query, key, and value. Those matrices are weights like any in S3, set by gradient descent like everything in S4. During training, the model is optimized to predict text; useful matching behavior emerges because it *helps* — backprop assigns blame straight through the attention computation, sculpting W_Q and W_K so that genuinely relevant pairs score high.

#### A caveat

One honest caveat, in the spirit of S3's interpretability warning: the crisp 'looking for a noun' glosses are illustrative. Real learned queries and keys are vectors whose 'meaning' is implicit and often not human-nameable. The structure — match via Q·K, deliver via V — is exact; the neat stories about what any head is matching are post-hoc interpretation.

**Check:** In the filing-system analogy: why does the system need keys AND values to be separate vectors — what goes wrong if a token's key IS its value?

<details>
<summary>Hint and answer</summary>

**Hint:** The label on a folder versus the document inside it: what is each optimized FOR?

**Answer:** Matching and content are different jobs. What makes a token findable ('singular noun, sentence subject') isn't the same as what it should contribute once found (its semantic content). Fusing them forces one vector to serve both purposes, degrading both — like a filing label that must double as the document. Separate learned projections let each be optimized for its role.

</details>

### 4. From scores to a new representation

#### The full computation

Now the full computation for one token, end to end — worth walking through once slowly, because it's the formula in the Attention Is All You Need paper (their Figure 2 and Equation 1: 'Scaled Dot-Product Attention').

#### Step 1: score

**Step 1 — score.** Take the token's query and compute its **dot product** with every token's key. A dot product is just a similarity measure between two vectors — multiply matching components, add up — yielding one number per pair: raw relevance.

#### Step 2: scale

**Step 2 — scale.** Divide every score by the square root of the key dimension (√d_k). Mechanical-sounding, but principled: with long vectors, raw dot products grow large, and large scores would slam the next step into its extreme, gradient-starved regime. The paper introduces this scaling explicitly to keep training stable — hence 'scaled dot-product attention.'

#### Step 3: softmax

**Step 3 — softmax.** Convert the scaled scores into proper weights: all positive, summing to exactly 1. Think of it as a fixed relevance *budget* — softmax decides how to split 100% of this token's attention across all tokens, sharpening contrasts so strong matches claim most of the budget.

#### Step 4: blend

**Step 4 — blend.** Compute the weighted sum of all tokens' **values**, using those weights. If 'animal' got 0.7 of 'it''s budget, the blend is 70% animal-content. This blended vector is the output: the token's representation, updated by exactly the information it judged relevant.

#### The whole core

That's genuinely the whole core — score, scale, normalize, blend — repeated for every token (in parallel!), and stacked across many layers so meanings refine progressively. When you annotate your diagram today, these four steps are the spine of it.

**Check:** Why does attention pass scores through softmax instead of just using raw dot products directly as blending weights?

<details>
<summary>Hint and answer</summary>

**Hint:** What properties must a set of blending proportions have? Check whether raw dot products have any of them.

**Answer:** Raw dot products can be negative or arbitrarily large — meaningless as blend proportions. Softmax converts them into positive weights summing to 1: a well-defined relevance budget where each token's update is a proper weighted average of values, with contrast sharpened so strong matches dominate. (And the √d_k scaling beforehand keeps softmax out of its saturated, gradient-starved extremes.)

</details>

### 5. Multi-head: many relationships at once

#### One head is not enough

One attention computation produces one pattern of relevance — one 'way of looking' at the sentence. But language runs many relationship types simultaneously: pronouns need referents, verbs care about subjects and objects, adjectives bind to nouns, and meaning can hinge on words being near or far. A single attention pattern would have to compress all of these into one blend — muddying each.

#### Multiple heads

The transformer's answer: run several attention operations **in parallel**, each with its own learned W_Q, W_K, W_V matrices. Each parallel copy is a **head**; the original paper used 8 per layer. Because each head has its own projections, each can learn its own notion of relevance — its own matching game. Alammar visualizes this memorably for the 'animal...it...tired' sentence: one head's attention from 'it' concentrates on 'the animal' while a different head's concentrates on 'tired' — the pronoun simultaneously gathering *what it refers to* and *what's being said about it*. Each head's output blend is computed separately, the results are concatenated, and one more learned projection mixes them back into a single vector per token. (Usual caveat applies: heads aren't assigned roles; whatever division of labor emerges, emerges from training, and many heads resist tidy human labels.)

#### The transformer block

Then the full transformer block: attention is the *communication* step (tokens exchange information), followed by a feed-forward network applied to each position — the *computation* step (each token processes what it gathered, alone). Stack this pair of steps dozens of times and you have the architecture. By the deep layers, each position's vector has absorbed and processed context repeatedly — which is how 'bank' ends up unambiguous, and how the final position ends up informative enough to predict what token comes next.

**Check:** Why is 8 heads with smaller Q/K/V vectors preferable to one head with giant ones — what specifically can 8 heads do that one big head cannot?

<details>
<summary>Hint and answer</summary>

**Hint:** Count the softmax distributions per token in each design. What does having only one force the model to do with multiple distinct relationships?

**Answer:** Maintain 8 independent relevance patterns at once. One head, however large, produces a single softmax distribution per token — one blend that must average together coreference, syntax, modification, and more. Separate heads with separate learned projections can each specialize in a different relationship and contribute distinct information that's combined afterward.

</details>

### 6. Why 'all you need' — and why it scaled

#### The title's claim

Now the title, which is a precise technical claim, not swagger. By 2017, attention was already known and used — *bolted onto* RNNs as a helper mechanism in translation systems. The paper's claim: the crutch was the whole leg. Keep attention plus simple feed-forward layers, **discard recurrence entirely** (and convolutions too), and translation quality goes *up* — the paper's transformer beat the best existing systems on standard English-German and English-French translation benchmarks. Attention isn't an additive — it's sufficient. Hence: attention is all you need.

#### Why it scaled

Why did this reshape the industry rather than just translation leaderboards? Recall the RNN's quiet killer from block one: sequential processing. In a transformer, every token's attention — all queries, keys, values, scores, blends — is computable **simultaneously** across the whole sequence, as giant matrix multiplications. And giant parallel matrix multiplications are precisely what GPUs do best. The architecture finally matched the hardware. Training that was bottlenecked by dependency chains became bottlenecked only by how many chips you could buy — and 'how many chips' is a problem money solves. Researchers kept finding that bigger transformers plus more data reliably meant better models, further and further than anyone expected; the GPT lineage — Generative **Pretrained Transformer** — is this one architecture scaled relentlessly, and S5's tokenizer is exactly what feeds it.

#### The cost

One honest cost to carry forward: because every token attends to every token, attention's compute grows roughly with the *square* of sequence length — doubling context far more than doubles the work. That quadratic bill is a core reason long context windows are expensive and a driver of ongoing architecture research.

#### The full stack

You now hold the complete stack: a function with learnable dials (S3), set by descending a loss (S4), reading token IDs (S5), relating them through attention (S6). Everything agentic builds on top of this object.

**Check:** Construct the causal chain: how does 'removed recurrence' lead, step by step, to 'ChatGPT became possible'?

<details>
<summary>Hint and answer</summary>

**Hint:** Five links: dependency chain gone → parallel matrix math → GPU fit → scale becomes purchasable → scaling kept paying off.

**Answer:** Removing recurrence removed the within-sequence dependency chain → every position's attention computes simultaneously as big matrix multiplications → which is exactly what GPUs excel at → so training scale became limited by hardware budget, not architecture → bigger transformers + more data kept yielding better models → scaled relentlessly, that recipe produced the GPT lineage.

</details>

## Quiz

**1. An RNN-based translator from 2015 handles short sentences well but garbles references in long documents — pronouns connect to the wrong antecedents pages apart. Which architectural property predicts exactly this?**

- A. Its vocabulary was too small for long documents
- B. All information must persist through a fixed-size hidden state updated at every step, so early content gets diluted and overwritten across hundreds of updates
- C. Its learning rate decayed too quickly during training
- D. RNNs cannot process punctuation

<details>
<summary>Answer and explanation</summary>

**Correct: B.** All information must persist through a fixed-size hidden state updated at every step, so early content gets diluted and overwritten across hundreds of updates

The fixed-size running summary is a bottleneck: by the time a distant pronoun is processed, the referent's contribution has been squeezed through many updates. Distance degrades the connection structurally — the exact weakness attention's direct token-to-token links eliminate.

</details>

**2. In 'The trophy didn't fit in the suitcase because it was too big,' attention resolves 'it' correctly. Which sequence describes the mechanism?**

- A. 'it' looks up 'trophy' in a fixed grammar table learned before training
- B. 'it''s query scores high against 'trophy''s key; softmax gives 'trophy' a dominant share of the relevance budget; 'it''s representation becomes a value-blend rich in trophy-content
- C. The nearest preceding noun always wins, and 'suitcase' is excluded for being inside a prepositional phrase
- D. 'trophy''s value is copied verbatim to replace 'it''s embedding

<details>
<summary>Answer and explanation</summary>

**Correct: B.** 'it''s query scores high against 'trophy''s key; softmax gives 'trophy' a dominant share of the relevance budget; 'it''s representation becomes a value-blend rich in trophy-content

Score (query·key), normalize (softmax budget), blend (weighted values) — and it's a weighted blend, not a copy-paste, so 'it' keeps its own content while absorbing trophy-content. Nearest-noun heuristics fail this very sentence ('suitcase' is nearer), which is the point: relevance is computed, not positional.

</details>

**3. Two models with identical parameter counts train on identical data and hardware: one RNN, one transformer. The transformer finishes training far sooner. The principal reason?**

- A. Transformers need fewer training examples to converge
- B. Attention's computations across all positions happen simultaneously as large matrix operations — saturating GPU parallelism — while the RNN must process each sequence step-by-step
- C. Transformers skip the backpropagation step
- D. RNN loss functions are not smooth, so gradient descent fails

<details>
<summary>Answer and explanation</summary>

**Correct: B.** Attention's computations across all positions happen simultaneously as large matrix operations — saturating GPU parallelism — while the RNN must process each sequence step-by-step

Within each sequence the RNN has an unbreakable dependency chain (step n needs step n−1); the transformer has none — every position's Q/K/V and blends compute at once. Same gradient machinery, radically different hardware utilization. This is the property that made scale purchasable.

</details>

**4. Inspecting a trained transformer, you find one attention head where pronouns attend to their referents and another where adjectives attend to the nouns they modify. What does this illustrate?**

- A. The architects assigned each head a grammatical rule before training
- B. Multi-head attention's purpose: separate learned Q/K/V projections let each head specialize in a different relationship type, with outputs combined afterward — though such tidy roles emerge from training rather than design, and many heads defy clean labels
- C. The model has exactly two relationship types it can represent
- D. Heads are redundant copies for fault tolerance

<details>
<summary>Answer and explanation</summary>

**Correct: B.** Multi-head attention's purpose: separate learned Q/K/V projections let each head specialize in a different relationship type, with outputs combined afterward — though such tidy roles emerge from training rather than design, and many heads defy clean labels

Each head runs its own matching game via its own projections, so distinct relevance patterns coexist per token instead of being averaged into one blend. The roles are emergent and only sometimes interpretable — the same honest caveat as S3's feature-detector story.

</details>

**5. A colleague claims the 2017 paper 'invented attention.' What's the historically and technically accurate correction?**

- A. Correct as stated — attention first appeared in that paper
- B. Attention predated the paper as an add-on to RNN systems; the paper's claim was that attention (plus feed-forward layers) SUFFICES — recurrence could be removed entirely, improving both quality and parallelizability
- C. The paper invented the GPU kernel for attention but not the concept
- D. The paper actually argued against attention in favor of convolutions

<details>
<summary>Answer and explanation</summary>

**Correct: B.** Attention predated the paper as an add-on to RNN systems; the paper's claim was that attention (plus feed-forward layers) SUFFICES — recurrence could be removed entirely, improving both quality and parallelizability

Hence the title: attention is ALL you need — sufficiency, not novelty, was the claim. Attention had been a helper bolted onto recurrent translation models; removing the recurrence and keeping the helper beat the state of the art while unlocking parallel training.

</details>

**6. Your client wants to jump from a 4k-token to a 400k-token context window and asks why vendors don't 'just do it.' Grounded in this session, your first-order answer?**

- A. Longer contexts require retraining the tokenizer from scratch
- B. Self-attention relates every token to every other token, so compute grows roughly with the square of length — 100x the context costs on the order of 10,000x the attention work, which is why long context is expensive and an active research target
- C. Models forget their training data beyond 4k tokens
- D. GPUs have a hard 4k limit on matrix size

<details>
<summary>Answer and explanation</summary>

**Correct: B.** Self-attention relates every token to every other token, so compute grows roughly with the square of length — 100x the context costs on the order of 10,000x the attention work, which is why long context is expensive and an active research target

All-pairs relevance is attention's superpower and its bill: quadratic growth in sequence length. (Long-context systems exist via heavy engineering and architectural variants, but the quadratic baseline is the reason it's hard.) Connecting a client's feature request to the mechanism is the kind of link a practitioner should be able to make.

</details>

## Produce task

Three artifacts in your notes. (1) ANALOGY SET: write three original analogies for Q/K/V (not the filing system from the lesson — your own; e.g. hiring, dating apps, asking a conference room for help). For each, label what plays query, key, and value — then stress-test it: write one sentence on where the analogy BREAKS (e.g. does it capture that every token is simultaneously searcher and searchee? that weights come from a budget summing to 1?). (2) ANNOTATED DIAGRAM: hand-draw attention for the sentence 'The cat sat because it was tired' from the perspective of the token 'it': show its query meeting every key, plausible scores, softmax into weights, and the value blend. Label the four steps: score, scale, normalize, blend. (3) STAKEHOLDER PARAGRAPH: 5 sentences explaining the paper title 'Attention Is All You Need' to a non-technical executive — what existed before, what the paper removed, what it kept, and why that unlocked scale.

**What to hand in:** A note with three stress-tested Q/K/V analogies + photographed annotated diagram + 5-sentence stakeholder paragraph.

**Success criteria:**

- Each analogy correctly distinguishes the three roles — especially key (matching label) vs value (delivered content).
- Each analogy has an honest written breaking point — no analogy presented as perfect.
- The diagram shows ONE query compared against ALL keys (including 'it' itself), and weights that visibly sum to a whole.
- The four computation steps are labeled in order on the diagram.
- The stakeholder paragraph names what was removed (recurrence), what remained (attention + feed-forward), and the parallelism-to-scale causal link — without using the words 'matrix', 'vector', or 'softmax'.

## Teach-back

Board-meeting framing: an executive asks, 'Every AI vendor says transformer this, transformer that. In plain terms: what was the 2017 breakthrough, and why should I believe it's why this stuff suddenly works?' Deliver 2-3 minutes: the before-state (reading word by word, forgetting, unparallelizable), the change (every word attends to every word, all at once), and the consequence (architecture matched the hardware, so capability became purchasable with scale). One analogy maximum, zero undefined jargon, and end with the one limitation (cost grows steeply with context length) so you sound like an engineer, not a salesperson.

## Sources

- [Jay Alammar — 'The Illustrated Transformer'](https://jalammar.github.io/illustrated-transformer/) (35-45 min read). The most-cited visual walkthrough of the architecture, used in university courses (Stanford, MIT among them) — Q/K/V, scores, softmax, multi-head, all diagrammed step by step on the 'animal...it' example. Read it after the lesson blocks; the diagrams will anchor everything.
- [Vaswani et al. (2017) — 'Attention Is All You Need'](https://arxiv.org/abs/1706.03762) (15 min (abstract + figures)). The primary source — the paper that introduced the transformer. Read the abstract and study Figures 1-2 (architecture and scaled dot-product/multi-head attention) only; the goal is recognizing that the diagrams now make sense, not parsing the full paper.
- [3Blue1Brown — 'Visualizing Attention, a Transformer's Heart' (Deep learning series)](https://www.3blue1brown.com/lessons/attention) (26 min video). Grant Sanderson animating Q/K/V and the information-moving view of attention — the best available visualization of WHY the mechanism updates meanings, complementing Alammar's WHAT. Same trusted source as S3-S4, so it also reinforces that series' framing.

Link status is in [SOURCES.md](../SOURCES.md).
