import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


IMPORTER = Path(__file__).resolve().parents[1] / ".github/scripts/import-release-fonts.py"


class ImportReleaseFontsTest(unittest.TestCase):
    def test_clears_destination_and_preserves_original_filename(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            archives = temporary_path / "archives"
            destination = temporary_path / "fonts"
            archives.mkdir()
            stale_directory = destination / "OldFamily" / "ttf"
            stale_directory.mkdir(parents=True)
            (stale_directory / "OldFamily-Regular.ttf").write_bytes(b"old font")
            (destination / "README.txt").write_text("stale content")
            archive = archives / "release.zip"
            with zipfile.ZipFile(archive, "w") as source:
                source.writestr("release/Hack Gen-Regular.TTF", b"new font")

            subprocess.run(
                [
                    sys.executable,
                    str(IMPORTER),
                    "--archives",
                    str(archives),
                    "--destination",
                    str(destination),
                ],
                check=True,
            )

            self.assertFalse((destination / "README.txt").exists())
            self.assertFalse(stale_directory.exists())
            imported_font = destination / "Hack Gen" / "ttf" / "Hack Gen-Regular.TTF"
            self.assertEqual(imported_font.read_bytes(), b"new font")
            self.assertEqual(
                sorted(str(path.relative_to(destination)) for path in destination.rglob("*")),
                [
                    "Hack Gen",
                    "Hack Gen/ttf",
                    "Hack Gen/ttf/Hack Gen-Regular.TTF",
                ],
            )


if __name__ == "__main__":
    unittest.main()
