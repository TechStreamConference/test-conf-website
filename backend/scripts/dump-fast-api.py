import argparse
import json
from pathlib import Path
from typing import Final

from backend.main import app

if __name__ == "__main__":
    parser: Final = argparse.ArgumentParser()
    _ = parser.add_argument("-o", "--output-file", type=Path, required=True)
    _ = parser.add_argument("-g", "--generate-directory", action="store_true")
    args: Final = parser.parse_args()

    if args.generate_directory:
        args.output_file.parent.mkdir(parents=True, exist_ok=True)

    args.output_file.write_text(
        json.dumps(app.openapi(), indent=2),
        encoding="utf-8",
    )

    print(args.output_file, " generated")
