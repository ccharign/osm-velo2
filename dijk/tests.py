from functools import reduce
from pprint import pprint


from django.test import TestCase
from django.test import Client

from dijk.pour_shell import *

import dijk.models as mo
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
    """
    Renvoie la liste des sommets non connectés au sommet de départ (arbitrairement le 1000-ième de g).
    """
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
    """
    Sortie : liste des arêtes reliées à un sommet déconnecté de g.
    """
    déconnectés = sommetsdéconnectés(g)
    arêtes_déconnectées = reduce(
        lambda a, b: a+b,
        [g.dico_voisins[s] for s in déconnectés if g.dico_voisins[s]],
        []
    )
    return arêtes_déconnectées


def lieuxSansArête():
    """
    Sortie : queryset des lieux sans arête.
    """
    return mo.Lieu.objects.filter(arête=None)


def structureArbreArête():

    vus = set()                 # sommets déjà vus
    
    def vérifUnArbre(r: mo.ArbreArête):
        """
        Vérifie que toutes les feuilles sont attachées à un unique segment.
        """
        vus.add(r)
        if not r.fils:
            print(f"{r} ne semble pas être une feuille valide! Voici ses segments : {r.segment()}")
            breakpoint()
        for f in r.fils:
            vérifUnArbre(f)

    for a in mo.ArbreArête.objects.all():
        if a not in vus:
            vérifUnArbre(a)


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
