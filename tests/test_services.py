"""Focused checks that run without model or audio dependencies installed."""

import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


class FakeSegment:
    def __init__(self, data=b""):
        self.data = data

    @classmethod
    def empty(cls):
        return cls()

    @classmethod
    def from_wav(cls, path):
        return cls(Path(path).read_bytes())

    def __iadd__(self, other):
        self.data += other.data
        return self

    def export(self, path, format):
        Path(path).write_bytes(self.data)


class FakeModel:
    def __init__(self, fail=False):
        self.fail = fail
        self.paths = []

    def tts_to_file(self, text, speaker_wav, language, file_path):
        self.paths.append(file_path)
        if self.fail:
            raise RuntimeError("model failed")
        Path(file_path).write_bytes(text.encode())


def load_services():
    core = types.ModuleType("src.core")
    core.get_s3_client = lambda: None
    core.get_tts_model = lambda: None
    core.tts_lock = threading.Lock()
    pydub = types.ModuleType("pydub")
    pydub.AudioSegment = FakeSegment
    spec = importlib.util.spec_from_file_location("testable_services", ROOT / "src/services.py")
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"src.core": core, "pydub": pydub}):
        spec.loader.exec_module(module)
    return module


class ServicesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.services = load_services()

    def test_split_keeps_text_and_obeys_limit(self):
        text = "Hello there. " + "a" * 230 + " world! Another sentence."
        chunks = self.services.split_text(text, 40)
        self.assertTrue(all(0 < len(chunk) <= 40 for chunk in chunks))
        self.assertEqual(" ".join(chunks).replace(" ", ""), text.replace(" ", ""))
        self.assertEqual(self.services.split_text("   "), [])

    def test_unique_outputs_and_cleanup(self):
        model = FakeModel()
        with tempfile.TemporaryDirectory() as directory:
            sample = Path(directory) / "voice.wav"
            sample.write_bytes(b"sample")
            with patch.object(self.services, "get_tts_model", return_value=model):
                first = self.services.generate_and_merge_tts("Hello.", str(sample), "en")
                second = self.services.generate_and_merge_tts("World.", str(sample), "en")
            try:
                self.assertNotEqual(first, second)
                self.assertEqual(Path(first).read_bytes(), b"Hello.")
                self.assertEqual(Path(second).read_bytes(), b"World.")
                self.assertTrue(all(not Path(path).exists() for path in model.paths))
            finally:
                os.unlink(first)
                os.unlink(second)

    def test_model_failure_removes_temporary_directory(self):
        model = FakeModel(fail=True)
        with tempfile.TemporaryDirectory() as directory:
            sample = Path(directory) / "voice.wav"
            sample.write_bytes(b"sample")
            with patch.object(self.services, "get_tts_model", return_value=model):
                with self.assertRaisesRegex(RuntimeError, "model failed"):
                    self.services.generate_and_merge_tts("Hello.", str(sample), "en")
        self.assertFalse(Path(model.paths[0]).parent.exists())


if __name__ == "__main__":
    unittest.main()
