# -*- coding:utf-8 -*-
"""
Fonctions permettant de remplir la base.
Ce module ne sera pas chargé lors d’une utilisation de routine de l’appli. Il utilise la bibliotèque osmnx qui est longue à charger.
"""

from .initialisation import ajoute_ville
from .initialisation import crée_zone
from .amenities import ajoute_ville_et_rue_manquantes
from .communes import charge_villes
