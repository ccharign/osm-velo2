import pytest

from dijk.progs_python.graphe_par_django import Graphe_django

@pytest.mark.parametrize("zone_str", ["Voiron_agglo"])
def testeConnexité(g: Graphe_django, zone_str: str):
    g.charge_zone(zone_str)
    ccs = g.composantesConnexes()
    breakpoint()
