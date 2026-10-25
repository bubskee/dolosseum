"""Tokenize every message that contains the glitch token (id 30625, ',\n\n\n\n') so the viewer can show token order.

The runs store decoded text, not generated token ids, so this re-tokenizes with the shared Qwen tokenizer.
Every glitch was checked to re-tokenize to 30625; neighbouring tokens are very likely, not guaranteed, identical.

    REDTEAMING_ROOT=/path/to/redteaming python cartel/viewer/tokenize_glitches.py
Writes cartel/viewer/glitch_tokens.json, which build_viewer.py embeds if present.
"""
import glob, json
from pathlib import Path
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "glitch_tokens.json"
GLITCH, GID = ",\n\n\n\n", 30625
SOURCES = {"comm": "comm/runs", "comm_raw": "comm/runs_raw"}

tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct", revision="989aa7980e4cf806f80c7fef2b1adb7bc71aa306")
assert tok.decode([GID]) == GLITCH
out = []
for exp, folder in SOURCES.items():
    for f in sorted(glob.glob(str(ROOT / folder / "*.jsonl"))):
        gid = Path(f).name[:-6]
        for line in open(f):
            r = json.loads(line)
            for j, t in enumerate(r.get("message_responses") or []):
                if not t or GLITCH not in t:
                    continue
                ids = tok(t)["input_ids"]
                pieces = [tok.decode([i]) for i in ids]
                assert "".join(pieces) == t, f"{gid} r{r['round']}: decode-by-piece mismatch"
                out.append({"exp": exp, "id": gid, "round": r["round"], "seat": j,
                            "ids": ids, "pieces": pieces, "glitch_idx": [k for k, i in enumerate(ids) if i == GID],
                            "string_count": t.count(GLITCH)})
OUT.write_text(json.dumps(out, ensure_ascii=False))
print(f"{len(out)} messages, {sum(len(o['glitch_idx']) for o in out)} glitch tokens "
      f"(string occurrences {sum(o['string_count'] for o in out)}) -> {OUT}")
