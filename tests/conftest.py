import pytest

from dijk.progs_python.graphe_par_django import Graphe_django



@pytest.fixture
def g() -> Graphe_django:
    return Graphe_django()
