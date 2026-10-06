# Session 3: Neural nets, intuitively

**Time:** about 120 minutes (the original estimate, not measured here).  
**Core question:** What is a neural network actually computing when it recognizes a handwritten digit?

**Aim:** Explain, unaided, what a single neuron computes and why stacking layers of them can turn 784 pixel values into a digit guess.

**How to use this page:** read each block, then answer its check question before you open the hint and answer. Everything marked "details" is closed on purpose. Try first.

## Lesson

### 1. The problem: 784 numbers in, one digit out

#### The task

Start with the task 3Blue1Brown builds the whole series around: recognizing handwritten digits, using the classic MNIST dataset. Each image is a 28×28 grid of pixels — 784 pixels total — and each pixel is just a brightness number (think 0 for black through 1 for white). So an image of a sloppy handwritten '3' is, to a computer, nothing but a list of 784 numbers. The job: map those 784 numbers to one of ten labels, 0 through 9.

#### Why rules fail

Here's why this is a genuinely hard problem and not a toy. Try to imagine writing the rules by hand. 'A 3 has two bumps on the right' — okay, but where exactly? At which pixels? People write 3s slanted, cramped, with flat tops, shifted left, half the size. Any rule you write in terms of specific pixels ('pixel 412 should be bright') shatters the moment the digit shifts two pixels sideways. Decades of attempts at hand-coded rules for vision problems like this went nowhere. The space of valid 3s is too messy to enumerate.

#### What the brain does

Meanwhile your brain does this instantly, effortlessly, across absurd variations. The promise of a neural network is: instead of US writing the rules, we build a flexible machine with millions of adjustable dials and let *the data* set the dials so the right rules emerge. This session is about what that machine looks like; the next session (S4) is about how the dials get set.

Hold onto the framing: a neural network is just a function. 784 numbers go in, 10 numbers come out, and everything in between is arithmetic.

**Check:** Why is a hand-written if/else program ('if these pixels are bright, it's a 7') doomed for MNIST, in one sentence?

<details>
<summary>Hint and answer</summary>

**Hint:** Think about what happens to your rule if the same digit is drawn two pixels to the left.

**Answer:** Because valid 7s vary endlessly in position, slant, thickness, and style, so any rule pinned to specific pixels breaks under tiny shifts — the category is too variable to capture with enumerable pixel-level rules.

</details>

### 2. One neuron: weighted sum, bias, squash

#### The neuron

The basic unit is almost insultingly simple. A neuron takes a set of input numbers, computes a **weighted sum** of them, adds a constant called a **bias**, and passes the result through an **activation function** that reshapes it. Output: one number, its 'activation.'

#### Weights, bias, activation

Unpack each piece. The **weights** are the neuron's opinion about its inputs: a large positive weight means 'I care a lot about this input being bright,' a negative weight means 'this input being bright counts against me,' near-zero means 'irrelevant.' The pattern of weights IS the pattern the neuron is looking for — you can literally visualize a first-layer neuron's weights as a 28×28 image showing which pixels excite it and which suppress it. The **bias** sets the threshold: adding a bias of −10 means the weighted evidence has to clear a high bar before the neuron activates meaningfully. The **activation function** introduces a crucial nonlinearity. In the 3Blue1Brown intro it's the sigmoid, which squashes any number into the range 0 to 1 — very negative inputs land near 0, very positive near 1. (He notes modern networks mostly use ReLU — output zero below zero, identity above — because it trains more easily. Same role: bend the line.)

#### Why the squash matters

Why is the squash crucial and not decoration? Because without it, stacking layers is pointless: a weighted sum of weighted sums is still just one big weighted sum, so a deep linear network collapses into a single linear function — incapable of the messy, curvy distinctions real categories need. The nonlinearity is what makes depth mean something.

One neuron, then: a tiny pattern detector. Everything else is organization.

**Check:** Design (in words) the weights and bias for a neuron that fires strongly only when the top row of the image is bright AND the rest is dark.

<details>
<summary>Hint and answer</summary>

**Hint:** Three levers: which pixels get positive weights, which get negative, and what the bias must do to scattered noise.

**Answer:** Positive weights on the 28 top-row pixels, negative (or strongly negative) weights on the remaining 756 pixels, and a negative bias large enough that scattered brightness elsewhere can't clear the threshold — so only the specific top-bright/rest-dark pattern pushes the weighted sum high before the squash.

</details>

### 3. Layers: banks of pattern detectors, stacked

#### Layers

Now organize neurons into **layers**. A layer is a bank of neurons that all read the same inputs — namely, every activation from the previous layer — but each with its own weights and bias, so each detects a different pattern. The 3Blue1Brown network is: 784 input neurons (one per pixel, their activations just ARE the brightness values), two hidden layers of 16 neurons each, and 10 output neurons, one per digit. After an image flows through, the output neuron with the highest activation is the network's answer.

#### Why stack layers

Why stack layers at all? The hope is a hierarchy of abstraction. First hidden layer: neurons that detect small local patterns — little edges and patches of stroke. Second hidden layer: neurons that combine edges into larger parts — a loop in the upper half, a long vertical line. Output layer: neurons that combine parts into digits — 'loop on top plus vertical line below it' is most of a 9; 'two stacked loops' is an 8. Each layer asks questions about the answers of the layer before, so questions get more abstract as you go deeper. This composition is the deep-learning idea in miniature: hard concepts built from easier ones.

#### The caveat

Now the honest caveat, which 3Blue1Brown is careful about and you should be too: when you inspect a real *trained* network, the hidden neurons usually don't correspond to clean human-nameable features like 'loop detector.' The learned patterns are messier, distributed, and only loosely interpretable. The edges-to-loops-to-digits story is the right *intuition* for why depth helps — it is not a literal description of what training finds. Keeping both the intuition and the caveat is what separates someone who understands this from someone who read about it.

**Check:** Using the hierarchy story, explain how a second-hidden-layer neuron could help recognize a 9 — then state the caveat you must attach.

<details>
<summary>Hint and answer</summary>

**Hint:** What does each layer take as ITS inputs? Build the 9 from parts, then remember what inspection of real trained nets shows.

**Answer:** It could activate when first-layer edge detectors jointly signal 'loop in the upper region' — and an output neuron combining that with 'vertical stroke below' scores 9 highly. Caveat: that's the idealized story; real trained networks usually learn messier, less interpretable features, so treat it as intuition for why depth helps, not a literal mechanism.

</details>

### 4. Counting the knobs: 13,002

Let's make 'the network has adjustable dials' concrete by counting them in the 784→16→16→10 network.

#### Counting weights and biases

Every connection between a neuron and each neuron in the previous layer carries one weight. First hidden layer: 16 neurons each connected to all 784 inputs → 784 × 16 = 12,544 weights. Second hidden layer: 16 × 16 = 256 weights. Output layer: 16 × 10 = 160 weights. Then one bias per non-input neuron: 16 + 16 + 10 = 42 biases. Total: 12,544 + 256 + 160 + 42 = **13,002** parameters — for a network 3Blue1Brown describes as small and old-fashioned. Frontier language models have billions of parameters, but they are the same kind of object: a big pile of weights and biases defining a function.

#### What the count tells you

Two things this count should recalibrate. First, where the bulk lives: over 96% of this network's parameters sit in the first layer, because connecting everything to 784 inputs is expensive. The shape of a network determines where its capacity is spent. Second — and this is the conceptual payoff — **'learning' means nothing more than finding good values for these 13,002 numbers.** When someone says a model 'learned' something, they mean: somewhere in its parameters, values were adjusted so the function maps inputs to better outputs. There is no other place for knowledge to live. No rules are written anywhere; there is only the setting of the dials.

That reframing makes the next session's question urgent and precise: by what procedure do you find a good setting of 13,002 (or 13 billion) numbers? You can't try combinations — the space is unimaginably vast. You need something cleverer.

**Check:** Your colleague says 'the network stores a rule like: two stacked loops means 8.' Correct them precisely: where does that knowledge actually live?

<details>
<summary>Hint and answer</summary>

**Hint:** List everything that exists inside this network. It's a short list — where could a 'rule' possibly be written?

**Answer:** There's no stored rule — only 13,002 weights and biases. Whatever the network 'knows' about 8s is implicit in the numerical settings of those parameters, which make the function output a high 8-activation for two-loop inputs. The knowledge is the dial settings, nothing else.

</details>

### 5. Learning = adjusting weights (and what the network can't do)

Put the pieces together and preview the cliffhanger.

#### Random weights, garbage outputs

A freshly created network starts with **random** weights and biases. It still runs perfectly well — arithmetic doesn't care — but its outputs are garbage: feed it a clearly written 7 and the output activations are noise, maybe '3' brightest for no reason. Structure exists before knowledge. Training is the process of nudging all 13,002 dials, over and over, using a pile of labeled examples, until the function's outputs match the labels. To do that you need two things: a way to *measure* how wrong the current dial settings are (one number, the 'cost' or 'loss'), and a procedure that tells you *which way to nudge each dial* to make that number smaller. Those two things — loss and gradient descent with backpropagation — are all of Session S4. For now, hold the clean summary: **learning = adjusting weights to reduce measured wrongness.**

#### What the network is not

And note what this network is NOT. It has no notion of 'not a digit': feed it a photo of a cat scaled to 28×28 and it will confidently activate some digit output, because all it can do is map 784 numbers to 10 scores. It doesn't 'see' in any rich sense; it doesn't know what a 3 *means*; it computes one fixed function, brilliantly fitted. Keeping the deflationary view — it's arithmetic with well-chosen constants — is what will let you reason clearly later about much grander systems, which are this same object at staggering scale. When a colleague anthropomorphizes a model, your mental model should quietly translate back to: a function, with dials, set by data.

**Check:** You feed the trained MNIST network a 28×28 photo of a cat. What happens, and what does that reveal about what the network fundamentally is?

<details>
<summary>Hint and answer</summary>

**Hint:** The network can't refuse input. Trace what it MUST do with any 784 numbers, then ask what that implies.

**Answer:** It computes as usual and confidently lights up some digit output — it has no 'none of the above.' This reveals it's a fixed function from 784 numbers to 10 scores: it can only answer the question its shape allows, with no understanding beyond its fitted arithmetic.

</details>

## Quiz

**1. A first-hidden-layer neuron has strong positive weights on pixels tracing a short horizontal stroke near the image center and negative weights immediately around them. What is this neuron doing?**

- A. Storing the digit '1' for later comparison
- B. Acting as a detector that activates when that horizontal stroke pattern is present and its surroundings are dark
- C. Averaging the brightness of the whole image
- D. Counting how many bright pixels the image contains

<details>
<summary>Answer and explanation</summary>

**Correct: B.** Acting as a detector that activates when that horizontal stroke pattern is present and its surroundings are dark

A neuron's weight pattern IS its target pattern: positive weights reward brightness where the stroke should be, negative weights punish brightness around it, so the weighted sum (and activation) is high exactly when that local feature is present.

</details>

**2. In the trained 784→16→16→10 network, the output neuron for '4' shows the highest activation for an input image. What's the correct interpretation?**

- A. The network has verified the image satisfies the definition of a 4
- B. The image is definitely a 4 with probability equal to that activation
- C. Of the ten output scores this function computed, '4' scored highest, so 4 is the network's best guess — which can still be wrong
- D. The network compared the image against stored template images of each digit

<details>
<summary>Answer and explanation</summary>

**Correct: C.** Of the ten output scores this function computed, '4' scored highest, so 4 is the network's best guess — which can still be wrong

The network is a function producing 10 scores; the answer is just the argmax. There's no verification, no stored templates, and raw activations aren't calibrated probabilities. Best-guess-can-be-wrong is the right stakeholder framing too.

</details>

**3. You strip every activation function out of a 10-layer network, leaving only weighted sums and biases. What can the resulting network learn?**

- A. The same things, just trained more slowly
- B. Only relationships expressible as a single linear function — the 10 layers collapse into the equivalent of one
- C. Nothing at all; it can no longer produce outputs
- D. Only binary classifications instead of 10-way ones

<details>
<summary>Answer and explanation</summary>

**Correct: B.** Only relationships expressible as a single linear function — the 10 layers collapse into the equivalent of one

A composition of linear maps is linear: weighted sums of weighted sums reduce to one weighted sum. Depth becomes decorative. The nonlinearity at each layer is precisely what makes stacking layers add expressive power.

</details>

**4. A freshly initialized (untrained) network confidently labels a clean '7' as a '3'. What's the right diagnosis?**

- A. The architecture is wrong for digit recognition
- B. The image needs preprocessing before the network can read it
- C. Nothing is broken: with random weights the function computes fluently but arbitrarily — structure exists before knowledge
- D. The activation functions are saturating and need replacement

<details>
<summary>Answer and explanation</summary>

**Correct: C.** Nothing is broken: with random weights the function computes fluently but arbitrarily — structure exists before knowledge

Random dials produce garbage outputs through perfectly functional arithmetic. The fix isn't architectural — it's training: adjusting the weights using labeled data until outputs match labels. This is the cliffhanger S4 resolves.

</details>

**5. In the 784→16→16→10 network, where do the overwhelming majority of the 13,002 parameters live, and why?**

- A. The output layer, because final decisions need the most capacity
- B. Spread evenly, since every layer has the same number of neurons
- C. The first hidden layer's weights (784 × 16 = 12,544), because every one of its 16 neurons connects to all 784 inputs
- D. The biases, which outnumber the weights

<details>
<summary>Answer and explanation</summary>

**Correct: C.** The first hidden layer's weights (784 × 16 = 12,544), because every one of its 16 neurons connects to all 784 inputs

Fully connecting to a 784-dimensional input is expensive: 12,544 of 13,002 parameters (~96%) sit in that first block. Architecture shape dictates where capacity is spent — a useful instinct when reasoning about much bigger models.

</details>

**6. You want a neuron to stay quiet unless its weighted evidence sum exceeds roughly 10. Which dial implements this, and how?**

- A. Set the bias to about −10, so the sum must beat 10 before the pre-activation goes positive
- B. Set all weights to 10
- C. Use a steeper activation function
- D. Add ten more inputs to the neuron

<details>
<summary>Answer and explanation</summary>

**Correct: A.** Set the bias to about −10, so the sum must beat 10 before the pre-activation goes positive

The bias shifts the activation threshold: with bias −10, weighted evidence below 10 leaves the pre-activation negative (squashed near zero by sigmoid, or exactly zero under ReLU). That's the bias's whole job — setting how much evidence 'counts as enough.'

</details>

## Produce task

Write an explainer note in your notes: 'What a neural network computes' — covering the neuron equation (weighted sum + bias + activation, in words), why nonlinearity is non-negotiable, the layer hierarchy story WITH its caveat, and the sentence 'learning = adjusting weights to reduce measured wrongness.' Then hand-draw (paper or tablet) a small 3-layer network — e.g. 4 inputs → 3 hidden → 2 outputs — labeling: at least three weights on connections, one bias, one activation value, and an arrow showing the direction information flows. Photograph it into your notes.

**What to hand in:** One explainer note + one hand-drawn labeled diagram embedded in your notes.

**Success criteria:**

- The neuron computation is stated correctly: weighted sum of inputs, plus bias, through an activation function.
- The note explains why removing activations collapses the network into one linear function.
- The hierarchy story (edges → parts → digits) appears WITH the caveat that real trained features are messier.
- The diagram labels weights on connections (not on neurons), and distinguishes weights from activations.
- Drawn from memory first; sources checked only afterwards for corrections (note any corrections made).

## Teach-back

A prospective client asks: 'Everyone says models learn. What is actually changing inside the machine when it learns?' Give the 2-minute plain-language answer using the MNIST network: the function framing, the dials, and what learning does to them — no equations, no jargon left undefined, and end by naming one thing the model still can't do so the client's expectations stay calibrated.

## Sources

- [3Blue1Brown — 'But what is a neural network?' (Neural networks, chapter 1)](https://www.3blue1brown.com/lessons/neural-networks) (19 min video). Grant Sanderson's series is the canonical visual treatment — the MNIST network, neurons, weights, biases, and layers, animated with real care for correctness. Watch before or after reading this session's blocks; the visuals will lock in the structure.
- [3Blue1Brown — 'Gradient descent, how neural networks learn' (chapter 2)](https://www.3blue1brown.com/lessons/gradient-descent) (21 min video (first half now, rewatch in S4)). Same source, second chapter. Watch the first half for this session (the cost-function setup and 'learning = finding weights'); the gradient-descent core returns as required viewing in S4, so this doubles as spaced exposure.

Link status is in [SOURCES.md](../SOURCES.md).
