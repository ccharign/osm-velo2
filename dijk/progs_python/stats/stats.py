# -*- coding:utf-8 -*-
"""
 Ce module n’est pas vraiemnt lié à l’appli. Il contient des fonctions de statistiques sur openstreetmap.
"""
import networkx as nx
import osmnx

def arêtes(g):
    """
    Entrée : g (nx.multidigraph)
    Itérateur sur les arêtes de g
    """
    for s in g.nodes:
        for arêtes in g[s].values():
            for a in arêtes.values():
                yield a


def pourcentage_piéton_et_pistes_cyclables(ville, bavard=0):
    """
    Sortie (float*float*float) : Pourcentage de ways marqués :
       - « pedestrian »
       - « footway > ou « step »
       - « cycleway »
    """
    print("Récupération du graphe")
    g = osmnx.graph_from_place(ville)
    l_piéton, l_pc, l_tot = 0., 0., 0.
    ch_piéton = 0.

    print("Lecture des arêtes")
    for a in arêtes(g):
        longueur = a["length"]
        if "highway" in a:
            l_tot += longueur
            if a["highway"] in ["pedestrian"]:
                l_piéton += longueur
            elif a["highway"] in ["footway", "steps"]:
                ch_piéton += longueur
            elif a["highway"] == "cycleway":
                l_pc+=longueur
    return round(l_piéton/l_tot*100, 1), round(ch_piéton/l_tot*100, 1), round(l_pc/l_tot*100, 1)





def graphe_communes(chemin):
    """
    Sommets : communes
    Arêtes : communes voisines
    """
    pass
