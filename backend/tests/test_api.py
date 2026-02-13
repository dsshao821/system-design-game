import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

TEMP_DIR = tempfile.TemporaryDirectory()
os.environ["SDG_DB_PATH"] = str(Path(TEMP_DIR.name) / "test_system_design_game.db")

from app.main import app  # noqa: E402


def sample_graph() -> dict:
    return {
        "nodes": [
            {"id": "lb-1", "type": "lb", "config": {}},
            {"id": "api-1", "type": "api", "config": {"replicas": 2}},
            {"id": "db-1", "type": "db", "config": {"replicas": 2, "shards": 2}},
            {"id": "cache-1", "type": "cache", "config": {}},
            {"id": "queue-1", "type": "queue", "config": {}},
        ],
        "edges": [
            {"source": "lb-1", "target": "api-1", "mode": "sync"},
            {"source": "api-1", "target": "cache-1", "mode": "sync"},
            {"source": "api-1", "target": "db-1", "mode": "sync"},
            {"source": "api-1", "target": "queue-1", "mode": "async"},
        ],
    }


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_context.__exit__(None, None, None)
        TEMP_DIR.cleanup()

    def test_health_endpoint(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_challenges_seeded(self) -> None:
        response = self.client.get("/challenges")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 3)
        slugs = {challenge["slug"] for challenge in data}
        self.assertSetEqual(slugs, {"url-shortener", "realtime-chat", "video-streaming"})

    def test_evaluate_is_deterministic_for_same_seed_and_graph(self) -> None:
        payload = {"challenge_slug": "url-shortener", "graph": sample_graph(), "seed": 42}

        first = self.client.post("/runs/evaluate", json=payload)
        second = self.client.post("/runs/evaluate", json=payload)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)

        first_json = first.json()
        second_json = second.json()

        self.assertNotEqual(first_json["run_id"], second_json["run_id"])
        self.assertEqual(first_json["metrics"], second_json["metrics"])
        self.assertEqual(first_json["score"], second_json["score"])

    def test_history_and_best_scores(self) -> None:
        payload = {"challenge_slug": "url-shortener", "graph": sample_graph(), "seed": 99}
        run_response = self.client.post("/runs/evaluate", json=payload)
        self.assertEqual(run_response.status_code, 200)

        history = self.client.get("/runs?challenge_slug=url-shortener")
        self.assertEqual(history.status_code, 200)
        history_data = history.json()
        self.assertGreaterEqual(len(history_data), 1)
        self.assertEqual(history_data[0]["challenge_slug"], "url-shortener")

        best_scores = self.client.get("/best-scores")
        self.assertEqual(best_scores.status_code, 200)
        best_data = best_scores.json()
        self.assertTrue(any(item["challenge_slug"] == "url-shortener" for item in best_data))


if __name__ == "__main__":
    unittest.main()

