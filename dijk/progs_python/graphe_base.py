# -*- coding:utf-8 -*-

import abc
from typing import Iterator

from dijk.progs_python.petites_fonctions import distance_euc
import dijk.models as mo


class Graphe(abc.ABC):
    """
    Classe abstraite pour les diverses implémentations d’un graphe.
    """

    @abc.abstractmethod
    def __contains__(self, s: int) -> bool:
        pass
    

    @abc.abstractmethod
    def coords_of_id_osm(self, s: int) -> tuple[float, float]:
        pass

    @abc.abstractmethod
    def __iter__(self) -> Iterator[int]:
        """Itère sur les pk des sommets de <self>."""
    
    def d_euc(self, s: int, t: int) -> float:
        cs, ct = self.coords_of_id_osm(s), self.coords_of_id_osm(t)
        return distance_euc(cs, ct)

    
    @abc.abstractmethod
    def voisins(self, s: int, p_détour: float, interdites={}) -> tuple[tuple[int, float], ...]:
        """
        Renvoie les couples (voisin, longueur ressentie de l'arrête) issus du sommet s."
        """

    @abc.abstractmethod
    def voisins_nus(self, s: int):
        """
        Sortie : liste des voisins de s.
        """

    @abc.abstractmethod
    def sommetOfId_osm(self, s: int) -> mo.Sommet:
        """
        Sortie : Sommet d’id_osm s
        """


    def composantesConnexes(self) -> list[set[int]]:
        """
        Renvoie les composantes connexes de <self>.
        """
        déjà_vus: set[int] = set()

        def parcours(s: int, cc: set[int])-> None:
            déjà_vus.add(s)
            cc.add(s)
            for t in self.voisins_nus(s):
                if t not in déjà_vus:
                    parcours(t)
            

        rés = []
        for s in self:
            if s not in déjà_vus:
                cc = set()
                parcours(s, cc)
                rés.append(cc)

        return rés
