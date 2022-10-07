# -*- coding:utf-8 -*-


#################### Rajoter la ville aux données des nœuds ####################


import overpy
from params import CHEMIN_NŒUDS_VILLES, CHEMIN_VILLES_OF_NŒUDS
from petites_fonctions import ajouteDico
from lecture_adresse.normalisation import normalise_ville, TOUTES_LES_VILLES
import osmnx as ox



def liste_villes():
    """ Liste des villes apparaissant dans TOUTES_LES_VILLES."""
    return (normalise_ville(n) for n in TOUTES_LES_VILLES.keys())




# pour test : id de Pau 162431

# # Trop lent... Récupérer direct le .osm de chaque ville ?
# def nœuds_ville(ville):
#     """ Renvoie la liste des nœeud de ville.
#     Utilise Nominatim pour trouver la relation qui décrit la ville puis overpass pour le résultat final.
#     Semble extrêmement lent !
#     """
#     r = localisateur.geocode({"city":ville, "country":"France"}).raw
#     assert r["osm_type"] == "relation"
#     id_ville = r["osm_id"]
#     api = overpy.Overpass()
#     r = api.query(f"""
#     node(area:{3600000000+id_ville});
#     out ids;
#     """)
#     return r.node_ids


# Deuxième essai : avec osmnx
# Il manque certains nœuds !
# La simplification dans graph_from_place serait plus forte que celle lors de la création du graphe initial dans crée_graphe ?
def nœuds_ville(ville):
    g = ox.graph_from_place({"city":str(ville), "country":"France"}, simplify=False, retain_all=True, network_type="all")
    return g.nodes


## https://stackoverflow.com/questions/58844414/what-is-a-correct-overpass-turbo-query-for-getting-all-streets-in-a-city
#https://overpass-api.de/command_line.html
#wget "https://overpass-api.de/api/interpreter?data=node[name=\"Gielgen\"];out;"
def nœuds_ville2(ville, bavard=0):
    """
    Entrée : ville, instance de Ville
    Sortie : liste des nodes de cette ville
    Cette méthode n’est pas acceptée par overpass...
    """
    #requête = f"""area[name = "{ville}"]; (way(area)[highway]; ); (._;>;); out;"""
    requête = f"""area[name = "{ville.nom_complet}"][boundary=administrative][postal_code={ville.code}]; way(area)[highway]; out;"""
    if bavard>0: print(requête)
    api=overpy.Overpass()
    res=set()
    res_ways = api.query(requête)
    for w in res_ways.ways:
        res.update(w._node_ids)
    return res


def test_overpass(id, bavard=0):
    #requête = f"""area[name = "{ville}"]; (way(area)[highway]; ); (._;>;); out;"""
    requête = f"""area[id = "{id}"]; way(area)[highway][name]; out;"""
    if bavard>0: print(requête)
    api=overpy.Overpass()
    return  api.query(requête)





### Création du csv ###



def crée_csv(g):
    """
    Utilise la fonction liste_villes pour récupérer la liste des villes.
    Ensuite, utilise osmnx pour récupérer les nœuds de chaque ville.

    Crée le csv « ville;liste des nœuds »
    """
    print(f"Enregistrement dans le fichier {CHEMIN_NŒUDS_VILLES}.")
    sortie = open(CHEMIN_NŒUDS_VILLES, "w", encoding="utf-8")
    début=True
    nœuds={}
    #try:
    for ville in liste_villes():
        if str(ville) not in nœuds or len(nœuds[str(ville)])==0:

            if not début :
                print("Pause pour ne pas surcharger overpass")
                début=False
                time.sleep(10)
            print(f"\n\nRecherche des nœuds de {ville}")
            nœuds[str(ville)] = [n for n in nœuds_ville(ville) if n in g.digraphe.nodes ]
        else:
            print(f"J’avais déjà {len(nœuds[str(ville)])} nœuds pour {ville}.")
        sortie.write( str(ville) + ";" + ",".join(map(str, nœuds[str(ville)] )) + "\n")
    sortie.close()
    #except Exception as e:
    #    print(e)
    #    return nœuds


def charge_csv():
    """ Renvoie le dico ville -> nœuds d’icelle"""
    res = {}
    with open(CHEMIN_NŒUDS_VILLES, encoding="utf-8") as entrée:
        for ligne in entrée:
            ville, suite = ligne.strip().split(";")
            nœuds = tuple(map(int, suite.split(",")))
            res[ville] = nœuds
    return res


def vérif_unicité_ville():
    """
    La réponse était False comme on pouvait s’en douter : certains nœuds sont dans plusieurs villes.
    """
    déjà_vus = set([])
    for ville, nœuds in charge_csv().items():
        for n in nœuds:
            if n in déjà_vus:
                return False
        déjà_vus.update(nœuds)
    return True


def crée_csv_villes_of_nœuds(g, bavard=0):
    """
    Charge le csv CHEMIN_NŒUDS_VILLES qui donne les nœuds de chaque ville, et crée un csv CHEMIN_VILLES_OF_NŒUDS qui donne les villes de chaque nœud.
    """
    compte=0
    d={} # dico nœud -> liste des villes
    with open(CHEMIN_NŒUDS_VILLES, encoding="utf-8") as entrée:
        for ligne in entrée:
            ville, suite = ligne.strip().split(";")
            nœuds = map(int, suite.split(","))
            for n in nœuds:
                if n in g:# devrait devenir inutile dès que le csv CHEMIN_NŒUDS_VILLES aura été proprement fait
                    ajouteDico( d, n, ville )
                    compte+=1
    if bavard>0:
        print(f"{compte} noms de ville ajoutés")

    with open(CHEMIN_VILLES_OF_NŒUDS, "w") as sortie:
        for n, villes in d.items():
            sortie.write(f"{n};{','.join(villes)}\n")



def ajoute_villes(g, bavard=0):
    """ 
    Remplit le dictionnaire g.villes_of_nœud
    """
    with open(CHEMIN_VILLES_OF_NŒUDS) as entrée:
        for ligne in entrée:
            n_t, villes_t = ligne.strip().split(";")
            n=int(n_t)
            villes = villes_t.split(",")
            g.villes_of_nœud[n]=villes
    
