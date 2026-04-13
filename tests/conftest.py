"""Keep scoring weights at baseline between tests."""

import pytest

from src.recommender import configure_scoring_baseline


@pytest.fixture(autouse=True)
def _reset_scoring_weights() -> None:
    configure_scoring_baseline()
    yield
    configure_scoring_baseline()
