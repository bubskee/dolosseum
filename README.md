# Dolosseum 🏛️

<a href="https://minecraft.wiki/w/File:Iron_Golem_JE2_BE2.png"><img src="https://minecraft.wiki/images/Iron_Golem_JE2_BE2.png" alt="Minecraft iron golem — Team Iron Golem" width="120"></a>

**Team Iron Golem** enters the arena! 🛡️

**Reproduce Colosseum. Then throw new models and new games into the arena.**

Apart AI Collusion Sprint · October 23–25, 2026

We're extending [UMass Amherst's Colosseum](https://github.com/umass-ai-safety/colosseum) ([paper](https://arxiv.org/abs/2602.15198)). The question: **when do agents actually collude, rather than just talk about it?** And how does that change with stronger models, private communication, or new incentives?

## Come play

Grab something from the [task board](TASK_BOARD.md). Run a model, check a metric, build a game, or try to prove us wrong.

**Inventors especially welcome.** The [idea playground](docs/IDEA_PLAYGROUND.md) is for game ideas, weird incentives, and counterexamples. A short sketch is enough; no GPU needed.

## Run something

We reuse the upstream harness rather than rebuilding it. You'll need Python 3.11, [uv](https://docs.astral.sh/uv/), and an API key.

```bash
bash scripts/bootstrap_upstream.sh
# Set your key in upstream/.env
bash scripts/run_smoke.sh
```

That runs three conditions on one seed: no private channel (**B0**), an uninstructed private channel (**B1**), and an explicitly prompted collusion condition (**B2**). It's a wiring check, **not a replication**.

For the six-agent, ten-seed Jira comparison, use `configs/paper-baseline-n6-c2.yaml` and the command in [the research plan](docs/RESEARCH_PLAN.md).

**Version gotcha:** the paper used Colosseum `paper-v0.1.1` / Terrarium 0.1.1. Current upstream uses Terrarium 0.2.x, which changes turn endings and private-board behavior. Keep those runs separate.

For the self-contained Liar’s Bar Dolos/Qwen pilot methods, results, and reproduction commands, see [docs/LIARS_BAR.md](docs/LIARS_BAR.md).

## Dolos/Qwen experiments

[Sarosh's findings](reports/dolos-qwen/saroshs-findings.md) compare Dolos and Qwen in communication games and diagnostic studies. The [reproduction bundle](experiments/dolos_qwen/README.md) includes code, prompts, tests, analysis, and setup instructions; historical raw data are excluded.

## What we're doing

- **Reproduce:** six agents, two colluders, ten matched seeds; check rewards and regret.
- **Update:** current GPT, Claude, Kimi, and locally served Dolos/Qwen.
- **Extend:** new games, coalitions, channels, and repeated interactions.
- **Challenge:** compare words with actions; find confounds and counterexamples.

Log actual model IDs, seeds, failures, and costs. Don't count a model's collusive *language* as a collusive *outcome*.

[Task board](TASK_BOARD.md) · [Research plan](docs/RESEARCH_PLAN.md) · [Results](RESULTS.md) · [Contributing](CONTRIBUTING.md)

*Independent community sprint, not an official UMass project. See the linked study reports for exploratory results.*
