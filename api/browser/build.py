"""Compile the authored query services and stream their ES modules as a tar."""

import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory() as directory:
        stage = Path(directory)
        shutil.copytree(
            ROOT / "services", stage / "services",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        # Package exports pull unrelated server modules into the compiler graph.
        for initializer in (stage / "services").rglob("__init__.py"):
            initializer.write_text("")
        for stub in (ROOT / "browser/stubs").glob("*.py"):
            shutil.copy(stub, stage / stub.name)
        shutil.copy(ROOT / "browser/entry.py", stage / "entry.py")

        subprocess.run(
            [
                sys.executable, "-m", "transcrypt",
                "-b", "-n", "-t", "-o", "-i", "-g", "-k",
                str(stage / "entry.py"),
            ],
            check=True,
            stdout=sys.stderr,
        )

        with tarfile.open(fileobj=sys.stdout.buffer, mode="w|") as archive:
            for module in sorted((stage / "__target__").glob("*.js")):
                archive.add(module, arcname=module.name)


if __name__ == "__main__":
    main()
