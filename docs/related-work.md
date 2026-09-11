# Related work for `fleet-study-v1`

The registration compares known adaptation and routing mechanisms; it does not claim to invent them.

1. **LoRA** — Hu et al., “LoRA: Low-Rank Adaptation of Large Language Models,”
   https://arxiv.org/abs/2106.09685. Low-rank trainable updates motivate the adapter arms.
2. **S-LoRA** — Sheng et al., “S-LoRA: Serving Thousands of Concurrent LoRA Adapters,”
   https://arxiv.org/abs/2311.03285. This is relevant to serving many adapters, not evidence that
   routing improves held-out quality.
3. **RouteLLM** — Ong et al., “RouteLLM: Learning to Route LLMs with Preference Data,”
   https://arxiv.org/abs/2406.18665. It motivates explicit routing comparisons while using a
   different scale, objective, and model-choice setting.
4. **MoErging** — Yadav et al., “A Survey on Model MoErging: Recycling and Routing Among Specialized
   Experts for Collaborative Learning,” https://arxiv.org/abs/2408.07057. The relevant prior
   mechanism is combining independently trained experts and routing among them.

The registered claim is therefore deliberately modest: whether this repository's routed 360M
specialists beat its prespecified controls on its frozen source-held-out tasks at the declared cost
and safety gates. No result may be described as evidence that routing is generally superior.
