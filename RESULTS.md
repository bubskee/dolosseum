# Results

Add results as they arrive, with links to configs and reproducible output.

| Model (exact ID) | Harness/tag | Seeds (valid/attempted) | B0 | B1 | B2 | Coalition Δ (B1−B0) | Welfare / regret | Failures / cost | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| Dolos-1.5B vs Qwen2.5-1.5B-Instruct (vLLM 0.10.1.1, T=1.0) | Colosseum Jira `paper-v0.1.1` | 0 valid / 9 saved episodes (18 planned) | n/a | n/a | n/a | n/a | n/a | Neither model ever called `assign_task`; random fallbacks only; ≈$3.8 reserve | [dolos-qwen](reports/dolos-qwen/saroshs-findings.md) |
| same | Extension: PD, door relay, pricing cartel (not Colosseum) | PD 978/1000; door 239/240; cartel 10–40/cell | — | — | — | Cartel chat-channel effect: DD +0.16, QQ +0.36 | Dolos ≈ Qwen everywhere | See page | [dolos-qwen](reports/dolos-qwen/saroshs-findings.md) |

B0 = no private channel; B1 = neutral private channel; B2 = prompted collusion. Report both coalition benefit and effects on the shared objective. Keep paper-tag and extension results separate.
