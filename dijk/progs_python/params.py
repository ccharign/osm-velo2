# -*- coding:utf-8 -*-

from datetime import datetime
import os
import sys
sys.path.append("dijk/progs_python")
sys.path.append("dijk/")

### Choix de la zone géographique

BBOX_DÉFAUT = (43.2671, -0.45, 43.3403, -0.2541)  # la bbox de la zone prise en charge # Convention overpass : sud, ouest, nord, est
STR_VILLE_DÉFAUT = "64000 Pau"  # Lorsque la ville n'est pas précisée par l'utilisateur
PAYS_DÉFAUT = "France"
TOUTES_LES_VILLES = {
    "Gelos": 64110,
    "Lée": 64320,
    "Pau": 64000,
    "Lescar": 64230,
    "Billère": 64140,
    "Jurançon": 64110,
    "Ousse": 64320,
    "Idron": 64320,
    "Lons": 64140,
    "Bizanos": 64320,
    "Artigueloutan": 64420,
    "Mazères-Lezons": 64110
}



### Adresses des fichiers de données ###

RACINE_PROJET = "dijk/"

DONNÉES = os.path.join(RACINE_PROJET, "données/")
TMP = os.path.join(RACINE_PROJET, "tmp/")
os.makedirs(TMP, exist_ok=True)
os.makedirs(DONNÉES, exist_ok=True)

# CHEMIN_XML = os.path.join(DONNÉES, "voies_et_nœuds.osm")  # Adresse du fichier .osm élagué utilisé pour chercher les nœuds d'une rue.
#CHEMIN_XML_COMPLET = os.path.join(TMP,"pau_agglo.osm") # le .osm complet. Mis dans TMP pour ne pas être transféré sur github. # Ne devrait plus servir : seul le script initialisation.py crée et manipule le fichier

#CHEMIN_RUE_NUM_COORDS = os.path.join(DONNÉES,"rue_num_coords.csv")
#CHEMIN_NŒUDS_VILLES = os.path.join(DONNÉES,"nœuds_villes.csv")
#CHEMIN_NŒUDS_RUES = os.path.join(DONNÉES,"nœuds_rues.csv")
#CHEMIN_CACHE = os.path.join(DONNÉES,"cache_adresses.csv")
#CHEMIN_CYCLA = os.path.join(DONNÉES,"Cyclabilité.csv")
#CHEMIN_CHEMINS = os.path.join(DONNÉES,"chemins.csv")
#CHEMIN_VILLES_OF_NŒUDS = os.path.join(DONNÉES, "villes_of_nœud.csv")

# Création des csv vides s’il n’existent pas déjà:
# for f in (CHEMIN_RUE_NUM_COORDS, CHEMIN_NŒUDS_VILLES, CHEMIN_NŒUDS_RUES, CHEMIN_CACHE, CHEMIN_CHEMINS):
#     if not os.path.exists(f):
#         x=open(f,"w")
#         x.close()


### Réglages divers ###



D_MAX_POUR_NŒUD_LE_PLUS_PROCHE = 500  # en mètres



### logs ###


os.makedirs(os.path.join(RACINE_PROJET, "log"), exist_ok=True)

DÉCALAGE_MAX = 10
def LOG(msg, type_de_log="divers", bavard=1, affiche=True):
    """
    """
    if bavard > 0:
        f = open(os.path.join(RACINE_PROJET,f"log/{type_de_log}.log"), "a", encoding="utf-8")
        décalage = 2*(max(DÉCALAGE_MAX-bavard, 0))*" "
        f.write(f"{décalage}{datetime.now()}  {msg}\n")
        f.close()
        if affiche:
            print(f"{décalage} {msg}\n")

LOG_PB = lambda m, bavard=1: LOG(m, "pb", bavard=bavard)
