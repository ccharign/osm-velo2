# -*- coding:utf-8 -*-
"""
Fonctions permettant de remplir la base.
Ce module ne sera pas chargé lors d’une utilisation de routine de l’appli. Il utilise la bibliotèque osmnx qui est longue à charger.
"""

from .initialisation import charge_ville, charge_villes
from .initialisation import charge_zone
