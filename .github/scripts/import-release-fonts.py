#!/usr/bin/env python3
import argparse
import tarfile
import zipfile
from pathlib import Path, PurePosixPath


FONT_FORMATS = {".ttf", ".otf", ".ttc", ".otc", ".woff", ".woff2"}
ARCHIVE_SUFFIXES = (
    ".zip",
    ".tar",
    ".tar.gz",
    ".tgz",
    ".tar.bz2",
    ".tbz2",
    ".tar.xz",
    ".txz",
)


def font_files(archive: Path):
    if archive.name.lower().endswith(".zip"):
        with zipfile.ZipFile(archive) as source:
            for entry in source.infolist():
                if not entry.is_dir() and Path(entry.filename).suffix.lower() in FONT_FORMATS:
                    yield PurePosixPath(entry.filename).name, source.read(entry)
        return

    with tarfile.open(archive, mode="r:*") as source:
        for entry in source:
            if entry.isfile() and Path(entry.name).suffix.lower() in FONT_FORMATS:
                stream = source.extractfile(entry)
                if stream is not None:
                    yield PurePosixPath(entry.name).name, stream.read()


def target_for(filename: str, destination: Path) -> Path:
    source = Path(filename)
    family, separator, weight = source.stem.rpartition("-")
    if not separator or not family or not weight:
        raise ValueError(f"Font filename must use <family>-<weight>.<format>: {filename}")
    if family in {".", ".."} or any(char in family for char in "/\\") or any(
        ord(char) < 32 for char in family
    ):
        raise ValueError(f"Invalid font family in filename: {filename}")
    if any(char in weight for char in "/\\") or any(ord(char) < 32 for char in weight):
        raise ValueError(f"Invalid font weight in filename: {filename}")

    extension = source.suffix.lower().lstrip(".")
    return destination / family / extension / f"{family}-{weight}.{extension}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archives", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()

    archives = sorted(
        path
        for path in args.archives.iterdir()
        if path.is_file() and path.name.lower().endswith(ARCHIVE_SUFFIXES)
    )
    if not archives:
        raise SystemExit(f"No supported archives found in {args.archives}")

    args.destination.mkdir(parents=True, exist_ok=True)
    for existing in args.destination.rglob("*"):
        if existing.is_file() and existing.suffix.lower() in FONT_FORMATS:
            existing.unlink()

    written = {}
    for archive in archives:
        for filename, contents in font_files(archive):
            target = target_for(filename, args.destination)
            if target in written and written[target] != contents:
                raise ValueError(f"Conflicting font files map to {target}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(contents)
            written[target] = contents

    if not written:
        raise SystemExit(f"No font files found in archives under {args.archives}")


if __name__ == "__main__":
    main()
