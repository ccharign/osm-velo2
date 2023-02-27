
from importlib import reload
from functools import reduce
from pprint import pprint


from django.test import TestCase
from django.test import Client
from django.db import close_old_connections

from dijk.pour_shell import mo

import dijk.progs_python.initialisation.amenities as amen
import dijk.progs_python.initialisation as ini
from dijk.progs_python.initialisation.communes import charge_villes
from dijk.progs_python.initialisation.initialisation import À_RAJOUTER_PAU, crée_zone, ZONE_GRENOBLE, charge_ville

import dijk.progs_python.utils as utils

import dijk.models as mo
import dijk.views as v
import dijk.progs_python.initialisation.communes as communes

import dijk.progs_python.recup_donnees as rd


gre = mo.Ville.objects.get(nom_complet="Grenoble")
pau = mo.Ville.objects.get(nom_complet="Pau")
pauz = mo.Zone.objects.get(nom="Pau")
pag = mo.Zone.objects.get(nom="Pau_agglo")
ousse = mo.Ville.objects.get(nom_complet="Ousse")


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

def arêtesSortant(g, ens_sommet):
    """
    Entrées:
        g : graphe networkx
        ens_sommet : ensemble de sommets d’icelui
    Sortie:
        liste des arêtes dont le départ est dans ens_sommet mais pas l’arrivée.
    """
    res = []
    for s in ens_sommet:
        res.extend([(t, la) for t, la in g[s].items if t not in ens_sommet])
    return res


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



class TestVues(TestCase):
    def test_statut_réponses(self):
        c = Client()
        
        ## page d’index
        réponse = c.get('/')
        self.assertEqual(réponse.status_code, 200)
        pprint(réponse.status_code)


        ## page cartes cycla
        réponse = c.get('/cycla/')
        self.assertEqual(réponse.status_code, 200)

        ## carte cycla de Pau
        réponse = c.get('/cycla/', {"zone": 72, "force_calcul": "on"})
        #pprint(réponse.context)
        self.assertEqual(réponse.status_code, 200)
