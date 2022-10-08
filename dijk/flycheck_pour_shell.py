# -*- coding:utf-8 -*-
from importlib import reload
from pprint import pprint
import osmnx

from django.db import close_old_connections

import dijk.models as mo
import dijk.views as v

from progs_python.initialisation.initialisation import charge_fichier_cycla_défaut as charge_cycla_defaut, charge_ville, charge_villes, charge_zone
from progs_python.utils import lecture_tous_les_chemins, réinit_cycla

osmnx.config(use_cache=True, log_console=True)

print("""
- charge_villes() Pour charger les données INSEE des villes de France.
- charge_ville(nom:str, code_postal:int, zone:str) pour charger une ville dans la base et l’associer à la zone indiquée.
- charge_zone(liste_villes: list[str*int], zone:str, ville_defaut:str ) idem mais avec une *liste* de (ville, code_postal)

""")
