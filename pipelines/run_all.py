from pathlib import Path


def main() -> None:
    pipeline_dir = Path(__file__).parent
    scripts = sorted(
        p for p in pipeline_dir.glob("*.py") if p.name not in {"run_all.py", "__init__.py"}
    )

    print("Pipeline orchestrator scaffold")
    print("Detected scripts:")
    for script in scripts:
        print(f"- {script.name}")

    print("\nNext: add execution order and robust error handling.")


if __name__ == "__main__":
    main()
