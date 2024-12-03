"""Fonctions utilitaires pour manipuler des objets géométriques"""

from functools import reduce

from geopandas import GeoDataFrame



def union_de_géoms(géoms: list[GeoDataFrame]) -> GeoDataFrame:
    début = géoms[0]
    return reduce(
        lambda p, q : p.union(q),
        géoms[1:],
        début
    )
