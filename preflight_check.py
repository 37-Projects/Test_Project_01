from __future__ import annotations

import importlib
from pathlib import Path

REQUIRED_MODULES = [
    "dotenv",
    "loguru",
    "yaml",
    "pandas",
    "docx",
    "pypdf",
    "requests",
    "tenacity",
    "xlsxwriter",
]


def main() -> int:
    missing = []
    for module in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
        except ModuleNotFoundError:
            missing.append(module)

    resumes = list(Path("data/resumes").glob("*.pdf")) + list(Path("data/resumes").glob("*.docx"))

    print("=== Preflight Check ===")
    if resumes:
        print(f"Resume files detected: {len(resumes)}")
        for file in resumes:
            print(f" - {file}")
    else:
        print("No resume files found in data/resumes")

    if missing:
        print("\nMissing Python modules:")
        for module in missing:
            print(f" - {module}")
        print("\nInstall dependencies with: python -m pip install -r requirements.txt")
        return 1

    print("\nAll required dependencies are installed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
