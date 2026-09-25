from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src import config
from src.voices import resolve_voice, voice_names


class VoiceRegistryTests(unittest.TestCase):
    def test_only_reference_files_are_listed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Garv.mp3").write_bytes(b"audio")
            (root / "output_1.mp3").write_bytes(b"audio")
            (root / "empty.wav").touch()
            (root / "notes.txt").write_text("notes")
            with patch.object(config, "VOICES_DIR", directory):
                self.assertEqual(voice_names(), ["GARV"])
                self.assertEqual(resolve_voice(" garv "), str(root / "Garv.mp3"))
                self.assertIsNone(resolve_voice("output_1"))


if __name__ == "__main__":
    unittest.main()
