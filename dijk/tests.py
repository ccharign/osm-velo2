from functools import reduce
from pprint import pprint
from time import perf_counter


from django.test import TestCase
from django.test import Client

import dijk.pour_shell as sh
import dijk.progs_python.dijkstra as dijkstra

import dijk.models as mo
import dijk.progs_python.recup_donnees as rd
from dijk.progs_python.graphe_base import Graphe
import dijk.progs_python.petites_fonctions as pf

gre = mo.Ville.objects.get(nom_complet="Grenoble")
pau = mo.Ville.objects.get(nom_complet="Pau")
pauz = mo.Zone.objects.get(nom="Pau")
pag = mo.Zone.objects.get(nom="Pau_agglo")
ousse = mo.Ville.objects.get(nom_complet="Ousse")



print("Chargement des zones")




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
            vérifUnArbre(a.ancètre())



def testChemins():
    """
    Vérifie que la lecture de chaque chemin de la base fonctionne.
    """
    raise NotImplementedError()




##############################
##### Profiling #####
##############################


# dico nom_zone -> liste des nom_norm des rues à tester
# Attention : ne mettre que des rues de nom_norm unique
RUES_À_TESTER = {
    "Pau_agglo": ["ρ veroniques", "ρ dou barthouil", "ρ castetnau", "passage louis sallenave"]
}

# id_osm de sommets
SOMMETS_À_TESTER = {
    "Pau_agglo": [286807996,    # Sallenave
                  459812763,    # Véroniques
                  2361682557,   # Barthouil
                  339803913     # Cartetnau
                  ]
}

def chronoDijkstra(g: Graphe, bavard=1):
    print("Chrono des iti_étapes_ensembles")
    tic0 = perf_counter()
    for z_t, rues_t in RUES_À_TESTER.items():
        z_d = g.charge_zone(z_t)
        rues = [mo.Rue.objects.get(nom_norm=nom) for nom in rues_t]
        étapes_rues = [sh.ch.ÉtapeAdresse.of_rue(r) for r in rues]


        for (s, t) in pf.paires(étapes_rues):
            c = sh.ch.Chemin(z_d, [s, t], [], 0.2, "black", False, interdites={}, texte_interdites="")
            tic = perf_counter()
            dijkstra.iti_étapes_ensembles(g, c, bavard=bavard-1)
            print(f"\n{s}->{t}: {perf_counter()-tic}\n")
    print(f"Temps total : {perf_counter()-tic0}")

    
    print("chrono de dijkstra.itinéraire")
    tic0 = perf_counter()
    for z_t, rues_t in RUES_À_TESTER.items():
        z_d = g.charge_zone(z_t)

        for (s, t) in pf.paires(SOMMETS_À_TESTER):
            tic = perf_counter()
            dijkstra.itinéraire(g, s, t, .2, bavard=bavard-1)
            print(f"\n{s}->{t}: {perf_counter()-tic}\n")
    print(f"Temps total : {perf_counter()-tic0}")







# Les tests ci-dessous sont automatiquement lancés avec python manage.py test
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
        self.assertEqual(réponse.status_code, 200)
