import json
import tempfile
from pathlib import Path
from typing import Final

from backend.main import app

if __name__ == "__main__":
    output_file: Final = Path(tempfile.gettempdir()) / "backend" / "openapi.json"

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(app.openapi(), indent=2),
        encoding="utf-8",
    )

    print(output_file, " generated")
