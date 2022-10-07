# -*- coding:utf-8 -*-

import os
import json
from pprint import pformat

from django.db import transaction

from dijk.models import Ville, objet_of_dico

from dijk.progs_python.lecture_adresse.normalisation import partie_commune
from dijk.progs_python.lecture_adresse.normalisation0 import int_of_code_insee

from params import RACINE_PROJET


### Données INSEE ###



# def charge_villes(chemin_pop=os.path.join(RACINE_PROJET, "progs_python/stats/docs/densité_communes.csv"),
#                   chemin_géom=os.path.join(RACINE_PROJET, "progs_python/stats/docs/géom_villes.json"),
#                   bavard=0):
#     """
#     Remplit la table des villes à l’aide des deux fichiers insee. (Il manque le code postal.)
#     """
    
#     dico_densité = {"Communes très peu denses":0,
#                     "Communes peu denses":1,
#                     "Communes de densité intermédiaire":2,
#                     "Communes densément peuplées":3
#                     }

#     def géom_vers_texte(g):
#         """
#         Enlève d’éventuelles paires de crochets inutiles avant de tout convertir en une chaîne de (lon, lat) séparées par des ;.
#         """
#         assert isinstance(g, list), f"{g} n’est pas une liste"
#         if len(g)==1:
#             return géom_vers_texte(g[0])
#         elif isinstance(g[0][0], list):
#             nv_g = reduce(lambda x,y : x+y, g, [])
#             return géom_vers_texte(nv_g)
#         else:
#             assert len(g[0])==2, f"{g} n’est pas une liste de couples.\n Sa longueur est {len(g)}"
#             return ";".join(map(
#                 lambda c: ",".join(map(str, c)),
#                 g
#             ))

#     dico_géom = {}  # dico code_insee -> (nom, géom)

#     print(f"Lecture de {chemin_géom} ")
#     with open(chemin_géom) as entrée:
#         données = json.load(entrée)
#         for v in données["features"]:
#             code_insee = int_of_code_insee(v["properties"]["codgeo"])
#             géom = géom_vers_texte(v["geometry"]["coordinates"])
#             nom = v["properties"]["libgeo"].strip().replace("?","'")
#             dico_géom[code_insee] = (nom, géom)
    

#     print(f"Lecture de {chemin_pop}")
#     close_old_connections()
#     with transaction.atomic():
#         with open(chemin_pop) as entrée:
#             à_maj=[]
#             à_créer=[]
#             n=-1
#             entrée.readline()
#             for ligne in entrée:
#                 n+=1
#                 if n % 500 ==0: print(f"{n} lignes traitées")
#                 code_insee, nom, région, densité, population = ligne.strip().split(";")
#                 code_insee = int_of_code_insee(code_insee)
#                 population = int(population.replace(" ",""))
#                 i_densité = dico_densité[densité]
#                 essai = Ville.objects.filter(nom_complet=nom).first()
#                 if code_insee in dico_géom:
#                     nom_dans_géom, géom = dico_géom[code_insee]
#                     if nom!=nom_dans_géom:
#                         print(f"Avertissement : nom différent dans les deux fichiers : {nom_dans_géom} et {nom}")
#                         géom=None
#                 else:
#                     print(f"Avertissement : ville pas présente dans {chemin_géom} : {nom}")
#                     géom = None

#                 if essai:
#                     essai.population=population
#                     essai.code_insee=code_insee
#                     essai.densité=i_densité
#                     essai.géom_texte = géom
#                     à_maj.append(essai)
#                 else:
#                     v_d = Ville(nom_complet=nom,
#                                 nom_norm=partie_commune(nom),
#                                 population=population,
#                                 code_insee=code_insee,
#                                 code=None,
#                                 densité=i_densité,
#                                 géom_texte=géom
#                                 )
#                     à_créer.append(v_d)
#     print(f"Enregistrement des {len(à_maj)} modifs")
#     Ville.objects.bulk_update(à_maj, ["population", "code_insee", "densité"])
#     print(f"Enregistrement des {len(à_créer)} nouvelles villes")
#     Ville.objects.bulk_create(à_créer)


def charge_villes(chemin=os.path.join(RACINE_PROJET, "progs_python/initialisation/données_à_charger/code-postalnettoyé.json")):
    """
    Remplit la table des villes au moyen du fichier json trouvé sur https://public.opendatasoft.com/explore/dataset/code-postal-code-insee-2015/export/
    """
    print("Chargement du fichier des communes de France. Patience...")
    with open(chemin) as entrée:
        données = json.load(entrée)

    print("Récupération des villes déjà présentes")
    toutes_les_villes = Ville.objects.all()
    déjà_présentes = set(x for x, in toutes_les_villes.values_list("code_insee"))
    print(f"{len(déjà_présentes)} villes déjà présentes.\n")

    print("Lecture des données")
    à_créer = []
    à_màj = []
    nb = 0
    for ville in données:
        ville["insee_com"] = int_of_code_insee(ville["insee_com"])
        if ville["insee_com"] in déjà_présentes:
            # màj
            v_d = toutes_les_villes.get(code_insee=ville["insee_com"])
            v_d.code = ville["code_postal"]
            v_d.géom_texte = json.dumps(ville["geo_shape"]["coordinates"][0])
            v_d.population = ville["population"]
            v_d.superficie = ville["superficie"]
            à_màj.append(v_d)
        else:
            # création
            ville["nom_norm"] = partie_commune(ville["nom_com"])
            ville["géom_texte"] = ville["geo_shape"]["coordinates"][0]
            v_d = objet_of_dico(Ville,
                                ville,
                                champs_obligatoires=["nom_norm", "population", "superficie"],
                                dico_champs_obligatoires={"nom_com":"nom_complet", "insee_com":"code_insee"},
                                dico_autres_champs={"code_postal":"code"},
                                autres_valeurs={"données_présentes":False},
                                champs_à_traiter={"géom_texte": ("géom_texte", json.dumps)}
                                )
            à_créer.append(v_d)
        nb+=1
        if nb%500==0: print(f"{nb} villes traitées")
    print(f"Enregistrement des {len(à_créer)} nouvelles villes")
    Ville.objects.bulk_create(à_créer)
    print(f"Màj des {len(à_màj)} autres villes (code postal, géométrie, superficie, population).")
    Ville.objects.bulk_update(à_màj, ["code", "géom_texte", "superficie", "population"])


def nettoie_json_communes(chemin=os.path.join(RACINE_PROJET, "progs_python/initialisation/données_à_charger/code-postal.json")):
    """
    Sert à nettoyé le fichier téléchargé à https://public.opendatasoft.com/explore/dataset/code-postal-code-insee-2015/export/.
    Ne devrait plus servir ensuite.
    - Remplace les éventuels «postal_code» par «code_postal»
    - ne garde que le contenu du ["fields"] de chaque entrée
    - ne garde que les champs "insee_com", "geo_shape", "code_postal", "nom_com", "population", "superficie"
    - Mets des None pour les champs manquant (il semble que ma ne soit que des code postaux)
    - supprime les doublons de (code insee, nom). Prends dans ces cas les min des codes postaux (Normalement ces cas sont des différents arrondissements d’une grande ville)
    """
    
    print("Chargement du fichier")
    with open(chemin) as entrée:
        données = json.load(entrée)
    print("Nettoyage des données")
    res = {}  # dico code_insee -> données de la ville
    champs = ["insee_com", "geo_shape", "code_postal", "nom_com", "population", "superficie"]
    supprimés = []
    
    for ville in données:
        ville = ville["fields"]
        if "postal_code" in ville:
            ville["code_postal"] = ville["postal_code"]

        if ville["insee_com"] in res:
            supprimés.append(ville)
            res[ville["insee_com"]]["code_postal"] = min(res[ville["insee_com"]]["code_postal"], ville["code_postal"])
            #print(res[ville["insee_com"]]["code_postal"])
        else:
            
            res[ville["insee_com"]] = {c:ville.get(c,None) for c in champs}


    print("Sauvegarde du nouveau fichier")
    nom_fichier = os.path.splitext(chemin)[0]+"nettoyé.json"
    with open(nom_fichier, "w") as sortie:
        sortie.write(json.dumps(tuple(res.values())))
    print(f"{len(supprimés)} doublons de code insee")
    #return supprimés


@transaction.atomic()
def renormalise_noms_villes():
    """
    Effet : recalcule le champ nom_norm de chaque ville au moyen de partie_commune.
    Utile si on changé cette dernière fonction.
    """
    n = 0
    for v in Ville.objects.all():
        if n%500==0: print(f"{n} communes traitées")
        n += 1
        v.nom_norm = partie_commune(v.nom_complet)
        v.save()
        

def charge_géom_villes(chemin=os.path.join(RACINE_PROJET, "progs_python/stats/docs/géom_villes.json")):
    """
    Rajoute la géométrie des villes à partir du json INSEE.
    """
    

        
    with open(chemin) as entrée:
        à_maj=[]
        
    Ville.objects.bulk_update(à_maj, ["géom_texte"])


def ajoute_villes_voisines():
    """
    Remplit les relations ville-ville dans la base.
    """
    dico_coords = {} # dico coord -> liste de villes
    à_ajouter=[]
    print("Recherche des voisinages")
    for v in Ville.objects.all():
        for c in v.géom_texte.split(";"):
            if c in dico_coords:
                for v2 in dico_coords[c]:
                    à_ajouter.append(Ville_Ville(ville1=v, ville2=v2))
                    à_ajouter.append(Ville_Ville(ville1=v2, ville2=v))
                    dico_coords[c].append(v)
            else:
                dico_coords[c] = [v]
    print("Élimination des relations déjà présente")
    à_ajouter_vraiment=[]
    for r in à_ajouter:
        if not Ville_Ville.objects.filter(ville1=r.ville1, ville2=r.ville2).exists():
            à_ajouter_vraiment.append(r)
    print("Enregistrement")
    Ville_Ville.objects.bulk_create(à_ajouter_vraiment)
