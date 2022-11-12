# -*- coding:utf-8 -*-
from importlib import reload
from pprint import pprint
import osmnx

from django.db import close_old_connections

import dijk.models as mo
import dijk.views as v

import progs_python.initialisation.initialisation as ini
from progs_python.initialisation.initialisation import charge_fichier_cycla_défaut as charge_cycla_defaut, ajoute_ville, charge_villes, crée_zone
import progs_python.utils as utils
import progs_python.initialisation.amenities as amen
from progs_python.utils import lecture_tous_les_chemins, réinit_cycla
from progs_python.initialisation.amenities import ajoute_ville_et_rue_manquantes

#osmnx.config(use_cache=True, log_console=True)
osmnx.settings.use_cache = True
osmnx.settings.log_console = True

def entraine_tout():
    """
    Lance la lecture de tous les chemins de la base.
    """
    for z_d in mo.Zone.objects.all():
        v.g.charge_zone(z_d.nom)
    lecture_tous_les_chemins(v.g)


def mise_à_jour():
    """
    Lance l’entraînement et met à jour les lieux de toutes les zones de la base.
    """
    print("Chargement de toutes les zones:\n")
    for z in mo.Zone.objects.all():
        v.g.charge_zone(z.nom)

    print("Entraînement:\n")
    utils.lecture_tous_les_chemins(v.g)

    print("Chargement des lieux:")
    villes = mo.Ville.objects.filter(données_présentes=True)
    for ville in villes:
        amen.charge_lieux_of_ville(ville)

    print("fini!\n")



print("""
- charge_villes()  (attention au s !) pour charger les données INSEE des villes de France.
- ajoute_ville(nom:str, code_postal:int, zone:str) pour ajuter une ville à la zone indiquée.
- crée_zone(liste_villes: list[str*int], zone:str) initialise une zone avec une *liste* de (ville, code_postal)

Dans les deux fonctions ci-dessus, les codes postaux ne servent que si le nom est ambigü.

- entraine_tout() pour lancer l’apprentissage à l’aide de tous les chemins de la base.
- mise_à_jour() pour lancer l’apprentissage et mettre à jour les lieux.
""")
