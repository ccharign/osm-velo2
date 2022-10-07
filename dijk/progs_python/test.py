#!usr/bin/python3
# -*- coding:utf-8 -*-


## Peut être exécuté directement hors de Django pour tests


from importlib import reload  # recharger un module après modif
import networkx as nx  # graphe
import os
if os.path.split(os.getcwd())[1]=="osm vélo":
    os.chdir("site_velo/") # Depuis emacs je suis dans le dossier osm-vélo, celui qui contient le .git
import dijk.progs_python.params
from init_graphe import charge_graphe  # le graphe de Pau par défaut
import apprentissage
import dijkstra
import chemins  # classe chemin et lecture du csv
#import initialisation.nœuds_des_rues as nr
#import lecture_adresse.arbresLex as lex
from lecture_adresse.normalisation import normalise_rue, VILLE_DÉFAUT, Adresse, ARBRE_DES_RUES
import utils
import petites_fonctions
import recup_donnees
g = charge_graphe(bavard=2)
#nr.sortie_csv(g)
from initialisation.ajoute_villes import ajoute_villes, crée_csv_villes_of_nœuds
#ajoute_villes(g)
from initialisation.noeuds_des_rues import sortie_csv



# arêtes_barbanègre= chemins.arêtes_interdites(g, ["boulevard barbanègre"])
# c = chemins.Chemin([chemins.Étape("rue des véroniques", g), chemins.Étape("place royale", g) ], .4, False, interdites=arêtes_barbanègre)
# iti, l_ressentie = dijkstra.chemin_étapes_ensembles(g, c, bavard=3)


# apprentissage.n_lectures(3, g, [c], bavard=3)

# c_sans_contrairte = chemins.Chemin([chemins.Étape("rue des véroniques", g), chemins.Étape("place royale", g) ], .4, False)
# iti2,_ = dijkstra.chemin_étapes_ensembles(g, c_sans_contrairte , bavard=3)

# list(zip(iti,iti2))
# g.sauv_cycla()

# tous_les_chemins = chemins.chemins_of_csv(g, bavard=1)
# len(tous_les_chemins)


# def ajoute_chemin(étapes, AR=True, pourcentage_détour=30):
#     c = chemins.Chemin.of_étapes(étapes, pourcentage_détour, AR, g)
#     utils.dessine_chemin(c, g, ouvrir=True)
#     confirme = input("Est-ce-que le chemin est correct ? (O/n)")
#     if confirme in ["","o","O"]:
#         tous_les_chemins.append(c)
    
    


# ajoute_chemin( ["lycée Louis Barthou", "rue Lamothe", "rue Jean Monnet", "rue Galos", "place de la république"], True, 20)
# ajoute_chemin(["rue des véroniques", "rue sambre et meuse", "avenue bié-moulié","avenue des acacias", "boulevard barbanègre"], True, 30)

# tous_les_chemins = utils.cheminsValides(tous_les_chemins, g)
# len(tous_les_chemins)



# def affiche_texte_chemins(chemins=tous_les_chemins):
#     for i,c in enumerate(chemins):
#         print(f"{i} : {c}\n")


    
# def affiche_séparément(chemins=tous_les_chemins, g=g):
#     for i, c in enumerate(chemins):
#         print(f"{i} : {c}")
#         utils.dessine_chemin(c, g)
    

# apprentissage.n_lectures(5, g, tous_les_chemins, bavard=0)

# affiche_séparément()

# # vérif de la structure
# for c in tous_les_chemins:
#     for é in c.étapes:
#         try:
#             rien = é.nœuds
#         except Exception as e:
#             print(e)
#             print(c)



