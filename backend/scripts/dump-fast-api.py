import argparse
import json
from pathlib import Path

from backend.main import app

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    _ = parser.add_argument("-o", "--output-file", type=Path)
    _ = parser.add_argument("-g", "--generate-directory", action="store_true")
    args = parser.parse_args()

    if args.generate_directory:
        args.output_file.parent.mkdir()

    with open(args.output_file, "w") as f:
        json.dump(app.openapi(), f, indent=2)

    print(args.output_file, " generated")
