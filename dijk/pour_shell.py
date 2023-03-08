# -*- coding:utf-8 -*-

from importlib import reload
from pprint import pprint
import osmnx

from django.db import close_old_connections

import dijk.models as mo
import dijk.views as v

import dijk.progs_python.initialisation.initialisation as ini
from dijk.progs_python.initialisation.initialisation import charge_fichier_cycla_défaut as charge_cycla_defaut, ajoute_ville, crée_zone
from dijk.progs_python.initialisation.communes import charge_villes
import dijk.progs_python.utils as utils
import dijk.progs_python.recup_donnees as rd
import dijk.progs_python.chemins as ch
from dijk.progs_python.graphe_base import Graphe
import dijk.progs_python.initialisation.amenities as amen
from dijk.progs_python.utils import lecture_tous_les_chemins

osmnx.settings.use_cache = True
osmnx.settings.log_console = True



def chargeToutesLesZones(g: Graphe):
    close_old_connections()
    for z_d in mo.Zone.objects.all():
        g.charge_zone(z_d.nom)
    


def entraine_tout(bavard: int = 2):
    """
    Lance la lecture de tous les chemins de la base.
    """
    assert isinstance(bavard, int)
    chargeToutesLesZones(v.g)
    lecture_tous_les_chemins(v.g, bavard=bavard)


def mise_à_jour():
    """
    Lance l’entraînement et met à jour les lieux de toutes les zones de la base.
    """
    
    for z in mo.Zone.objects.all():
        v.g.charge_zone(z.nom)
        amen.charge_lieux_of_zone(z, force=True, réinit=True)

    print("Entraînement:\n")
    utils.lecture_tous_les_chemins(v.g)

    # print("Chargement des lieux:")
    # villes = mo.Ville.objects.filter(données_présentes=True)
    # for ville in villes:
    #     amen.charge_lieux_of_ville(ville, v.g.arbre_arêtes[v])

    print("fini!\n")



print("""
- charge_villes()  (attention au s !) pour charger les données INSEE des villes de France.
- ajoute_ville(nom:str, code_postal:int, zone:str) pour ajuter une ville à la zone indiquée.
- crée_zone(liste_villes: list[(str, int)], zone:str) initialise une zone avec une *liste* de (ville, code_postal)

Dans les deux fonctions ci-dessus, les codes postaux ne servent que si le nom est ambigü.

- entraine_tout() pour lancer l’apprentissage à l’aide de tous les chemins de la base.
- mise_à_jour() pour lancer l’apprentissage et mettre à jour les lieux.
""")
