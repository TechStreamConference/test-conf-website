"""CLI entry point for the log-event code generator.

Usage::

    python -m codegen \\
        --input  /path/to/logging-schema/schema \\
        --python-output  /path/to/backend/src/backend/logging/events.gen.py \\
        --typescript-output  /path/to/frontend/src/lib/logging/events.gen.ts
"""

import argparse
import sys
from pathlib import Path
from typing import Final

from codegen.generator import generate_python
from codegen.generator import generate_typescript
from codegen.parser import parse_schema_dir


def main() -> None:
    parser: Final = argparse.ArgumentParser(
        description="Generate typed log event models from JSON Schema."
    )
    _ = parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Directory containing the JSON Schema files emitted by TypeSpec.",
    )
    _ = parser.add_argument(
        "--python-output",
        type=Path,
        required=True,
        help="Output path for the generated Pydantic v2 Python module.",
    )
    _ = parser.add_argument(
        "--typescript-output",
        type=Path,
        required=True,
        help="Output path for the generated Zod/TypeScript module.",
    )

    args: Final = parser.parse_args()

    if not args.input.is_dir():
        print(f"error: --input '{args.input}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    models = parse_schema_dir(args.input)
    if not models:
        print(f"warning: no JSON Schema files found in '{args.input}'.", file=sys.stderr)

    generate_python(models, args.python_output)
    print(f"Generated Python:     {args.python_output}")

    generate_typescript(models, args.typescript_output)
    print(f"Generated TypeScript: {args.typescript_output}")


if __name__ == "__main__":
    main()
