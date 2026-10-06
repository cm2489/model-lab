# Session 4: How models learn: gradient descent & backprop

**Time:** about 120 minutes (the original estimate, not measured here).  
**Core question:** How does a network find good values for thousands of weights it could never try one by one?

**Aim:** Compute one gradient-descent step by hand on a two-weight toy neuron, and explain precisely what backpropagation contributes versus what gradient descent contributes.

**How to use this page:** read each block, then answer its check question before you open the hint and answer. Everything marked "details" is closed on purpose. Try first.

## Lesson

### 1. Loss: compressing wrongness into one number

S3 left us with 13,002 randomly-set dials and garbage outputs. Step one of fixing them is deceptively important: define a single number that measures how wrong the network currently is. This is the **cost function**, also called the **loss**.

#### What loss is

The version 3Blue1Brown uses: show the network a training image whose label you know — say a 3. The ideal output would be activation 1.0 on the '3' neuron and 0.0 on the other nine. Take the network's actual ten outputs, subtract the ideal ones, square each difference, and add them up. That's the cost of one example: near zero when the network nails it, large when it's confidently wrong (squaring punishes big misses disproportionately). Then average this over thousands of training examples, and you get one number summarizing how badly the *entire current setting of all 13,002 weights and biases* performs. Notice the reframing: the loss is a function whose *inputs are the weights themselves*. Images and labels are temporarily frozen facts; the dials are the variables.

#### Why loss must be smooth

Why insist on a single smooth number rather than something natural like 'percent correct'? Because accuracy is a staircase: nudge a weight slightly and accuracy usually doesn't change at all — then suddenly jumps when some example flips its answer. A staircase gives you no slope, no sense of 'warmer or colder,' nothing to follow. The squared-error loss changes *smoothly* as you nudge any weight, so every tiny nudge gets graded. That smoothness is the entire foundation: it converts 'make the network better' — a vague aspiration — into 'make this one number smaller' — a precise math problem with a usable signal at every point.

**Check:** Why would 'percentage of training images classified correctly' fail as the number to optimize during training, even though it's what we ultimately care about?

<details>
<summary>Hint and answer</summary>

**Hint:** Imagine nudging one weight by 0.0001. What happens to accuracy? What happens to the summed squared differences?

**Answer:** Accuracy is a staircase function of the weights: tiny nudges almost never change which answers flip, so the signal is flat almost everywhere — no slope to follow. Squared-error loss changes smoothly with every nudge, grading even microscopic improvements, which is what a downhill-following procedure needs.

</details>

### 2. Gradient descent: feel the slope, step downhill

#### Loss as a landscape

Now picture the loss as a landscape. With just two weights you could literally plot it: a surface over a plane, where each point is a (w1, w2) setting and the height is the loss there. The real network's landscape lives over 13,002 dimensions — unvisualizable, but the same object. Training is finding a low point.

#### Rolling downhill

The algorithm is the obvious one, done carefully. You're standing on a hillside in dense fog (you can't see the valley — there are too many dimensions to survey). What you CAN do is feel the slope under your feet. The **gradient** is exactly that information, made precise: it's the vector of all 13,002 sensitivities — for each weight, how much the loss rises per unit increase of that weight. The gradient points in the direction of steepest *ascent*; so you step in the **opposite** direction, the steepest descent. Recompute the slope where you land. Step again. Repeat thousands of times. That's **gradient descent** — the whole training loop of modern AI in one sentence: compute the slope of wrongness, step downhill, repeat.

#### Two refinements

Two refinements make the picture honest. First, each component of the gradient has a sign AND a magnitude: the sign says which way to nudge that particular weight (up or down), and the magnitude says how much that weight currently *matters* — big component, big lever; near-zero component, that dial is locally almost irrelevant. A gradient step therefore changes influential weights a lot and irrelevant ones barely at all, automatically. Second, you never leap to the bottom — the slope only describes the terrain right where you stand, so you take a modest step and re-measure. How modest is the next block's topic.

**Check:** Map each element of the fog-on-a-hillside analogy to its mathematical counterpart: the hiker's position, the fog, the felt slope, the step.

<details>
<summary>Hint and answer</summary>

**Hint:** Each physical element corresponds to exactly one of: weight vector, gradient, locality of information, parameter update.

**Answer:** Position = the current setting of all weights (a point in 13,002-dimensional space). Fog = you can't survey the global landscape, only local information. Felt slope = the gradient: each weight's local sensitivity, with direction and magnitude. The step = updating every weight a small amount against its gradient component — steepest local descent.

</details>

### 3. Learning rate: the size of your steps

The gradient gives a direction; it deliberately doesn't tell you how far to move. That's a hyperparameter you choose — the **learning rate** — and it's the first knob practitioners reach for when training misbehaves, so build the intuition properly.

#### Steps too large or too small

**Too large:** the slope you measured is only valid near where you stand. Take a huge step down a steep slope and you can sail straight across the valley floor and land *higher* on the opposite wall. Measure there, leap again, overshoot again — the loss oscillates or climbs, and training diverges. The telltale symptom: loss bouncing around or exploding. **Too small:** every step is technically correct and pathetically tiny. Loss creeps down; training that should take hours takes weeks, or stalls in shallow terrain making no visible progress. The telltale: a loss curve flatlining at a high value while everything is 'working.'

#### Steps shrink on their own

A standard refinement comes free with the math: since the update is (learning rate × gradient component), and gradient components shrink as the terrain flattens near a minimum, steps *automatically* get smaller as you approach the bottom — like a ball slowing as the bowl levels out. This helps you settle instead of overshooting forever. In practice engineers also schedule the learning rate explicitly (start larger, decay it), but the principle is what matters here.

#### Reading training curves

Grasp the trade and you can already read training curves like a practitioner: smooth steady descent — healthy; violent oscillation — rate too high; flat high plateau — possibly too low (among other causes you'll meet later). For a parameter that's just 'one float,' it owns a remarkable share of deep learning's day-to-day debugging.

**Check:** A colleague shows you a loss curve that drops briefly, then oscillates wildly upward. Another shows one that decreases imperceptibly for hours. Diagnose each using this block.

<details>
<summary>Hint and answer</summary>

**Hint:** One failure comes from steps that outrun the validity of the local slope; the other from steps too timid to make progress.

**Answer:** First: learning rate too large — steps overshoot the valley, each leap landing on a higher slope, so loss bounces and diverges. Second: consistent with a learning rate too small — every step is correct but tiny, so descent is real but glacial. (Both warrant adjusting the rate first, since it's the cheapest hypothesis to test.)

</details>

### 4. Backprop: the blame ledger

#### The problem

Everything so far assumes you can obtain the gradient — all 13,002 sensitivities. Backpropagation is the algorithm that computes them *efficiently*. Be precise about the division of labor, because people constantly blur it: **gradient descent decides how to use slopes; backpropagation computes the slopes.**

#### Why the obvious method fails

Why is computing them hard? The naive method: nudge weight #1 a hair, re-run the network, see how the loss moved — that ratio approximates one sensitivity. Now repeat for weight #2... that's one full forward pass *per weight*, 13,002 passes for one step of our toy network — and billions per step for a frontier model. Dead on arrival. Backprop gets every sensitivity in roughly the cost of **one** backward sweep through the network.

#### The backprop idea

The idea, intuitively: the network is a chain of simple computations, and the chain rule of calculus says the sensitivity of the final loss to any early quantity is the product of sensitivities along the path connecting them. So start at the output, where blame is obvious — this output neuron was 0.8 and should have been 0.0 — and propagate that blame backward, layer by layer. Each neuron splits its share of blame among the weights and activations that fed it, in proportion to their influence: a weight attached to a strong input activation gets more blame (changing it moves the output more) than the same-sized weight on a near-zero input. One backward sweep, and every weight in every layer has its blame assigned — which is exactly the gradient.

The payoff of the magnitude story from last block now sharpens: backprop doesn't just say 'all weights, nudge down.' It says *which* weight changes matter most, quantitatively, network-wide — the full ledger of who-caused-how-much-error, at the cost of one pass.

**Check:** A weight in the first hidden layer is many steps removed from the output. By what reasoning does it receive a precise share of blame for an error at the output?

<details>
<summary>Hint and answer</summary>

**Hint:** The weight affects its neuron's output, which affects the next layer's neurons, which... — what mathematical tool turns a chain of 'affects' into one number?

**Answer:** Through the chain rule: the loss's sensitivity to that weight is the product of local sensitivities along the path(s) from the weight through intermediate neurons to the output. Backprop computes this by passing blame backward layer by layer, each neuron distributing its received blame to its inputs in proportion to their influence.

</details>

### 5. Local minima and stochastic descent: imperfect on purpose

Two final honest complications round out the picture.

#### Local minima

**The landscape isn't a single bowl.** A real loss surface has many valleys: gradient descent only ever walks downhill, so it settles into whichever local minimum its starting point flows toward — possibly never finding the globally lowest point. This sounds fatal and, in practice, mostly isn't. For large networks, the working experience of the field is that there are very many settings good enough to be useful, and descent reliably finds one. You don't need the best valley; you need a good valley. (The full geometry of why high-dimensional landscapes are this forgiving is an active research area — fine to hold it at this level of generality.)

#### Stochastic descent

**Nobody computes the true gradient anyway.** The honest loss is an average over the whole training set — recomputing it for every step is brutally expensive. So instead: shuffle the data, grab a small random **mini-batch** (say 100 examples), compute the gradient on just that batch, step, grab the next batch. This is **stochastic gradient descent (SGD)**. Each step is now noisy — the batch's slope only approximates the true slope — so the path wanders. 3Blue1Brown's image: a drunk man stumbling quickly downhill beats a careful surveyor computing the perfect direction for each of his rare, deliberate steps. The wandering is a price worth paying for taking hundreds of steps in the time one perfect step would cost — and the noise even helps jiggle you out of poor little dips along the way.

#### The whole machine

Assemble the whole machine: loss measures wrongness smoothly; backprop computes every weight's blame in one backward sweep; SGD steps downhill fast and noisily; the learning rate sizes the steps. That loop, iterated millions of times, is how every network you'll study from here on — including the ones that write code — got its dials set.

**Check:** Give two distinct reasons why noisy mini-batch steps beat exact full-dataset steps in practice.

<details>
<summary>Hint and answer</summary>

**Hint:** One reason is about the budget (steps per unit compute); the other is about what randomness does to a walker stuck in a small dip.

**Answer:** (1) Speed: a mini-batch gradient costs a tiny fraction of a full-dataset gradient, so you take vastly more steps per hour, and the noisy steps still trend downhill. (2) The noise itself can be useful — random jiggle helps the optimizer escape shallow dips that would trap an exact descent.

</details>

## Quiz

**1. A network achieves loss ≈ 0 on its training set. What is the strongest correct conclusion?**

- A. It will perform equally well on new examples
- B. Its weights produce near-ideal outputs for the training examples — which says nothing yet about unseen data
- C. Gradient descent found the global minimum of all possible settings
- D. The learning rate was optimally chosen

<details>
<summary>Answer and explanation</summary>

**Correct: B.** Its weights produce near-ideal outputs for the training examples — which says nothing yet about unseen data

Loss is measured ON the training data: zero loss means the function fits those examples. Generalization to new data is a separate question (and fitting training data too perfectly can even hurt it). Neither global optimality nor learning-rate quality follows.

</details>

**2. Toy neuron: y = w·x with x = 2, w = 0.5, target = 3, loss = (y − target)². The sensitivity dL/dw = 2(y−target)·x = −8. What does the next gradient-descent step do?**

- A. Decreases w, since the gradient is negative
- B. Increases w, since we subtract (learning rate × −8), and a larger w raises y toward the target of 3
- C. Leaves w unchanged until more data arrives
- D. Sets w directly to the value that makes y = 3

<details>
<summary>Answer and explanation</summary>

**Correct: B.** Increases w, since we subtract (learning rate × −8), and a larger w raises y toward the target of 3

Update rule: w_new = w − lr × gradient = w − lr × (−8) = w + 8·lr, so w rises. Sanity check: y = 1 is below target 3, and increasing w increases y. Gradient descent never jumps straight to the answer — it steps and re-measures.

</details>

**3. Why is backpropagation essential, given that you could estimate each weight's sensitivity by nudging it and re-running the network?**

- A. Nudging gives mathematically wrong answers
- B. Nudging requires one forward pass per weight — millions or billions of passes per step — while backprop recovers every sensitivity in roughly one backward sweep
- C. Backprop finds better minima than nudging would
- D. Nudging only works on networks without activation functions

<details>
<summary>Answer and explanation</summary>

**Correct: B.** Nudging requires one forward pass per weight — millions or billions of passes per step — while backprop recovers every sensitivity in roughly one backward sweep

Nudge-and-rerun is a valid approximation but catastrophically expensive at scale. Backprop's contribution is purely efficiency: the chain rule lets one backward pass assign every weight its exact blame. Same gradient, ~one pass instead of one per parameter.

</details>

**4. Mid-training, the gradient component for a particular weight is almost exactly zero. The right interpretation?**

- A. That weight is optimally set for the final network
- B. Backprop failed to reach that layer
- C. The loss is locally insensitive to that weight right now, so this step will barely change it — though later steps might
- D. The weight should be deleted to shrink the model

<details>
<summary>Answer and explanation</summary>

**Correct: C.** The loss is locally insensitive to that weight right now, so this step will barely change it — though later steps might

Gradient magnitude = local influence on the loss. Near-zero means 'this dial barely matters from where we currently stand' — a statement about the present neighborhood, not a permanent verdict; as other weights move, its sensitivity can change.

</details>

**5. Why does the field accept SGD's noisy mini-batch gradients instead of computing the true full-dataset gradient each step?**

- A. Mini-batch gradients are more accurate than full-dataset ones
- B. Noisy-but-cheap steps allow vastly more steps per unit compute, still trend downhill on average, and the jitter can even help escape shallow dips
- C. Full-dataset gradients cause the loss to increase
- D. GPUs cannot process more than a few hundred examples

<details>
<summary>Answer and explanation</summary>

**Correct: B.** Noisy-but-cheap steps allow vastly more steps per unit compute, still trend downhill on average, and the jitter can even help escape shallow dips

It's an economics decision with a side benefit: hundreds of stumbling steps beat one perfect step per unit time (the 'drunk man downhill' image), and stochasticity helps the walker jiggle out of small local dips. Full-batch gradients aren't wrong — just slow.

</details>

**6. An engineer says: 'We use backprop instead of gradient descent.' What's the precise correction?**

- A. Backprop replaced gradient descent in modern systems, so they're right
- B. They're complementary, not alternatives: backprop computes the gradient (each weight's sensitivity); gradient descent is the procedure that uses it to update weights
- C. Gradient descent computes the gradient and backprop applies it
- D. The two terms are exact synonyms

<details>
<summary>Answer and explanation</summary>

**Correct: B.** They're complementary, not alternatives: backprop computes the gradient (each weight's sensitivity); gradient descent is the procedure that uses it to update weights

Division of labor: backprop = how the slopes are computed (chain rule, backward sweep); gradient descent = what's done with them (step downhill, scaled by learning rate). Conflating them is the single most common imprecision in casual ML talk — worth being the person who keeps it straight.

</details>

## Produce task

On paper, run one full gradient-descent step by hand for a toy neuron with NO activation function: output y = w1·x1 + w2·x2, loss L = (y − target)². Given: x1 = 2, x2 = 1, w1 = 0.5, w2 = −1.0, target = 1, learning rate = 0.1. Steps: (a) compute y and L; (b) compute the sensitivities dL/dw1 = 2(y−target)·x1 and dL/dw2 = 2(y−target)·x2; (c) update each weight: w_new = w_old − learning_rate × sensitivity; (d) recompute y and L with the new weights; (e) write 2-3 sentences: why did w1 move more than w2, and what does that illustrate about gradients? Attempt every step before checking.

**What to hand in:** A photographed page of hand-worked calculations plus the short reflection, kept in your notes.

Do every step on paper first. Open the box below only when you have an answer for each step.

<details>
<summary>Worked answers and success criteria</summary>

**Worked answers:** y = 0, L = 1; dL/dw1 = −4, dL/dw2 = −2; new w1 = 0.9, new w2 = −0.8; new y = 1.0, new L = 0.

**Success criteria** (these repeat the answers, so they are hidden too):

- Initial forward pass correct: y = 0, L = 1.
- Both sensitivities computed with correct sign and magnitude (−4 and −2), and the update SUBTRACTS learning_rate × sensitivity (so both weights increase).
- New loss recomputed and shown to decrease (here, all the way to 0).
- Reflection correctly explains that w1 moved more because its input x1 is larger, so the loss is more sensitive to it — gradient magnitude = influence.
- Worked from memory of the method first; the formula sheet consulted only to verify.

</details>

## Teach-back

Your stakeholder asks: 'Training GPU bills are enormous — what is the computer actually DOING all those hours?' Give the 2-minute answer: the loss number, the downhill steps, why it takes millions of repetitions, and where backprop fits — using one sustained analogy of your choosing (hiker, blame ledger, anything) without ever saying 'derivative' or 'calculus.' End with one sentence on what the learning rate is, since they'll see it in every vendor doc.

## Sources

- [3Blue1Brown — 'Gradient descent, how neural networks learn' (chapter 2)](https://www.3blue1brown.com/lessons/gradient-descent) (21 min video). The definitive visual treatment of the cost function and downhill-stepping — the landscape animations make 13,002 dimensions feel navigable. You watched the first half in S3; now watch it all.
- [3Blue1Brown — 'What is backpropagation really doing?' (chapter 3)](https://www.3blue1brown.com/lessons/backpropagation) (14 min video). The intuitive backprop chapter: blame flowing backward, the role of activation magnitudes, and mini-batch SGD — exactly the level this session targets, from the primary visual source rather than a secondhand explainer.
- [3Blue1Brown — 'Backpropagation calculus' (chapter 4)](https://www.3blue1brown.com/lessons/backpropagation-calculus) (10 min video (stretch goal)). The chain-rule mechanics on a tiny network. Optional-but-recommended stretch: watch once without pausing just to see that the 'blame ledger' story IS the chain rule — you are not required to reproduce the notation.

Link status is in [SOURCES.md](../SOURCES.md).
