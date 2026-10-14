import inspect
import re
import sys
import typing
from collections import defaultdict
from pathlib import Path
from typing import Final

import pytest
from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel

from backend.config import Settings
from backend.models import responses
from backend.models.responses import ApiResponseModel
from backend.routes import v1_api

_ENV_EXAMPLE_FILE = Path(__file__).resolve().parents[3] / ".env.example"

_CAMEL_CASE_PATTERN = re.compile(r"[a-z][a-zA-Z0-9]*")

# Framework response classes carry no generated client model, so the versioning
# rule cannot apply to them. Matched by identity so that a same-named local class
# does not slip through. `NoneType` is a 204 No Content endpoint: it has no
# response body and therefore no generated client model either.
_EXEMPT_RESPONSE_TYPES = frozenset[type]({RedirectResponse, type(None)})


def _collect_routes(router: APIRouter) -> list[APIRoute]:
    """Recursively collect all APIRoute objects from a router and its included sub-routers."""
    result: Final[list[APIRoute]] = []
    for item in router.routes:
        if isinstance(item, APIRoute):
            result.append(item)
        elif hasattr(item, "include_context"):
            result.extend(_collect_routes(item.include_context.included_router))  # type: ignore[unknownMemberType, unknownArgumentType]
    return result


def _response_models() -> list[type]:
    module: Final = sys.modules[responses.__name__]
    return [
        obj
        for _, obj in inspect.getmembers(module, inspect.isclass)
        if obj is not ApiResponseModel and obj.__module__ == module.__name__
    ]


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


def test_operation_ids_are_unique(api_routes: list[APIRoute]) -> None:
    # The operation ID determines the function name in the auto-generated
    # frontend API client, so duplicates would produce clashing client functions.
    assert len(api_routes) > 0

    paths_by_operation_id: Final[dict[str, list[str]]] = defaultdict(list)
    for route in api_routes:
        assert route.operation_id is not None, f"Endpoint '{route.path}' has no operation_id defined"
        paths_by_operation_id[route.operation_id].append(route.path)

    duplicates: Final = {operation_id: paths for operation_id, paths in paths_by_operation_id.items() if len(paths) > 1}
    assert not duplicates, f"Operation IDs are used by multiple endpoints: {duplicates}"


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


@pytest.mark.parametrize("model", _response_models(), ids=lambda m: m.__name__)
def test_response_model_names_are_versioned(model: type) -> None:
    assert re.search(r"V\d+$", model.__name__) is not None, (
        f"Response model type '{model.__name__}' does not end with 'V<digits>'"
    )


@pytest.mark.parametrize("model", _response_models(), ids=lambda m: m.__name__)
def test_response_model_inherits_from_api_response_model(model: type) -> None:
    assert issubclass(model, ApiResponseModel), f"{model.__name__} must inherit from ApiResponseModel"


@pytest.mark.parametrize("model", _response_models(), ids=lambda m: m.__name__)
def test_response_model_field_names_are_camel_case(model: type) -> None:
    assert issubclass(model, BaseModel), f"{model.__name__} must be a Pydantic model"

    # Test the generator with a sample field name.
    generator: Final = model.model_config.get("alias_generator")
    assert callable(generator)
    assert generator("some_field_name") == "someFieldName"

    # Check the actual field names.
    schema: Final = model.model_json_schema(mode="serialization")
    for field_name in schema.get("properties", {}):
        assert _CAMEL_CASE_PATTERN.fullmatch(field_name) is not None, (
            f"Field '{field_name}' of {model.__name__} is not camelCase"
        )


def test_env_example_satisfies_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    # CI seeds its `.env` by copying `.env.example`, so the example file has to
    # provide every mandatory setting.
    for field_name in Settings.model_fields:
        monkeypatch.delenv(field_name.upper(), raising=False)
        monkeypatch.delenv(field_name.lower(), raising=False)

    assert _ENV_EXAMPLE_FILE.is_file(), f"'{_ENV_EXAMPLE_FILE}' does not exist"

    Settings(_env_file=_ENV_EXAMPLE_FILE)  # type: ignore[reportCallIssue]
