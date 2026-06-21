#!/usr/bin/env python3
import subprocess  # noqa: S404
import sys
from pathlib import Path
from typing import Final

# This script is intended to be invoked via Poe the Poet (`poe`). Python projects
# should include it in their `pyproject.toml` as a task, so that one can run
# `uv run check` or `uv run fix` from the project root.


def _run(cmd: list[str]) -> None:
    print(f"Running: `{' '.join(cmd)}`")
    result = subprocess.run(cmd)  # noqa: S603
    if result.returncode != 0:
        sys.exit(result.returncode)


def _run_uv(args: list[str]) -> None:
    cmd = ["uv", "run", "--active"] + args
    _run(cmd)


def _find_project_root(start: Path) -> Path:
    for path in [start, *start.parents]:
        if (path / "pyproject.toml").exists():
            return path.resolve()
    raise RuntimeError("Could not determine project root.")


def main() -> None:
    args: Final = sys.argv[1:]
    if len(args) == 1 and args[0] == "--test":
        project_root: Final = _find_project_root(Path.cwd())
        cov_config_path: Final = (Path(__file__).parent.parent / ".coveragerc").resolve()
        src_dir: Final = project_root / "src"
        cov_targets: Final = sorted(
            child.name for child in src_dir.iterdir() if child.is_dir() and child.name != "test"
        )

        _run_uv([
            "pytest",
            "src/test/",
            "-v",
            *(f"--cov=src/{target}" for target in cov_targets),
            "--cov-branch",
            "--cov-report=term-missing:skip-covered",
            "--cov-report=html:coverage_html",
            f"--cov-config={cov_config_path}",
            "--cov-fail-under=85",
        ])
        return

    if len(args) > 1 or (args and args[0] != "--fix"):
        print(f"Usage: {args[0]} [--fix]", file=sys.stderr)
        print(args, file=sys.stderr)
        sys.exit(2)

    if "--fix" in args:
        _run_uv(["ruff", "format"])
        _run_uv(["ruff", "check", "--fix"])
        _run_uv(["pyright"])
    else:
        _run_uv(["ruff", "format", "--check"])
        _run_uv(["ruff", "check"])
        _run_uv(["pyright"])


if __name__ == "__main__":
    main()
