import re
import typing
from pathlib import Path
from typing import Final

import pytest
from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute

from backend.config import Settings
from backend.routes import v1_api

_ENV_EXAMPLE_FILE = Path(__file__).resolve().parents[3] / ".env.example"

# Framework response classes carry no generated client model, so the versioning
# rule cannot apply to them. Matched by identity so that a same-named local class
# does not slip through.
_EXEMPT_RESPONSE_TYPES = frozenset[type]({RedirectResponse})


def _collect_routes(router: APIRouter) -> list[APIRoute]:
    """Recursively collect all APIRoute objects from a router and its included sub-routers."""
    result: Final[list[APIRoute]] = []
    for item in router.routes:
        if isinstance(item, APIRoute):
            result.append(item)
        elif hasattr(item, "include_context"):
            result.extend(_collect_routes(item.include_context.included_router))  # type: ignore[unknownMemberType, unknownArgumentType]
    return result


@pytest.fixture(scope="module")
def api_routes() -> list[APIRoute]:
    # If another API version is added, we can also collect those here.
    return _collect_routes(v1_api.ROUTER)


def test_all_endpoints_have_versioned_operation_id(api_routes: list[APIRoute]) -> None:
    assert len(api_routes) > 0

    for route in api_routes:
        assert route.operation_id is not None, f"Endpoint '{route.path}' has no operation_id defined"
        assert re.search(r"v\d+$", route.operation_id) is not None, (
            f"Endpoint '{route.path}' has `operation_id` '{route.operation_id}' which does not end with 'v<digits>'"
        )


def test_all_response_model_types_are_versioned(api_routes: list[APIRoute]) -> None:
    assert len(api_routes) > 0

    collected: Final[list[tuple[str, type]]] = []
    for route in api_routes:
        hints = typing.get_type_hints(route.endpoint)
        return_type = hints.get("return")
        assert return_type is not None, f"Endpoint '{route.path}' has no return type annotation"
        collected.append((route.path, return_type))

        for response_info in route.responses.values():
            model = response_info.get("model")
            assert model is not None, f"Endpoint '{route.path}' has a response without a model defined"
            collected.append((route.path, model))

    for path, model_type in collected:
        if any(model_type is exempt for exempt in _EXEMPT_RESPONSE_TYPES):
            continue

        type_name = getattr(model_type, "__name__", None) or str(model_type)
        assert re.search(r"V\d+$", type_name) is not None, (
            f"Response model type '{type_name}' on endpoint '{path}' does not end with 'V<digits>'"
        )


def test_env_example_satisfies_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    # CI seeds its `.env` by copying `.env.example`, so the example file has to
    # provide every mandatory setting.
    for field_name in Settings.model_fields:
        monkeypatch.delenv(field_name.upper(), raising=False)
        monkeypatch.delenv(field_name.lower(), raising=False)

    assert _ENV_EXAMPLE_FILE.is_file(), f"'{_ENV_EXAMPLE_FILE}' does not exist"

    Settings(_env_file=_ENV_EXAMPLE_FILE)  # type: ignore[reportCallIssue]
