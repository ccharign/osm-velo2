# -*- coding:utf-8 -*-

# Ce module regroupe les fonctions de recherche de données géographiques qui n'utilisent pas osmnx

import geopy, overpy
#import functools
from params import VILLE_DÉFAUT
import xml.etree.ElementTree as xml  # Manipuler le xml local


geopy.geocoders.options.default_user_agent = "pau à vélo"

localisateur = geopy.geocoders.osm.Nominatim(user_agent="pau à vélo")
#geocode = functools.lru_cache(maxsize=128)(functools.partial(localisateur.geocode, timeout=5)) #mémoïzation
api = overpy.Overpass()


class LieuPasTrouvé(Exception):
    pass



# Pour contourner le pb des tronçons manquant dans Nominatim :
# 1) récupérer le nom osm de la rue
# 2) recherche dans le xml local

def cherche_lieu(nom_rue, ville=VILLE_DÉFAUT, pays="France", bavard=0):
    """ Renvoie la liste d'objets geopy enregistrées dans osm pour la rue dont le nom est passé en argument. On peut préciser un numéro dans nom_rue.
    """
    try:
        #Essai 1 : recherche structurée. Ne marche que si l'objet à chercher est effectivement une rue
        if bavard>1:print(f'Essai 1: "street":{nom_rue}, "city":{ville}, "country":{pays}')
        lieu = localisateur.geocode( {"street":nom_rue, "city":ville, "country":pays, "dedup":0}, exactly_one=False, limit=None  ) # Autoriser plusieurs résultats car souvent une rue est découpée en plusieurs tronçons
        if lieu != None:
            return lieu
        else:
            # Essai 2: non structuré. Risque de tomber sur un résultat pas dans la bonne ville.
            LOG_PB(f"La recherche structurée a échouée pour {nom_rue, ville}.")
            print( "Recherche Nominatim non structurée... Attention : résultat pas fiable." )
            print(f'Essai 2 : "{nom_rue}, {ville}, {pays}" ')
            lieu = localisateur.geocode( f"{nom_rue}, {ville}, {pays}", exactly_one=False  )
            if lieu != None:
                return lieu
            else:
                raise LieuPasTrouvé
    except Exception as e:
        print(e)
        LOG_PB(f"{e}\n Lieu non trouvé : {nom_rue} ({ville})")



def tronçons_rassemblés(l):
    """ Entrée : l (int list list), liste de tronçons de rues.
        Sortie : liste obtenue en recollant autant que possible deux tronçons qui se suivent (càd dernier nœud de l’un == premier de l’autre).
    """
    fini = False
    res = l
    à_essayer = l #file d’attente des tronçons à tester
    
    while not fini:
        fini = True
        for t1 in à_essayer :
            t1_changé=False
            if t1 in res : # sinon t1 avait déjà été fusionné
                tmp = []
                for t2 in res :
                    if t2 != t1:
                        if t1[0] == t2[-1]:
                            t1 = t2+t1[1:]
                            fini = False; t1_changé = True
                        elif t1[-1] == t2[0]:
                            t1 = t1+t2[1:]
                            fini = False; t1_changé = True
                        elif t1[0] == t2[0]:
                            t1 = list(reversed(t2)) + t1[1:]
                            fini = False; t1_changé = True
                        elif t1[-1] == t2[-1]:
                            t1 = t1[:-1] + list(reversed(t2))
                        else:
                            tmp.append(t2)
                tmp.append(t1)
                if t1_changé : à_essayer.append(t1)
                # Ici, ∪_{t ∈ tmp} t  == ∪_{t ∈ l} t
                res = tmp
    return res

            
def nœuds_sur_rue(nom_rue, ville=VILLE_DÉFAUT, pays="France", bavard=1):

    res=[]
    
    # Partie 1 avec Nominatim je récupère l'id de la rue
    rue = cherche_lieu(nom_rue, ville=ville, pays=pays, bavard=bavard)
    if bavard:print(rue)
    
    for tronçon in rue : #A priori, cherche_lieu renvoie une liste
        id_rue = tronçon.raw["osm_id"]
        if bavard:print(f"id de {nom_rue} : {id_rue}")
    
        # Partie 2 avec Overpass je récupère les nœuds de cette rue
        
        r = api.query(f"way({id_rue});out;")
        rue = r.ways[0]
        nœuds = rue.get_nodes(resolve_missing=True)
        res.extend([n.id for n in nœuds])
    return res





def infos_nœud(id_nœud):
    r=api.query(f"""
    node({id_nœud});out;
    """)
    return r

def coord_nœud(id_nœud):
    n = api.query(f"""
    node({id_nœud});out;
    """).nodes[0]
    print(n)
    return float(n.lat), float(n.lon)
    

def coords_lieu(nom_rue, ville=64000, pays="France", bavard=0):
    lieu = cherche_lieu(nom_rue, ville=ville, pays=pays, bavard=bavard)[0]
    return lieu.latitude, lieu.longitude

#id_hédas="30845632"
#id_hédas2="37770876"






###################################################
#####          Recherche en local             #####
###################################################


#Plus besoin maintenant que j'utilise directement les données du graphe.
#print(f"Chargement du xml {CHEMIN_XML}")
#root = xml.parse(CHEMIN_XML).getroot()
#print("fini\n")

def nœuds_sur_tronçon_local(id_rue):
    """ Cherche les nœuds d'une rue dans le fichier local. Renvoie la liste des nœuds trouvés (int list).
    """

    for c in root:
        if c.tag == "way" and c.attrib["id"] == str(id_rue) :
            return [int(truc.attrib["ref"]) for truc in c if truc.tag=="nd"]
    return [] #Si rien de trouvé
        

def nœuds_sur_rue_local(nom_rue, ville=VILLE_DÉFAUT, pays="France", bavard=0):
    rue = cherche_lieu(nom_rue, ville=ville, pays=pays, bavard=bavard)
    if bavard:print(rue)
    res = []
    for tronçon in rue : #A priori, cherche_lieu renvoie une liste
        if tronçon.raw["osm_type"] == "node":
            if bavard : print(f"Récupéré directement un nœud osm ({tronçon.raw['osm_id']}) pour {nom_rue} ({ville}). Je renvoie le premier de la liste.")
            return(  [tronçon.raw["osm_id"]] )
        elif tronçon.raw["osm_type"] == "way":
            id_rue = tronçon.raw["osm_id"]
            if bavard: print(f"Je cherche les nœuds de {nom_rue} dans le tronçon {id_rue}.")
            res.append(nœuds_sur_tronçon_local(id_rue))
    nœuds_sur_tronçons = tronçons_rassemblés(res)

    if len(nœuds_sur_tronçons)>1:
        print(f"  -- Je n’ai pas pu rassembler les tronçons pour {nom_rue}. --")
        res = []
        for t in nœuds_sur_tronçons :
            res.extend(t)
            return res
    else:
        return nœuds_sur_tronçons[0]    


def nœuds_of_adresse(adresse, ville=VILLE_DÉFAUT, pays = "France", bavard=0):
    """ Entrée : une adresse, càd au minimum un numéro et un nom de rue.
        Sortie : liste des nœuds osm récupérés via Nominatim.
    """
    pass

def kilométrage_piéton():
    """ Rien à voir : calcul du kilométrage de voies marquées « pedestrian » ou « footway »."""
    res=[]
    for c in root:
        if c.tag=="way":
            for truc in c:
                if truc.tag == "tag" and truc.attrib["k"]=="highway" and truc.attrib["v"] in ["pedestrian", "footway"] :
                    res.append(c)
    for c in res:
        for truc in c:
            if truc.tag == "tag" and truc.attrib["k"]=="name":print(truc.attrib["v"])
#Faire une classe Nœud_OSM pour extraire les tags, les nœuds d'une voie etc
