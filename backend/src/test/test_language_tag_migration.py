import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2] / "alembic" / "versions" / "33bb3322c275_normalize_display_language_tags.py"
)

# Normalizing a normalized tag changes it again, which the installed langcodes does not do for any known tag.
_NORMALIZED_TAGS = {"a": "b", "b": "c"}


@pytest.fixture
def migration(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    spec: Final = importlib.util.spec_from_file_location("normalize_display_language_tags", _MIGRATION_PATH)
    assert spec is not None
    assert spec.loader is not None
    module: Final = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "normalize_tag", _NORMALIZED_TAGS.__getitem__)
    return module


def test_plan_tag_updates_rejects_rewriting_a_tag_to_another_rewritten_tag(migration: ModuleType) -> None:
    plan_tag_updates: Final = migration.plan_tag_updates
    assert callable(plan_tag_updates)

    with pytest.raises(
        RuntimeError,
        match=r"static_pages: language tag 'a' for 'IMPRINT' normalizes to 'b', which is normalized differently itself",
    ):
        _ = plan_tag_updates("static_pages", [("IMPRINT", "a"), ("IMPRINT", "b")])


def test_plan_tag_updates_rewrites_the_tags_of_different_owners_independently(migration: ModuleType) -> None:
    plan_tag_updates: Final = migration.plan_tag_updates
    assert callable(plan_tag_updates)

    updates: Final = plan_tag_updates("event_translations", [(1, "a"), (2, "b")])

    # `TagUpdate` is a named tuple, so it equals a plain tuple of its fields.
    assert updates == [(1, "a", "b"), (2, "b", "c")]
