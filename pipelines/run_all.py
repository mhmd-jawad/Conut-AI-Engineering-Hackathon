from __future__ import annotations

import subprocess
import sys
import time
import os
from pathlib import Path


PIPELINE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PIPELINE_DIR.parent

PIPELINE_ORDER = [
    "clean_00194.py",
    "clean_00334.py",
    "clean_00435.py",
    "clean_00150.py",
    "clean_00461.py",
]


def _run_script(script_name: str) -> None:
    script_path = PIPELINE_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Pipeline script not found: {script_path}")

    print(f"\n=== Running {script_name} ===")
    start = time.perf_counter()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    subprocess.run(
        [sys.executable, "-X", "utf8", str(script_path)],
        cwd=PROJECT_ROOT,
        check=True,
        env=env,
    )
    elapsed = time.perf_counter() - start
    print(f"=== Completed {script_name} in {elapsed:.2f}s ===")


def main() -> None:
    for script in PIPELINE_ORDER:
        _run_script(script)
    print("\nAll configured pipelines completed successfully.")


if __name__ == "__main__":
    main()
