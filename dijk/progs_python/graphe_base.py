# -*- coding:utf-8 -*-

import abc

from dijk.progs_python.petites_fonctions import distance_euc


class Graphe(abc.ABC):
    """
    Classe abstraite pour les diverses implémentations d’un graphe.
    """

    @abc.abstractmethod
    def __contains__(self, s: int):
        pass
    

    @abc.abstractmethod
    def coords_of_id_osm(self, s: int):
        pass

    
    def d_euc(self, s: int, t: int):
        cs, ct = self.coords_of_id_osm(s), self.coords_of_id_osm(t)
        return distance_euc(cs, ct)

    
    @abc.abstractmethod
    def voisins(self, s: int, p_détour: float, interdites={}):
        """
        Renvoie les couples (voisin, longueur ressentie de l'arrête) issus du sommet s."
        """

    @abc.abstractmethod
    def voisins_nus(self, s: int):
        """
        Sortie : liste des voisins de s.
        """

