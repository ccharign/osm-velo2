#!/usr/bin/python3
# -*- coding:utf-8 -*-

### À terme devrait être le seul fichier à utiliser osmnx, afin d’éviter de le charger dans les utilisations courantes.

import osmnx as ox
ox.config(use_cache=True, log_console=True)
import sys


def crée_graphe_bbox(nom_fichier, bbox, option={"network_type":"all"}, bavard=1):
    """ 
    nom_fichier : nom du fichier où enregistrer le fichier xml du graphe.
    Effet : création du fichier graphml
    Sortie : le graphe, au format networkx non dirigé
    """
    s,o,n,e = bbox
    g = ox.graph_from_bbox(n, s, e, o, **option)
    
    print("conversion en graphe non orienté")
    g = ox.get_undirected(g)
    
    print(f"Chargement fini. Je l'enregistre pour la prochaine fois dans {nom_fichier}.")
    ox.io.save_graphml(g, nom_fichier)
    
    return g


# Choix de la fonction à utiliser. (J'ai supprimé les autres de toute façon!)
charge_graphe = crée_graphe_bbox

# Pour télécharger une carte avec overpass : wget -O pau.osm "https://overpass.openstreetmap.ru/cgi/xapi_meta?*[bbox=-0.4285,43.2671,-0.2541,43.3403]"
#Agglo : wget -O pau.osm "https://overpass.openstreetmap.ru/cgi/xapi_meta?*[bbox=-0.48,43.26,-0.25,43.35]"
#Ne semble fonctionner que pour des petites zones.

if __name__ == "__main__":
    print(f"\ncrée_graphe.py lancé avec arguments {sys.argv}")
    nom_fichier = sys.argv[1]
    bbox = tuple(map(float, sys.argv[2][1:-1].split(",")))
    print(f"nom_fichier={nom_fichier}, bbox reçue : {bbox}\n")
    crée_graphe_bbox(nom_fichier, bbox)


    
