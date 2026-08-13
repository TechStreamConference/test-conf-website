from typing import Final

import pytest

pytestmark: Final = pytest.mark.integration


def test_backend_is_reachable(backend_is_reachable: bool) -> None:
    # `just up` is a bit overkill because it starts the database server and nginx,
    # while only nginx is needed here. It is still the simplest and most convenient
    # way for developers to start the required infrastructure.
    assert backend_is_reachable, "The backend is not reachable. Did you forget to run `just up` and `just run`?"
