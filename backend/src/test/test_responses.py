import inspect
import sys
from typing import Final

import pytest

from backend.models import responses
from backend.models.responses import ApiResponseModel


def _response_models() -> list[type]:
    module: Final = sys.modules[responses.__name__]
    return [
        obj
        for _, obj in inspect.getmembers(module, inspect.isclass)
        if obj is not ApiResponseModel and obj.__module__ == module.__name__
    ]


@pytest.mark.parametrize("model", _response_models(), ids=lambda m: m.__name__)
def test_response_model_uses_camel_case(model: type) -> None:
    assert issubclass(model, ApiResponseModel), f"{model.__name__} must inherit from ApiResponseModel"

    generator: Final = model.model_config.get("alias_generator")
    assert callable(generator)
    assert generator("some_field_name") == "someFieldName"
