import argparse
import json
from pathlib import Path
from typing import Final

from backend.main import app


def main() -> None:
    parser: Final = argparse.ArgumentParser(description="Generate the OpenAPI specification.")

    _ = parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output file path.",
        required=True,
    )

    args: Final = parser.parse_args()

    if args.output.suffix == "":
        parser.error("Output must include a filename, e.g. openapi.json")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    _ = args.output.write_text(
        json.dumps(app.openapi(), indent=2),
        encoding="utf-8",
    )

    print(args.output, " generated")


if __name__ == "__main__":
    main()
