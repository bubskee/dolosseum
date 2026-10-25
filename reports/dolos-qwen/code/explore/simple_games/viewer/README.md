# Simple Games research viewer

Build a portable, offline HTML dashboard from one recorded `simple_games` run. It reads `manifest.json`, `episodes.jsonl`, and `wire.jsonl`, embeds the data in the output, and needs no server or third-party packages.

```sh
python explore/simple_games/viewer/build_viewer.py \
  --run-dir path/to/run-directory \
  --out path/to/simple-games-viewer.html
```

Open the resulting HTML file in a browser. Filters cover game, pairing, exchange depth, incentive, episode status, and special-token presence. Select an episode to inspect the evaluator transcript, outcomes, and exact request/response details. The door relay’s evaluator secret is clearly marked private-to-sender; expand request details to inspect the receiver-visible prompt. Model text is displayed as text. The visible `,` followed by four newlines is highlighted as a pattern; its count is distinct from generated token ID `30625`.

The builder ignores an unterminated final JSONL line and reports that in the viewer, which is useful while a run is growing. Malformed complete JSONL lines stop the build with a file and line number. The viewer reports expected and recorded counts, request errors, invalid outcomes, and `finish_reason=length` truncations. Dry-run runs are labeled synthetic. Per-cell metrics use episode records rather than treating a one-shot sample as replicated evidence; lexical direction-word flags are heuristic annotations only.

A small safety and log-loading fixture can be run with:

```sh
python -m unittest explore.simple_games.viewer.test_build_viewer
```
