"""Code generation: render IR models via Jinja2 templates into output files."""

import re
from pathlib import Path

from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import select_autoescape

from codegen.models import EventModel


def _upper_snake(value: str) -> str:
    result = re.sub(r"([A-Z])", r"_\1", value).upper().lstrip("_")
    return result


def _make_env() -> Environment:
    env = Environment(
        loader=PackageLoader("codegen", "templates"),
        autoescape=select_autoescape([]),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["upper_snake"] = _upper_snake
    return env


def generate_python(models: list[EventModel], output_path: Path) -> None:
    """Render *models* as a Pydantic v2 Python module at *output_path*."""
    env = _make_env()
    content = env.get_template("pydantic.py.j2").render(models=models)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _ = output_path.write_text(content, encoding="utf-8")


def generate_typescript(models: list[EventModel], output_path: Path) -> None:
    """Render *models* as a Zod/TypeScript module at *output_path*."""
    env = _make_env()
    content = env.get_template("zod.ts.j2").render(models=models)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _ = output_path.write_text(content, encoding="utf-8")
