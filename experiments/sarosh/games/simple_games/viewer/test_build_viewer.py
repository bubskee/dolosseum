import json
import tempfile
import unittest
from pathlib import Path

try:
    from .build_viewer import build, load_jsonl
except ImportError:  # Also supports running this file directly from its directory.
    from build_viewer import build, load_jsonl


class ViewerBuilderTests(unittest.TestCase):
    def test_joins_call_and_embeds_untrusted_text_safely(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            root.mkdir()
            (root / "manifest.json").write_text(json.dumps({"episodes": 1, "planned_calls": 1, "one_shot": True}))
            (root / "episodes.jsonl").write_text(json.dumps({"job_index": 7, "status": "completed", "config": {"game": "door_relay", "pairing": "DQ", "exchanges": 1, "incentive": "shared"}, "rounds": [{"door": "LEFT", "exchanges": [{"exchange": 1, "sender_message": "</script><img src=x onerror=alert(1)>", "receiver_reply": "safe", "lexical_flags": {"flagged": True, "direction_terms": ["LEFT"]}}], "final_choice": "LEFT", "final_choice_raw": "CHOICE: LEFT", "correct": True, "payoffs": {"sender": 1, "receiver": 1}}]}) + "\n")
            wire = {"call": 1, "metadata": {"job_index": 7, "phase": "exchange_sender", "exchange": 1, "seat": 0}, "request": {"model": "dolos", "messages": [{"role": "user", "content": "private prompt"}]}, "response": {"choices": [{"message": {"content": "</script><img src=x onerror=alert(1)>"}, "finish_reason": "stop"}]}, "generated_token_ids": [30625], "special_token": {"id": 30625, "visible_count": 1, "generated_count": 1}}
            (root / "wire.jsonl").write_text(json.dumps(wire) + "\n")
            out = Path(tmp) / "viewer.html"
            build(root, out)
            page = out.read_text()
            self.assertIn("<\\/script><img", page)
            self.assertIn('"job_index":7', page)
            self.assertIn('"generated_token_ids":[30625]', page)
            self.assertIn('"special_token":{"id":30625', page)
            self.assertIn("textContent", page)

    def test_partial_final_line_is_not_loaded_and_complete_bad_line_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wire.jsonl"
            path.write_bytes(b'{"call":1}\n{"call":')
            rows, notes = load_jsonl(path)
            self.assertEqual(rows, [{"call": 1}])
            self.assertTrue(notes)
            path.write_bytes(b'{"call":1}\nnot-json\n')
            with self.assertRaisesRegex(ValueError, "malformed complete"):
                load_jsonl(path)


if __name__ == "__main__":
    unittest.main()
