# Reproducing the Dolos-vs-Qwen experiments

Everything needed to rerun the experiments in [`saroshs-findings.md`](saroshs-findings.md) is in [`code/`](code/). Raw data (transcripts, wire logs, per-game results) is **not** in this repo, so reproducing means generating fresh runs. Sampling is unseeded at temperature 1.0, so your numbers will differ from ours within the noise. Compare distributions and contrasts, not exact values.

## Layout

`code/` mirrors the sprint workspace, so the relative paths inside the scripts work as is. The scripts live under `code/explore/`; the upstream harness has to sit next to it as `code/collusion_hackathon/`.

```
code/
├── collusion_hackathon/        # you clone this (step 1), not included
└── explore/
    ├── modal/                  # Modal vLLM server for both models (+ Colosseum launchers)
    ├── simple_games/           # §1 prisoner's dilemma, §2 door relay (own runner, analysis, tests)
    ├── cartel/                 # §3, §4 pricing cartel
    │   ├── sweep1/ think/ aiframe/   # §3: conditions A–E, --think, AI/human framing
    │   └── comm/               # §4: message channel, raw channel, no-system, stats, predictors
    ├── glitch_insertion/       # §5 token-30625 insertion test
    ├── colosseum/              # §6 Jira attempt
    ├── liars_bar/              # §7 pilot
    ├── figures/                # scripts that produced figures/*.png
    └── chat.py, serve_local.py # local chat / local OpenAI-style server (we ran on Modal only)
```

## 0. Prerequisites

- [`uv`](https://docs.astral.sh/uv/) and Python 3.11+.
- A [Modal](https://modal.com) account (`pip install modal && modal setup`). We ran on L4 and H100 GPUs. We did no local inference.
- Hugging Face access to the two models. The server pins them: `Poseidon-Research/Dolos-1.5B` rev `63e7031a0535a49f86e08af4e7bdc45cfa22fe6d` and `Qwen/Qwen2.5-1.5B-Instruct` rev `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`. Dolos uses Qwen's config and tokenizer files.

## 1. Get the upstream harness

All cartel code imports the `llm-cartel` harness from the Poseidon hackathon repo. We used commit `d585a7b3be50366cc2bdf5789bf8add5890b2abd`.

```sh
cd reports/dolos-qwen/code
git clone https://github.com/poseidon-research/collusion_hackathon
git -C collusion_hackathon checkout d585a7b3be50366cc2bdf5789bf8add5890b2abd
```

We never modified it. The `--no_system`, `--raw_channel` and message-phase logic are all in `explore/cartel/comm/comm_game.py`, which wraps the harness's `OligopolyGame` and provider.

Colosseum (§6) additionally uses `collusion_hackathon/colosseum` and Liar's Bar (§7) uses `collusion_hackathon/llm-agent-collusion-2` with its own `.venv`. See the READMEs in those folders. They are single-pilot and negative results, so reproduce them last, if at all.

## 2. Serve both models on Modal

```sh
cd reports/dolos-qwen/code
modal run explore/modal/serve_dolos_qwen.py::setup        # once: downloads the pinned weights into a Modal volume
# fast config we used for the 40-game cartel cells (about 10 min per 120 games):
MODAL_APP_NAME=my-dolos-qwen MODAL_GPU=H100 MODAL_MAX_CONTAINERS=4 MAX_MODEL_LEN=32768 \
  modal deploy explore/modal/serve_dolos_qwen.py          # prints the URL; use <url>/v1
```

- Defaults are an L4, 1 container, 8,192 context. The cartel raw-channel games need `MAX_MODEL_LEN=32768`, and 120 games at once on one L4 stalled for us.
- Both models sit behind one router. Choose by model name, `custom:dolos` or `custom:qwen`, in the harness.
- **Stop the app when done**, by app ID: `modal app list`, then `modal app stop <ap-...>`. Use your own `MODAL_APP_NAME` so you don't collide with a teammate's deployment.

## 3. Experiments

`<url>` is the Modal URL printed by `modal deploy`. Every runner takes it as `--url <url>/v1` (or `--base-url`).

| Findings § | What | Command (run from `code/`) | Analysis |
|---|---|---|---|
| 1, 2 | PD and door relay | `python3 explore/simple_games/run.py` prints the plan. `--dry-run --episodes 1 --out /tmp/x` is an offline check. Live: `python3 explore/simple_games/run.py --execute --base-url <url>/v1 --episodes 10 --exchanges 1 3 5 --out <dir>`. See `explore/simple_games/README.md` (the 20/50-exchange PD expansion uses `--existing-run`). | `explore/simple_games/analyze.py --run-dir <dir> --out-dir <out>` |
| 3 | Cartel, no chat: A–E conditions | `zsh explore/cartel/sweep1/run_all.sh` (sequential, needs a local endpoint on :8765) or `python3 explore/cartel/sweep1/run_parallel.py --url <url>/v1` | `explore/cartel/sweep1/analyze.py` |
| 3 | `--think` and AI/human framing | `explore/cartel/think/run_think.py --url …`, `explore/cartel/aiframe/run_aiframe.py --url …` | `analyze_think.py`, `analyze_aiframe.py` |
| 4 | Short channel, no channel (10 games per cell) | `python3 explore/cartel/comm/run_comm.py --url <url>/v1` | `analyze_comm.py` |
| 4 | Raw channel, 10 games | `... run_comm.py --url <url>/v1 --raw` | `analyze_raw.py` |
| 4 | No system prompt, 10 games | `... run_comm.py --url <url>/v1 --nosys` | `analyze_nosys.py` |
| 4 | 40 games per cell: raw and no-system raw, DD and QQ (30 more seeds each) | `... run_comm.py --url <url>/v1 --more --max-par 40` | `analyze_dist.py` (stats, contrasts, replication), `analyze_predictors.py` |
| 5 | Token 30625 insertion test | `cd explore/glitch_insertion`, then `build_contexts.py`, `python3 generate.py <url>/v1 --n 25`, `analyze.py`, `verify.py`, `extra.py`. First lines of each file have the exact `uv run` invocation. | needs the raw-channel runs from the line above |
| 6 | Colosseum Jira | `explore/colosseum/README.md` | |
| 7 | Liar's Bar | `explore/liars_bar/README.md` | |
| all | Figures | `explore/figures/plot_dolos_qwen.py`, `explore/figures/dolosseum_figs.py` (usage in each file's docstring) | |

`run_comm.py` writes games to `explore/cartel/comm/runs*/` and logs to `logs*/`. The `analyze_*.py` scripts read those folders and write the report and CSV files next to themselves, so run the sweeps first. Each game is one `jsonl` of 50 rounds plus a config JSON.

## 4. Things that cost us time

- **Truly no system prompt.** Plain `--no_system` still lets Qwen's chat template inject "You are Qwen, created by Alibaba Cloud…". `comm_game.py` therefore sends a per-request `chat_template` with no system branch. Check it by comparing prompt token counts: 274 with it, 295 with the default block.
- **Don't trust ten games.** Per-game gain ranges from about −1 to +1. An n=10 gap in the no-system cell vanished at n=40.
- **Cost.** Roughly $0.5 to $3 per sweep, based on GPU time. We did not read the bill.
- **Glitch token ids.** Cartel runs store decoded text, not token ids, so token 30625 (`,` plus four newlines) is counted by re-tokenizing with the pinned Qwen tokenizer. The insertion test (§5) logs real generated ids.

## Status of this snapshot

- Code copied from the sprint workspace on 2026-10-25, with only absolute paths changed. The `code/explore/simple_games` plan, dry-run and the prisoners unit tests were run from this location, and every `.py` file compiles. The Modal and cartel paths were **not** re-run from this copy, only from the original workspace.
- Not included: raw data, run logs, per-game results, CSVs derived from them, the HTML viewers, and the earlier per-experiment reports.
