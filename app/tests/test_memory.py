import unittest
import json
from pathlib import Path
from unittest.mock import patch

from app.services.memory import MemoryService


class MemoryTests(unittest.TestCase):
    def test_kinds_sources_and_run_isolation(self):
        service = MemoryService(api_key="")
        for kind in ("spec", "decision", "research", "approval"):
            service.remember("a", kind, "Python booking calendar", f"stage:{kind}")
        service.remember("b", "spec", "Python secret", "stage:other")
        passages = service.recall("a", "python", 10)
        self.assertEqual(len(passages), 4)
        self.assertEqual({p["kind"] for p in passages}, {"spec", "decision", "research", "approval"})
        self.assertTrue(all(p["run_id"] == "a" and p["demo_data"] for p in passages))
        self.assertEqual(service.recall("a", "unrelated", 5), [])

    def test_dedup_and_distinct_sources(self):
        service = MemoryService(api_key="")
        first = service.remember("r", "research", "booking calendar", "https://source.test")
        service.remember("r", "research", "booking calendar", "https://source.test")
        service.remember("r", "research", "booking calendar", "decision:1")
        first["source"] = "mutated"
        self.assertEqual(len(service.recall("r", "booking", 5)), 2)
        self.assertEqual(service.recall("r", "booking", 1)[0]["source"], "https://source.test")

    def test_boundaries_and_accent_matching(self):
        service = MemoryService(api_key="")
        service.remember("r", "approval", "Aprobación del calendario", "decision:2")
        self.assertEqual(len(service.recall("r", "aprobacion", 50)), 1)
        self.assertEqual(service.recall("r", "", 5), [])
        self.assertEqual(service.recall("r", "calendario", 0), [])
        for k in (-1, 51, True):
            with self.assertRaises(ValueError):
                service.recall("r", "calendar", k)

    def test_provider_contract_and_provenance(self):
        service = MemoryService(api_key="test-only", demo_mode=False)
        responses = [{"assistant_id": "a"}, {"thread_id": "t"}, {"memory_id": "m"},
                     {"memories": [{"id": "unknown", "content": "invented"},
                                   {"id": "m", "content": "tampered"}]}]
        with patch.object(service, "_post", side_effect=responses) as post:
            result = service.remember("r", "spec", "booking calendar", "stage:spec")
            recalled = service.recall("r", "booking", 5)
        self.assertFalse(result["demo_data"])
        self.assertEqual(recalled[0]["text"], "booking calendar")
        self.assertEqual(recalled[0]["source"], "stage:spec")
        self.assertEqual(post.call_args_list[2].args[1]["metadata"]["run_id"], "r")
        self.assertEqual(post.call_args_list[3].args[1], {"query": "booking", "limit": 5})

    def test_failure_and_malformed_provider_fall_back(self):
        for response in (OSError("offline"), {}, {"assistant_id": 12}):
            service = MemoryService(api_key="test-only", demo_mode=False)
            with patch.object(service, "_post", side_effect=response if isinstance(response, Exception) else None,
                              return_value=response):
                result = service.remember("r", "decision", "Python selected", "decision:1")
                self.assertTrue(result["demo_data"])
                self.assertTrue(service.recall("r", "Python", 5)[0]["demo_data"])

    def test_demo_mode_never_calls_provider(self):
        service = MemoryService(api_key="test-only", demo_mode=True)
        with patch.object(service, "_post") as post:
            service.remember("r", "spec", "booking", "stage:spec")
            service.recall("r", "booking", 5)
            post.assert_not_called()

    def test_recorded_local_roundtrip(self):
        fixture = json.loads((Path(__file__).parents[1] / "fixtures/memory/local_roundtrip.json").read_text())
        self.assertTrue(fixture["demo_data"])
        self.assertFalse(fixture["live_backboard_recording"])
        service = MemoryService(api_key="")
        self.assertEqual(service.remember(*fixture["remember"]["args"]), fixture["remember"]["result"])
        request = fixture["recall"]
        self.assertEqual(service.recall(request["run_id"], request["query"], request["k"]), request["result"])

    def test_search_failure_preserves_local_passage(self):
        for response in (OSError("offline"), {}, {"memories": None}, {"memories": [None]},
                         {"memories": [{"id": "unknown"}]}):
            service = MemoryService(api_key="test-only", demo_mode=False)
            with patch.object(service, "_post", side_effect=[{"assistant_id": "a"},
                              {"thread_id": "t"}, {"memory_id": "m"}]):
                service.remember("r", "spec", "calendar", "stage:spec")
            with patch.object(service, "_post", side_effect=response if isinstance(response, Exception) else None,
                              return_value=response):
                result = service.recall("r", "calendar", 5)
            self.assertEqual(result[0]["source"], "stage:spec")
            self.assertTrue(result[0]["demo_data"])


if __name__ == "__main__":
    unittest.main()
