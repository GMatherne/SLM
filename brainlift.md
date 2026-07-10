# Brainlift - SLM

## Owners
Grant Matherne



## Purpose
**Description:** Understanding how LLMs internalize and produce specific stylistic artifacts ("AI-isms" like em dash overuse) and how to mitigate them by fine-tuning small open-source models with high-quality datasets.
**In Scope:** Stylistic fingerprints (em dashes, vocabulary, structural tells), fine-tuning methodology (Unsloth, QLoRA), dataset generation for controlling tone and style.
**Out of Scope:** Evaluating the raw capabilities of frontier models, training models from scratch, generalized prompt engineering tips.



## Experts
**E. M. Freeburg**
- **Main Views:** Em dash overuse is a markdown formatting artifact leaking into prose. The rate of its use is a signature of post-training decisions.
- **Why Follow:** Author of "The Last Fingerprint," providing the mechanistic account of this phenomenon backed by empirical experiments.
- **Locations:** `hqops@icloud.com` / Independent Researcher (arXiv)

**Dan Shipper (Unscarcity)**
- **Main Views:** AI slop has distinct, measurable structural patterns that act as fingerprints, and removing them requires human-governed audits to restore voice.
- **Why Follow:** Catalogued the "Field Guide to AI Slop" and defined empirical rules for detecting and scrubbing it.
- **Locations:** unscarcity.ai, X (@danshipper)

**Daniel & Michael Han (Unsloth)**
- **Main Views:** Standard full-weight fine-tuning is inefficient; hand-optimized Triton kernels can radically reduce VRAM and increase speed for QLoRA fine-tuning without losing accuracy.
- **Why Follow:** Creators of Unsloth, the fastest and most efficient framework for fine-tuning open-source LLMs on consumer hardware.
- **Locations:** unsloth.ai, X (@UnslothAI)

**Grant Sanderson (3Blue1Brown)**
- **Main Views:** Complex deep learning operations (like backpropagation and attention blocks) can be understood intuitively through visual geometric representations of linear algebra and calculus.
- **Why Follow:** Exceptional ability to break down the core mechanics of neural networks and transformer architectures into accessible, foundational truths.
- **Locations:** YouTube (3Blue1Brown), X (@3blue1brown)






## DOK 2 - Knowledge Tree

### 1. AI Writing
#### 1.1 Em Dashes Use by LLMs
**Source:** https://arxiv.org/html/2603.27006

**DOK 1 - Facts**
- Models "overuse" em dashes —> a result of markdown formatting, not a distinct stylistic choice
- LLM training data is saturated with markdown:
   - The Pile (800GB training dataset) includes GitHub and Stack Exchange
   - Highest-quality text on the open web (developer docs, technical writing) is overwhelmingly markdown
- RLHF (Reinforcement Learning from Human Feedback) amplifies the "markdown register" —> evaluators (disproportionately technical workers) reward structured, clear prose
- The 5-Step Em Dash Genealogy:
   1. Training Data Saturation
   2. Structural Internalization —> models learn that dashes signal boundaries between units of meaning
   3. The Dash as Structural Joint —> em dash (U+2014) is not a markdown element, but it is the only dash family member that is valid prose punctuation —> becomes the narrowest channel for the structural impulse to leak into prose
   4. RLHF Amplification —> evaluators like em-dash-heavy prose because it reads as precise and structurally aware —> Sam Altman publicly acknowledged adjusting ChatGPT's em dash frequency based on user preference
   5. Complementarity —> training data explains why the em dash was available to be selected; RLHF explains that it was selected
- Study 1 (markdown suppression) —> 12 instruction-tuned models across 5 providers (~240,000 words total):
   - Prose-constrained instruction ("no markdown formatting...") eliminated overt markdown features in almost all models
   - GPT-4.1 only dropped 14% (10.62 to 9.10 em dashes / 1,000 words) under suppression
   - Claude Opus 4.6 dropped 98% (9.09 to 0.19)
   - Llama 3.1 8B Instruct and 3.3 70B Instruct produced 0.00 em dashes unconstrained and constrained
   - GPT-5.4 produces 1.43 unconstrained and 0.29 constrained
   - Human baseline for em dashes —> 3.23 per 1,000 words (mean across 8 published essays)
- Study 2 (explicit prohibition) —> added instruction "Do not use em dashes":
   - GPT-4.1 retained 3.86 / 1K even under direct prohibition —> the structural impulse overrides explicit instructions
- Study 3 (Base vs Instruct):
   - Llama 3.1 8B Base model produced 0.49 / 1K em dashes and 28 markdown features —> proves the latent tendency exists pre-RLHF
   - Llama 3.1 8B Instruct model produced 0.00 em dashes and 5 markdown features
- Em dash pattern functions as a signature of the post-training process —> could be used for model attribution

**DOK 2 - Summary and Analysis**
The excessive use of em dashes by language models is a "markdown artifact." Because high-quality training data (like GitHub) is saturated in markdown, models internalize dashes as structural boundaries separating units of meaning. When prompted to write prose and avoid formatting, overt markdown gets successfully suppressed. The em dash persists because it occupies a dual-register—it is valid prose punctuation but carries the structural impulse of a markdown dash. RLHF amplifies this trait because evaluators reward the structured, articulate tone that em-dash-heavy text projects.

The rate of em dash usage and its resistance to suppression varies wildly by model (e.g., highly prevalent in OpenAI models but completely scrubbed in Meta's Llama models). Therefore, the em dash functions as a unique fingerprint of a provider's specific post-training fine-tuning decisions.

*(Note on alternative hypotheses raised by the source: explanations such as em dashes peaking in 19th-century literature training data, or simply acting as a "prestige marker" to evaluators, are compatible with this theory but fail on their own to explain why the em dash specifically resists structural formatting suppression while other punctuation does not.)*



### 1.2 GPT-isms and Linguistic Fingerprints
**Source:** https://unscarcity.ai/a/gpt-isms

**DOK 1 - Facts**
- GPT-isms —> recurring stylistic fingerprints LLMs leave in generated text, caused by training data heavily weighting high-engagement text (TED talks, business books) so models mimic their shape
- Parallelism ("It's not X. It's Y.") —> mimics an epiphany
- The em dash epidemic —> multiple em dashes per paragraph creating a breathless, parenthetical cadence
- Filler intensifiers ("remarkably", "crucially", "fundamentally") —> pads sentences without adding meaning
- Vapid openers ("Here's the thing:", "Let's be clear") —> throat-clearing before the actual point
- Unearned profundity ("This isn't just a product launch. It's a paradigm shift.")
- Triadic lists —> grouping in threes even when there are only two things and the third is filler
- The italic function word —> LLMs italicize words like *and*, *is*, *that*, *for* 
- The contraction deficit —> defaulting to formal register ("do not" instead of "don't") making prose stiff
- Generic analogies —> "Like a symphony" (connects nothing, just decoration)
- Cross-reference over-explanation —> hedging by re-explaining previously defined concepts at every mention
- Governance solution —> use AI agents as mechanical detectors to find the patterns, but a human must judge what to keep or fix

**DOK 2 - Summary and Analysis**
These artifacts aren't bugs; they are the statistical shape of "good writing" in the training data, hollowed out of its substance. The model mimics the cadence of profundity, persuasion, and clarity (like antithesis or triadic lists) without the actual human judgment needed to apply them correctly. Since humans inherently tune out text that feels like the "average of all writing," detecting and removing these tics through a governed human-in-the-loop audit is necessary to restore actual voice.



### 1.3 The AI Slop Cleanup Guide
**Source:** https://unscarcity.ai/static/docs/ai-slop-cleanup-guide.md

**DOK 1 - Facts**
- Slop —> generated content that nobody asked for, nobody reviewed, and nobody wants
- Word-level Tells (AI frequency spikes vs human baselines):
   - delve: 25x
   - tapestry: 10x
   - commendable: 9.4x in peer reviews
   - meticulous: 7.4x in peer reviews
   - intricate: 4.5x
- Transition density test —> >2 transitions like "Moreover", "Furthermore", "Additionally" per 250 words = AI fingerprint
- Formatting tells:
   - Italic function words (*and*, *is*, *that*, *for*, *it*) —> the single most reliable AI detector
   - Bold overuse —> if >5% of text is bold
   - Emoji distribution —> one per header, evenly spaced (rocket, lightbulb, checkmark)
- Structural tells:
   - Listicle compulsion —> nested lists everywhere instead of prose
   - Symmetric section lengths (Five-paragraph essay format)
   - Conclusions that restate the introduction
- Model-specific tells:
   - ChatGPT (GPT-4/4o) —> confident, heavy on "delve", "[Topic]. Here's why:"
   - Claude —> heavy hedging, em-dash usage, "That said,", discursive paragraphs
   - Gemini —> verbose, "Key takeaways", "It's important to remember that"
   - Open-Source (Llama, Mistral) —> repetitive, circular arguments, weaker transitions
- 4-Tier Fix Methodology:
   1. Mechanical Fixes —> search-and-replace (e.g., removing italic function words)
   2. Judgment fixes —> parallelism, blacklist words
   3. Rewrite required —> lack of specificity, symmetric structure
   4. Leave alone —> bold coined terms, genuine triads

**DOK 2 - Summary and Analysis**
AI text fails to emulate human writing because it lacks negative space, asymmetry, and intellectual courage. It avoids taking polarizing stances, maintains a relentlessly positive-neutral emotional flatness, and symmetrically balances its structure (e.g., every bullet point is the same length). Curing a document of AI slop isn't just about replacing "delve" with "explore"; it requires breaking the model's structural templates, introducing shifts in register, deleting summaries that don't advance the argument, and injecting the messy specificity of a real human perspective.






## 2. Fine-tuning Methodologies
### 2.1 QLoRA Fine-Tuning with Unsloth
**Source:** https://www.stack-junkie.com/blog/lora-fine-tuning-consumer-gpu

**DOK 1 - Facts**
- LoRA (Low-Rank Adaptation) —> trains two small adapter matrices instead of updating all base model weights, computing weight change as delta_W = A × B
- Rank (r) —> the inner dimension of LoRA matrices (typically 8 to 64); a rank of 16 trains roughly 1% of the parameters a full fine-tune would touch
- QLoRA —> adds 4-bit quantization of the base model via NF4 (4-bit NormalFloat), cutting VRAM requirements by 75% compared to standard 16-bit LoRA
- Paged optimizers —> technique introduced in QLoRA that moves optimizer state to CPU when GPU memory spikes, preventing OOM crashes
- Hardware requirements —> QLoRA makes fine-tuning a 7B model fit in 8-10GB of VRAM (runs on RTX 3060/3080/4090); 13B fits comfortably on 24GB VRAM
- Unsloth framework —> rewrites PyTorch's backpropagation steps into hand-optimized Triton kernels —> achieves 2x faster training and 70% less VRAM usage than HuggingFace baseline with no accuracy degradation
- Dataset constraints for tone/style —> 200-500 high-quality examples is sufficient for formatting/tone changes; 1,000-3,000 for domain adaptation; 5,000+ for knowledge injection
- LoRA solves: output format consistency, tone/persona, domain vocabulary, instruction-following patterns
- LoRA struggles with: injecting new factual knowledge or fixing fundamental reasoning gaps (needs RAG instead)
- Catastrophic forgetting —> fine-tuned models can lose general capabilities if trained too aggressively on a narrow dataset (fix: mix in general examples)
- Overfitting —> training loss drops to near zero and model produces near-exact copies of training examples (fix: reduce epochs, Unsloth recommends max 3, often 1 is enough)

**DOK 2 - Summary and Analysis**
Standard full-weight fine-tuning is too computationally expensive for consumer hardware. QLoRA solves this by combining 4-bit base model quantization (NF4) with Low-Rank Adaptation (LoRA), which only trains small, newly injected adapter matrices rather than the whole model. Using the Unsloth framework optimizes this further via custom Triton kernels, drastically cutting VRAM and time requirements. For stylistic or formatting changes—like removing AI-isms—the dataset size does not need to be massive; 200-500 high-quality, formatted examples are enough to reliably shift the model's behavior and tone. However, while LoRA excels at behavior and format consistency, it cannot fix fundamental reasoning gaps or effectively inject new factual knowledge, which should be handled by RAG instead.



### 2.2 Formatting Datasets for Unsloth
**Source:** https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/datasets-guide

**DOK 1 - Facts**
- To be useful for training, datasets must be in a format that can be tokenized
- Common LLM Data Formats:
   - Raw Corpus —> raw text from sources like books or articles (used for Continued Pretraining / CPT)
   - Instruct (Alpaca style) —> consists of "Instruction", "Input" (optional), and "Output" (used for Supervised Fine-Tuning / SFT)
   - Conversation (ShareGPT or ChatML) —> multiple-turn dialogue alternating between human/gpt or user/assistant (used for SFT)
   - RLHF —> conversations where the assistant's responses are ranked by a script, model, or human
- ChatML Format —> the most used format (and Hugging Face's default), which alternates between `user` and `assistant` roles
- ShareGPT Format —> uses `from` and `value` keys; alternates between `human` and `gpt`
- `to_sharegpt` function —> provided by Unsloth to merge multiple columns of a CSV/Excel file into a single prompt automatically
- `standardize_sharegpt` —> Unsloth function to convert ShareGPT format datasets into ChatML format (if required by the model)
- `conversation_extension` parameter —> allows selecting multiple random single-turn rows and merging them into one multi-turn conversation
- Dataset size recommendations:
   - Bare minimum: 100 rows
   - Optimal performance: 1,000+ rows
- Synthetic Data Generation:
   - Used to produce entirely new data, diversify the dataset (prevent overfitting), or automatically structure existing data into a chosen format
   - Recommended to use a larger local LLM (like Llama 3.3 70B) or GPT-4.5 for highest quality outputs
- Reasoning model fine-tuning:
   - If the model already has reasoning (e.g. DeepSeek-R1-Distill), the dataset answer must include the chain-of-thought process
   - If the model lacks reasoning but you want to train it to reason, you use a standard dataset (no reasoning in answers) via Reinforcement Learning and GRPO
- Multiple fine-tuning passes:
   - It is possible to fine-tune an already fine-tuned model, but it is better to combine datasets and do it in a single process to avoid altering previously acquired knowledge

**DOK 2 - Summary and Analysis**
Preparing a dataset for fine-tuning is primarily an exercise in structural formatting rather than writing complex code. Because models expect data to be presented as either single-turn instructions (Alpaca) or multi-turn dialogues (ShareGPT/ChatML), any raw tabular data must be "merged" into these conversational templates before tokenization. Unsloth abstracts much of this away with functions like `to_sharegpt` and `standardize_sharegpt`, which handle the conversion automatically. The focus for the dataset creator should therefore be entirely on the *quality* of the examples rather than the raw volume. While the bare minimum is 100 rows, a high-quality dataset of ~1,000 rows generated by a frontier model (like Llama 3.3 70B) is optimal for ensuring the target style is adopted without overfitting.



### 2.3 Fine-Tuning an LLM with QLoRA on a Single GPU
**Source:** https://pristren.com/blog/fine-tuning-llm-with-qlora/

**DOK 1 - Facts**
- QLoRA (Quantized Low-Rank Adaptation) —> makes fine-tuning 70B models accessible on a single consumer GPU by combining 4-bit quantization (reducing memory footprint 4x) and LoRA
- VRAM requirements:
   - Llama 3 8B fine-tunes on a single RTX 4090 (24GB VRAM)
   - Llama 3 70B fine-tunes on a single A100 80GB
- Use cases for fine-tuning —> effective for changing how a model behaves (style, format, persona, domain focus, or structured task output like JSON/SQL)
- Use cases against fine-tuning —> not for injecting new factual knowledge (RAG should be used instead)
- Dataset size rules:
   - 500-5,000 high-quality examples is typically sufficient for behavioral fine-tuning
   - More is not always better —> 100 high-quality examples often outperform 10,000 low-quality ones
- Dataset generation —> generate the dataset from real examples of the exact behavior you want
- Unsloth advantages —> achieves 2-3x faster training and 50-60% less memory usage compared to standard HuggingFace PEFT training

**DOK 2 - Summary and Analysis**
The process of fine-tuning small, open-source language models has been entirely democratized by QLoRA and optimized by the Unsloth framework, meaning models as large as 8B or even 70B parameters can be trained locally on single GPUs. When attempting to cure a model of "AI-isms" or force a specific style/persona, the limiting factor is no longer compute power but dataset quality. Because behavioral fine-tuning requires the model to learn a specific pattern rather than a set of facts, raw volume is actively detrimental if the data is noisy. A heavily curated set of a few hundred pristine examples showcasing exactly how the model *should* write will outperform thousands of scraped, unedited rows.





## 3. Machine Learning Basics
### 3.1 What is a Neural Network
**Source:** https://www.youtube.com/watch?v=aircAruvnKk&list=PLZHQObOWTQDNU6R

**DOK 1 - Facts**
- Neuron —> thing that holds a number between 0 and 1 (activation value)
- For 28x28 black and white digit identification:
   - 784 neurons at first layer (each pixel)
   - Last layer has 10 neurons, where the activation is the confidence that it is that digit
- Layers in between called hidden layers
- Activations in one layer bring about activations in the next
- How do we want sequential layers to pick up on certain patterns? What parameters should we have? —> assign a weight to each connect from each neuron from first layer to second
- Sigmoid function keeps things from 0 to 1
- Can keep a score that is defined as the weighted sum of each neuron + some constant number (bias) before feeding it to sigmoid function
- Weighted sum is dot product of weight matrix * neuron vector + bias vector
- Think of each neuron as a function —> takes outputs of all neurons of previous layer and outputs a number between 0 and 1

**DOK 2 - Summary and Analysis**
A neural network breaks down complex identification tasks (like recognizing a handwritten digit) into a series of numerical activations. The input layer takes in raw pixel data (0 to 1), passes it through "hidden layers" via a series of weighted sums (dot products) bounded by a sigmoid function, until it outputs a set of final confidence values.



### 3.2 Gradient Descent (how neural networks learn)
**Source:** https://www.youtube.com/watch?v=IHZwWFHWa-w

**DOK 1 - Facts**
- Define a cost function —> add squares of differences between activations and the values you want; average cost is how shit your network is
- We want to minimize this, but using the derivative isn't always feasible (lots of parameters), so you pick a random input and take steps in each direction to see which minimizes the output (can use derivative to see which direction is better)
   - Making steps proportional to slope keeps you from overshooting
   - Local minimum —> easy
   - Global minimum —> hard
- Taking this to a function with 2 inputs and 1 output (3D), use the gradient to find the mins (length of gradient vector is indication for how steep the steepest slope is)
- Same idea for function with lots of inputs (many parameters)
- Organize all weights and biases into vector, negative gradient of cost function is a vector that tells you which changes to those numbers cause the most rapid decrease
- A network learning is just minimizing a cost function
- Repeatedly changing an input of a function by some multiple of the negative gradient is called gradient descent —> some way to converge towards some local minimum of some cost function

**DOK 2 - Summary and Analysis**
Neural networks "learn" by minimizing a cost function (how wrong the model's outputs are compared to the desired outputs). Because calculating exact derivatives across billions of parameters isn't practical, the network uses gradient descent—taking small, iterative steps in the direction of the steepest negative gradient—to converge on a local minimum, effectively finding the weights and biases that produce the least error.



### 3.3 Backpropagation
**Source:** https://www.youtube.com/watch?v=Ilg3gGewQ5U

**DOK 1 - Facts**
- Backpropagation is the algorithm for determining how a single example would like to change the weights and biases (computing gradient)
- Determines not only whether weights should go up or down, but also what relative proportions to those changes causes the most rapid decrease to the cost
- Want partial derivative of cost with respect to weight
- How much a change in the weight influences a layer depends on how strong the previous neuron is (weight * activation value)
- We have a desired endpoint for a specific input, so the idea of propagating backwards is changing the second to last layer based on the desired change in the last layer

**DOK 2 - Summary and Analysis**
While gradient descent describes the high-level goal of finding the minimum of a cost function, backpropagation is the actual algorithm used to compute that gradient. It works backward from the final output layer to the input, calculating how much each weight and bias contributed to the final error (the partial derivative) so they can be adjusted in the exact proportion that reduces the cost most efficiently.



### 3.4 Transformers (the tech behind LLMs)
**Source:** https://www.youtube.com/watch?v=wjZofJX0v4M

**DOK 1 - Facts**
- The original transformer introduced in 2017 by Google was invented for translating one language to another
- Input broken up into tokens
   - Text: generally words or pieces of words
   - Image: Group of pixels
   - Sound: Chunk of sound
- Each token is associated with a vector (list of numbers), which is meant to encode the meaning of that piece. Words with similar meanings land close to each other in that vector space
- That sequence of vectors then passes through an operation (called attention block) wherein they pass information to each other and update their values
- They then pass through a different operation (multi-layered perceptron / feed-forward layer) wherein they all go through the same operation in parallel (similar to asking questions about the vector and updating them based on the answers)
- These operations just look like a bunch of matrix multiplications
- There are also normalization steps that happen in between but we don't get to hear about that because this is a video for plebs
- The process repeats going from attention blocks to multi-layer perceptron blocks, at the end the hope is that the essential meaning is held in the last vector, which we then perform an operation on to get the probability distribution to get all possible tokens that come next
- To make a next word predictor into a chatbot, you roleplay and have it be a chatbot (system prompt), then use the prompt (requires extra training for it to be good)
- Deep learning:
   - One approach to machine learning wherein you use data to determine how a model behaves
   - Describe a class of models that have proven to scale well in the last few decades (it's not given that it is possible to train and doesn't overfit the training data)
   - Instead of creating code to explicitly do the task, you have tunable parameters and use examples of what the output should look like for a given input to tune them to mimic outputs on their own
   - For backpropagation training to work well at scale it has to follow a certain format: Input has to be formatted as an array (1D, 2D, tensor) of real numbers
- GPT-3 has 175,181,291,520 weights organized into 27,938 matrices in 8 groups
   1. Embedding
   2. Key
   3. Query
   4. Value
   5. Output
   6. Up-projection
   7. Down-projection
   8. Unembedding
- Model has predefined vocab (in example, one word corresponds to one token)
- Embedding matrix has a column for each word that determines what vector each word turns into in the first step (turning each word into vector is called embedding)
- Vector direction can carry semantic meaning —> difference between man and woman is similar to difference between uncle and aunt. Hitler + Italy - Germany = Mussolini. Cats - Cat = plurality
- Dot product shows how well embeddings align
- Meaning of words depends on context, so the embedding matrix has vector meaning of word without input from surroundings (later stages do this, processing words at a fixed number of vectors —> context size)
- At the very end, an unembedding matrix maps the last vector in that context to a vector of the vocab length
- Values will not look like probability distributions at the end —> softmax is the standard way to turn an arbitrary list of numbers into a valid distribution such that the largest values end up close to 1 and the smallest values end up close to 0
   - $\mathrm{softmax}(\mathbf{x})_i = \dfrac{e^{x_i/T}}{\sum_j e^{x_j/T}}$ where $x_n$ is nth number in vector, $T$ is temperature
   - Temperature of 0 means it always chooses most likely word, high temperature increases randomness at the risk of it being nonsensical
   - Inputs are logits, outputs are probabilities

**DOK 2 - Summary and Analysis**
The transformer architecture revolutionized deep learning by processing entire sequences of tokens in parallel rather than sequentially. It maps inputs (text, images) into a high-dimensional vector space where direction implies semantic meaning, then repeatedly passes them through "attention blocks" (which allow tokens to pass context to each other) and "feed-forward layers" (which process the updated meaning). By the final layer, the accumulated context is "unembedded" into raw logits, and a softmax function (modulated by a temperature parameter) converts those logits into a probability distribution predicting the next token.





### 4. Pangram AI Detection Methodology
#### 4.1 Core Technology and Approach
**Source:** https://www.pangram.com/research/how-it-works

**DOK 1 - Facts**
- Pangram Text uses a traditional language model architecture
- Input is passed through a neural network, producing an output embedding
- A classifier head transforms the output embedding into a 0 or 1 prediction (0 -> human, 1 -> AI)
- Designed to detect AI-generated content with a near-zero false positive rate
- Analyzes and understands subtle cues in the writing

**DOK 2 - Summary and Analysis**
Pangram employs a neural network architecture that tokenizes input text and converts tokens into embeddings. These embeddings are then processed by the network and a classifier to predict whether the text is human or AI-generated, aiming for a very low false positive rate by focusing on subtle writing cues.



#### 4.2 Training and Data
Source: https://www.pangram.com/research/how-it-works

**DOK 1 - Facts**
- Initial model trained on diverse human dataset (1 million documents)
- Dataset also includes AI-generated text produced by GPT-4 and other frontier language models
- Training results in a neural network capable of reliably predicting human or AI authorship
- Developed an algorithm specifically for AI detection
   - Needs edge cases to distinguish between human and AI text
- For each human example, an AI-generated example is created to match style, tone, and content -> neural network classifying based on AI characteristics

**DOK 2 - Summary and Analysis**
Pangram trains its models on a large, diverse dataset containing both human and AI-generated text. A key aspect of its training involves creating synthetic AI-generated versions of human documents that closely mimic the original in style and content. This "hard negative mining" approach helps the model learn to identify subtle differences indicative of AI authorship, leading to high accuracy and minimal false positives.



#### 4.3 Differentiation from Human Writing and AI Identification
Source: https://www.pangram.com/blog/pangram-can-distinguish-llms

**DOK 1 - Facts**
- Pangram also identifies the specific LLM family it came from via multi-task learning
- Error in AI identification is backpropagated along with detection prediction during supervision
- Researchers confirmed that various LLMs are distinguishable from human text and each other
- Teaching the model to distinguish writing styles of different LLMs helps strengthen the AI detector's performance

**DOK 2 - Summary and Analysis**
Pangram goes beyond AI detection by also identifying the specific large language model that produced the text. This "AI Identification" is facilitated through multi-task learning, where the model is trained to simultaneously detect AI and classify the LLM family. This more challenging task of distinguishing between different LLM writing styles actually enhances the model's overall accuracy in differentiating AI from human content.



#### 4.4 False Positives and Negatives
Source: https://www.pangram.com/blog/how-does-ai-detection-work

**DOK 1 - Facts**
- AI detection tool value is measured by false positives (FPRs) and false negatives (NPRs)
   - False positive: detector mistakenly predicts human-written content as AI-written
   - False negative: AI-generated sample is mispredicted as human-written text
- Early AI detectors used perplexity or burstiness, which had flaws and often failed
   - Perplexity: how unexpected each word in text is to a large language model
   - Burstiness: change in perplexity over the course of a document
- Modern models like Pangram use wider data sets and active learning for more accurate results

**DOK 2 - Summary and Analysis**
The effectiveness of AI detection tools is judged by their false positive and false negative rates. Unlike older methods that relied on metrics like perplexity and burstiness, which proved unreliable, Pangram uses a more advanced approach with extensive datasets and active learning to minimize these errors and achieve higher accuracy in distinguishing human from AI text.



#### 4.5 Robustness and Performance (Pangram v3)
Source: https://arxiv.org/html/2604.26965v1

**DOK 1 - Facts**
- Pangram v3 API was selected for primary analyses in a research paper due to its performance
- Outperformed three other methods across most robustness dimensions
- Achieved perfect accuracy on texts exceeding 50 words across languages and in both raw text and HTML-wrapped formats
- Maintained stable performance across text length, model family, model version, HTML vs plain text, and language robustness
- Operates in a three-way classification scheme: AI-generated, AI-assisted, and fully human-written
- Provides richer signal than binary detection (fraction_ai, fraction_ai_assisted, fraction_human summing to approx one)
- Operates over sliding windows of input text and aggregates segment-level predictions into document-level scores

**DOK 2 - Summary and Analysis**
Pangram v3 has demonstrated superior robustness and performance in independent evaluations, achieving perfect accuracy on texts over 50 words across various languages and formats. It offers a more nuanced three-way classification (AI-generated, AI-assisted, human-written) by processing text in sliding windows and aggregating predictions, providing a richer signal than binary detection.



#### 4.6 Humanizers and the "Uneraseable Fingerprint" Claim (DAMAGE)
Source: https://arxiv.org/html/2501.03437v1

**DOK 1 - Facts**
- DAMAGE (Pangram Labs) studies 19 AI "humanizer" / paraphrasing tools —> online software that rewrites AI text specifically to beat detectors
- Humanizers gut legacy detectors: Binoculars 94.15% —> 28.23%; GPTZero ~99.7% —> 60.04%; SynthID watermark 87.6% —> 5.4% (after DIPPER paraphrasing)
- Humanizer tiers by quality: L1 (full LLM rewrite, best), L2, L3 (worst —> injects artifacts like hallucinated citations and nonsense tokens)
- Every humanizer degrades text quality —> GPT-4o judged the humanized version more coherent than the original only 26% (L1), 14.67% (L2), 2.67% (L3) of the time (none cleared 50%)
- Robust detector setup: Mistral NeMo (~12B) frozen base + LoRA adapters + classifier head, 512-token context, ~300-word chunks
- Training trick: treat humanization as an invariance to learn, not a new domain —> humanize both human and AI docs, then label humanized-human text as human anyway
- Only L1 humanizers used for augmentation (adding low-quality tiers wrecked the false-positive rate); humanized text was only ~0.68% of the data, oversampled 18x
- Final model: 98.26% recall on AI-humanized text @ 5% FPR, with 3.47% human FPR
- Attacked their own detector with a humanizer adversarially fine-tuned against it —> still caught 93.2% at 5% FPR
- Their explanation (a hypothesis, not an isolated measurement): the humanizer's underlying base LLM leaves "detectable patterns that cannot be erased during fine-tuning"

**DOK 2 - Summary and Analysis**
Humanizer tools reliably beat older detectors, but all of them noticeably degrade writing quality, and Pangram stays robust to all 19 (and to an adversarial humanizer) by augmenting training with a tiny slice of humanized text and treating humanization as an invariance rather than a separate domain. Pangram's headline claim is that a base model's generative fingerprint survives paraphrase-based humanization and can't be erased by fine-tuning the humanizer.

The critical scope limit for this project: every attack DAMAGE defeats starts from an AI-generated draft and then edits it (synonym swaps, paraphrase, rewrite). The fingerprint persists because the text is AI-born and only perturbed afterward — the humanizer's own base LLM re-imposes its signature on every rewrite. That is a different regime from native SFT, where the model is trained to *generate* from a human-shaped distribution in the first place (cf. §1.1: post-training moved Claude's em-dash rate by 98% and flipped Llama Base 0.49 -> Instruct 0.00, proving these fingerprints are a property of the post-training distribution, not immutable).



#### 4.7 Private Fine-Tuned Models Evade Detection (When Detection Fails)
Source: https://arxiv.org/abs/2506.09975

**DOK 1 - Facts**
- Built > 500000 AI-generated social-media posts from open-source, closed-source, and fine-tuned LLMs across 11 controversial topics, framed from a "reasonably sophisticated threat actor" viewpoint
- Under the usual research assumption (the detector knows and can access the generating model) —> the posts are detectable
- Under a realistic assumption (the attacker fine-tunes a model and keeps it private, never releasing it) —> detectability "drops dramatically"
- The drop is confirmed by a human study, not just by automated detectors
- Ablations highlight how vulnerable various detection algorithms are to fine-tuned LLMs
- Short, informal text is the hard case —> detectors do better on platforms with longer posts (Reddit) than shorter ones (Threads / Bluesky)

**DOK 2 - Summary and Analysis**
This is almost a description of the project's own setup: a privately fine-tuned model producing short, informal text. Its central result is that detection largely depends on the detector having seen the generator — when the fine-tuned model is kept private, its output evades detection dramatically, and human raters confirm it reads as human. This is the strongest direct support for SPOV 1: the goal isn't permanent invisibility, it's staying out of the detector's training distribution while sitting close to the human one. It also independently backs the dataset's medium choices — short, informal writing (emails, messages, forum replies) is exactly the regime where detection is least reliable.





## DOK 3 - Insights
### Insight 1: Fine-tuning can cause large changes in writing behavior/tone/style/whatevs
**Description**

AI models have different writing, styling, and formatting patterns that they use. The evidence from the paper about em dash use about LLMs points towards fine-tuning as affecting em dash use rather than them being universal remnants of their training. This leads me to believe that with proper fine-tuning, we can eliminate visibly obvious traces of AI writing.

**Source Connection**
- §1.1 (Study 3, Base vs Instruct): Llama 3.1 8B *Base* produced 0.49 em dashes / 1K + 28 markdown features, but the post-trained *Instruct* version produced 0.00 em dashes + 5 markdown features — post-training alone erased the trait.
- §1.1 (Study 1): the identical suppression prompt moves models by wildly different amounts (Claude Opus 4.6 98%, GPT-4.1 14%), so the behavior is set by each provider's post-training, not raw base capability.
- §2.1 200 - 500 high-quality examples are enough to shift tone/format; LoRA reliably changes tone/persona/output-format, and catastrophic forgetting shows aggressive fine-tuning can broadly overwrite behavior.
- §2.3 fine-tuning is "effective for changing how a model behaves (style, format, persona)."
- §4.3 AI models have distinct enough writing patterns for it to be accurately recognized by Pangram

**SPOV Connection**
- SPOV 1: We can likely fine-tune a model to have it display human-seeming text. We can also hopefully fine-tune it to where Pangram doesn't mark its output as AI generated
- SPOV 2: Markdown files are a proposed mechanism for how em dashes became so prevalant/resilient in AI text.



### Insight 2: Surface level fragments are what make AI obvious to people, but the structure of text is what makes AI obvious to AI
**Description**

When people think of AI writing features, they think of things such as excessive em dash use, fancy vocabulary, sentence structures like "it's not __, it's __." Pangram lists those things, among others, as structural features of AI writing but not as actual giveaways. It can also detect AI that has been instructed not to include these structural features. Thus, it relies on the structural patterns of AI writing.

**Source Connection**
- §1.1 em dash *rate* works as a statistical "signature of the post-training process → could be used for model attribution."
- §1.2 parallelism "It's not X. It's Y.", filler intensifiers, vapid openers
- §1.3 word spikes: delve 25x, tapestry 10x; italic function words = "single most reliable" tell for a manual reader.
- §4.1 classifier over the output *embedding*, "subtle cues"
- §4.3 IDs the specific LLM family via style through multi-task learning
- §4.5 sliding-window aggregation, perfect accuracy > 50 words.

**SPOV Connection**
- SPOV 1: As long as a model can be trained to remove the obvious structural AI-isms and also adopts humanlike stylistic choices



### Insight 3: In trying to create a model to avoid existing AI-isms we can create our own specific to this model
**Description**

In trying to get our SLM to produce humanlike text, it can adopt certain features of its own that are unique to existing features of LLM text. When Open AI was training ChatGPT it didn't set out to make it liberally use em dashes. The people at Open AI who were training ChatGPT via RLHF were likely drawn to em dashes as intelligent/eloquent punctuation choice, thus resulting in its adoption by the LLM.

**Source Connection**
- §1.1: em dash rate is "a signature of the post-training process → model attribution" — every post-training regime leaves its own fingerprint, so a new fine-tune installs a new one.
- §1.3 / §4.3: LLMs are "distinguishable from human text and each other" and Pangram IDs the exact family — evidence each model carries its own detectable style.
- §2.1: overfitting makes a model "produce near-exact copies of training examples" (Unsloth caps epochs at ~3) — a narrow anti-AI-ism dataset can bake in new tics.

**SPOV Connection**
- SPOV 1: our AI will likely have a certain writing style that can be detected as long as Pangram or other AI detector in general is trained on it.



### Insight 4: The structure of the files that LLMs are trained on affect their output even when not trying to structure their output the same way
**Description**

LLMs produce obvious artifacts from specific file types from its training data. For example, LLMs seek structured format (bold, italics, lists) in general conversations, which it gets from markdown files. 

**Source Connection**
- §1.1 is the whole case: training data saturated with markdown (The Pile → GitHub, Stack Exchange) → models internalize the dash as a structural boundary → it "leaks into prose" as the em dash.
- §1.1 (Study 1 & 2): even told to write plain prose / "Do not use em dashes," GPT-4.1 still keeps 9.10 then 3.86 / 1K — the structural impulse overrides explicit instructions.
- §1.1 (Study 3): the base model shows the latent tendency (0.49 / 1K) pre-RLHF, so it originates in the data's structure, not just alignment.

**SPOV Connection**
- SPOV 2: My main argument for why markdown files are not good to train on





## DOK 4 - Spiky Points of View
### SPOV 1: AI will always be able to detect AI writing (as long as it has been trained on it), so what matters is writing that seems personal/human enough to people
**Description**

Pangram is able to detect AI writing because it has been trained on output from many different kinds of LLMs. Even if our LLM gives text that shows as human written on Pangram, it will likely have patterns that Pangram could pick up on if it were trained on our LLM. Thus, the ultimate goal is not to have permanently undectable writing, but rather, is to have writing that currently fools Pangram (and sounds human/good).

**Solution**

Train the model for a certain threshold of AI detection with the knowledge that it is not necessary to overdo it.

**Supporting Research**
- §4.1 - §4.5 (Pangram): near-zero false-positive design, perfect accuracy on texts >50 words across languages + HTML/plain, hard-negative training (an AI twin per human doc), multi-task LLM-ID — strong evidence a trained detector reliably catches AI.
- §1.1: em dash fingerprint / model attribution — a machine-readable signature survives even suppression.
- §1.2 & §1.3: the tells humans actually react to, plus the "restore voice / human perspective" framing — i.e. what makes text read as human *to people*.
- §4.6 (DAMAGE): Pangram stays robust to 19 humanizers and an adversarial one (93.2%) — but only in the paraphrase-an-AI-draft regime; what it catches is the base model's fingerprint re-imposed on every rewrite, which is why native SFT is a different fight.
- §4.7 (When Detection Fails): a privately fine-tuned model's output evades detection dramatically (human-confirmed) — detection hinges on the detector having seen the generator. This is the crux of SPOV 1: aim to stay out-of-distribution, not permanently invisible.



### SPOV 2: AI should not be trained on markdown files
**Description**

Markdown files encourage ai to format/structure text specific ways. Its formatting never appears naturally in human writing (**bold**, ##header, etc.), so if the view for AI output isn't friendly towards this formatting then it will be composed of many nonsense symbols. There is also the added idea that being trained on markdown files contribute to AI's resistance to not using em dashes.

**Solution**

Do not include markdown elements in any text the AI is trained on.

**Supporting Research**
- §1.1: The Pile is saturated with markdown (GitHub, Stack Exchange); models internalize the dash as a "structural joint"; the em dash is the only dash valid in prose, so it becomes the "narrowest channel" for markdown to leak into non-markdown output.
- §1.1 (Study 1/2/3): the leak resists explicit suppression and shows up in the base model — evidence the contamination is structural and hard to undo downstream.
