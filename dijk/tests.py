from django.test import TestCase
from importlib import reload
from functools import reduce
from pprint import pprint

import dijk.pour_shell as sh

import dijk.progs_python.initialisation.amenities as amen
from dijk.progs_python.initialisation.communes import charge_villes
from dijk.progs_python.initialisation.initialisation import À_RAJOUTER_PAU, crée_zone, ZONE_GRENOBLE, charge_ville

import dijk.progs_python.utils as utils

from django.db import close_old_connections

import dijk.models as mo
import dijk.views as v
import dijk.progs_python.initialisation.communes as communes

import dijk.progs_python.recup_donnees as rd

gre = sh.mo.Ville.objects.get(nom_complet="Grenoble")
pau = sh.mo.Ville.objects.get(nom_complet="Pau")
pag = sh.mo.Zone.objects.get(nom="Pau_agglo")
ousse = sh.mo.Ville.objects.get(nom_complet="Ousse")


# Create your tests here.

    
def test_data_gouv(nb=5):
    """
    Teste adresses_of_liste_lieux sur les nb premiers lieux de la base.
    """
    ll = mo.Lieu.objects.all()[:nb]
    pprint(ll)
    rés = rd.adresses_of_liste_lieux(ll, bavard=2, affiche=True)
    for l, r in zip(ll, rés):
        if "result_housenumber" not in r:
            print(f"Pas de result_housenumber pour {l}\n Données reçues :\n{r}")
    return rés


def sommetsdéconnectés(g):

    départ = list(g.dico_Sommet.keys())[1000]
    vu = set((départ,))
    àVisiter = [départ]

    while àVisiter:
        s = àVisiter.pop()
        vu.add(s)
        for t, _ in g.dico_voisins[s]:
            if t not in vu:
                àVisiter.append(t)
    
    pas_vus = [t for t in g.dico_Sommet.keys() if t not in vu]
    return pas_vus


def nomsDesDéconnectés(g):
    déconnectés = sommetsdéconnectés(g)
    arêtes_déconnectées = reduce(
        lambda a, b: a+b,
        [g.dico_voisins[s] for s in déconnectés if g.dico_voisins[s]],
        []
    )
    return arêtes_déconnectées


def lieuxSansArête():
    return mo.Lieu.objects.filter(arête=None)

