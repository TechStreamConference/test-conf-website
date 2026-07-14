import json
import os
import tempfile
from pathlib import Path
from typing import Final

from backend.main import app

if __name__ == "__main__":
    base_dir: Final = Path(os.environ.get("CI_TMP_DIR", tempfile.gettempdir()))
    output_file: Final = Path(base_dir / "backend" / "openapi.json")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    _ = output_file.write_text(
        json.dumps(app.openapi(), indent=2),
        encoding="utf-8",
    )

    print(output_file, " generated")
