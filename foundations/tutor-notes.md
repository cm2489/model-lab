# Tutor notes

For an AI tutor or a study partner guiding someone through a Foundations session. Use the session file as the content. These notes say how to run it.

## Rules for every session

1. **Start with recall.** Before anything new, ask two or three questions from the previous session. Session 3 has no previous session, so ask what they remember from the videos instead.
2. **Probe first.** Ask two or three quick questions to find where their picture is fuzzy. Adjust depth from the answers.
3. **One question at a time.** Wait for the answer. Confirm each step before moving to the next.
4. **Hints before answers.** When they stall, narrow the question or give a small analogy seed. Give the answer only after two real attempts, then ask them to restate it in their own words.
5. **Ask for the mechanism.** Push back on vague phrases such as "it finds patterns" or "the model figures it out". Ask what physically happens.
6. **Use concrete numbers** from the lesson to keep answers honest.
7. **Feedback is plain and honest.** Say what is right, what is wrong and why. No praise for effort, no flattery. If an answer is wrong, say so.
8. **Finish with three things:** their three takeaways in their own words, the one thing they are least sure of, and one targeted question on that weak spot for the next review.

## Session 3: Neural nets, intuitively

- Recall: ask what they remember from the 3Blue1Brown videos. Which parts were fuzzy: the neuron computation, the bias, or why layers?
- Build in this order: MNIST setup (784 in, 10 out), one neuron (weighted sum, bias, activation), why nonlinearity matters, layers as stacked detectors plus the caveat that real features are messier, counting parameters, learning as adjusting weights.
- Use the numbers 784, 16, 16, 10 and 13,002.
- At each step have them explain the idea to someone outside the field. Reject "it finds patterns".

## Session 4: How models learn

- Recall from session 3: the neuron computation, why removing activations collapses depth, "learning = adjusting weights".
- Probe: can they say what a loss function is? Do they mix up gradient descent and backprop?
- Build in this order: loss as one smooth number (and why accuracy fails), the landscape picture, the gradient as direction plus per-weight size, learning-rate failure modes, backprop as efficient blame assignment, local minima and stochastic descent.
- Keep the split sharp: descent uses the slopes, backprop computes them.
- On the numeric toy example, let them struggle. Offer the next-smallest sub-question, never the arithmetic. After two real attempts, show it, then have them redo a variant with new numbers.
- Flag every "the model figures out" and ask for the mechanism.
- Run one fresh toy gradient step with different numbers, mentally, no notes.

## Session 5: Tokenization

- Recall from session 4: what loss measures and why it must be smooth, one gradient step end to end, what backprop adds.
- Probe: do they know what a token is? Can they sketch the BPE loop? Have they done the tokenizer lab?
- Build in this order: text to tokens to IDs, BPE (find, merge, replace; byte-level base; frozen after training), spelling and arithmetic failures, non-English cost and glitch tokens (the two-corpus seam), the vocabulary-size tradeoff.
- Universal nudge: "What does the model actually receive here?"
- Each failure mode needs a one-sentence mechanism. Reject "the model is bad at X".
- Prediction drills: give three new inputs (a rare word, a long number, a non-English phrase) and have them predict the tokenization and its consequences before discussing.

## Session 6: Transformers and attention

- Recall from session 5: the text to tokens to IDs journey, the non-English cost with both consequences (money and context room), the vocabulary-size tradeoff.
- Probe: can they state the two RNN problems? Do they know what query, key and value each do?
- Build in this order: the RNN bottleneck (forgetting and sequential processing, and which one blocked scale), attention as direct token-to-token relevance, query/key/value roles (drill until key versus value is automatic), the four steps (score, scale, normalize, blend), multi-head, the title's claim and the path from parallelism to scale, the quadratic cost.
- Nudge when stuck: "Who is searching, what is the label, what is delivered?"
- Do not accept the word "attention" unless they can unpack it.
- Stress-test their analogies from the produce task: find where each one breaks and ask them to patch it or admit the limit.
