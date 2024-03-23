import pytest

from src import Node


@pytest.fixture
def alice() -> Node:
    return Node()


@pytest.fixture
def bob() -> Node:
    return Node()


@pytest.fixture
def charlie() -> Node:
    return Node()


@pytest.fixture
def eve() -> Node:
    return Node()


@pytest.fixture
def malice() -> Node:
    return Node()
