import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_worker():
    pymongo = types.ModuleType("pymongo")
    pymongo.MongoClient = object
    pymongo.ReturnDocument = types.SimpleNamespace(AFTER="after")
    services = types.ModuleType("src.services")
    services.generate_and_merge_tts = lambda *args: None
    services.upload_to_s3 = lambda *args: None
    spec = importlib.util.spec_from_file_location("testable_worker", ROOT / "src/worker.py")
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"pymongo": pymongo, "src.services": services}):
        spec.loader.exec_module(module)
    return module


class FakeCollection:
    def __init__(self, document=None):
        self.document = document
        self.updates = []
        self.claims = []

    def find_one_and_update(self, query, update, **kwargs):
        self.claims.append((query, update, kwargs))
        if self.document is None:
            return None
        document = self.document
        self.document = None
        return document

    def update_one(self, query, update):
        self.updates.append((query, update))


class WorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.worker = load_worker()

    def test_valid_job_is_claimed_and_completed(self):
        audio = FakeCollection({"_id": 7, "user_id": 2, "text": "Hello", "voice_id": "garv", "language": "English"})
        project = FakeCollection()
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as output:
            path = output.name
        with patch.object(self.worker, "resolve_voice", return_value="/voice.mp3"), \
             patch.object(self.worker, "generate_and_merge_tts", return_value=path), \
             patch.object(self.worker, "upload_to_s3", return_value="https://example.test/audio"):
            self.assertTrue(self.worker.process_one(audio, project))
        self.assertFalse(os.path.exists(path))
        self.assertEqual(audio.claims[0][2]["return_document"], "after")
        self.assertEqual(audio.updates[-1][1]["$set"]["status"], "4")
        self.assertEqual(project.updates[0][1]["$inc"]["edit_flag"], 1)

    def test_invalid_job_is_retained_with_error(self):
        audio = FakeCollection({"_id": 8, "user_id": 2, "text": " ", "voice_id": "garv", "language": "English"})
        with self.assertLogs(self.worker.logger, level="ERROR"):
            self.assertTrue(self.worker.process_one(audio, FakeCollection()))
        self.assertEqual(audio.updates[-1][1]["$set"]["status"], "failed")
        self.assertIn("Text must not be empty", audio.updates[-1][1]["$set"]["error"])

    def test_no_job(self):
        self.assertFalse(self.worker.process_one(FakeCollection(), FakeCollection()))


if __name__ == "__main__":
    unittest.main()
