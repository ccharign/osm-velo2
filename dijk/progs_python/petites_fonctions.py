# -*- coding:utf-8 -*-


"""
Ces petites fonctions ne doivent pas dépendre d’autres modules, à part params.py, pour ne pas créer de pb de dépendance.

"""

from math import pi, cos, acos, sin
import time
import shutil
import os
import datetime
import re

from django.db import transaction
# import geopy
# import geopy.distance
from params import D_MAX_POUR_NŒUD_LE_PLUS_PROCHE, LOG




#################
### Géométrie ###
#################

class TropLoin(Exception):
    pass


R_TERRE = 6360000  # en mètres

# geopy.distance.distance

def distance_euc(c1, c2):
    """
    Entrée : deux coords sous la forme (lon, lat)
    Sortie : distance en mètres.
    """
    
    # return geopy.distance.distance(c1,c2).km
    
    lon1, lat1 = c1
    lon2, lat2 = c2

    # Conversion en radian
    k=pi/180
    lat1*=k
    lat2*=k
    lon1*=k
    lon2*=k
    #assert lat1>40 and lat2>40, f"Je voulais des coordonnées au format (lon, lat) et j’ai reçu {c1} et {c2}"
    dx = R_TERRE * cos(lat1) * (lon2-lon1)
    dy = R_TERRE * (lat2-lat1)
    return (dx**2+dy**2)**.5
    
    # vraie formule (pas utilisée) :
    return R_TERRE * acos(cos(lat1)*cos(lat2)*cos(lon2-lon1) + sin(lat1 * lat2))


def bbox_autour(coords, d):
    """
    Entrée:
        coords (float×float)
        d (float), en mètres
    Renvoie le carré de centre « coords » de rayon d. Au format (s,o,n,e).
    """
    lon, lat = coords
    dlat = d / R_TERRE / pi * 180
    dlon = dlat/cos(lat/180*pi)
    return (lat-dlat, lon-dlon, lat+dlat, lon+dlon)
    


def distance_si_pas_trop(c1, c2):
    d = distance_euc(c1, c2)
    if d > D_MAX_POUR_NŒUD_LE_PLUS_PROCHE:
        print(f"distance entre {c1} et {c2} supérieure à {D_MAX_POUR_NŒUD_LE_PLUS_PROCHE}")
        raise TropLoin()
    else:
        return d

    
def milieu(c1, c2):
    lon1, lat1 = c1
    lon2, lat2 = c2
    return (lon1+lon2)/2, (lat1+lat2)/2



##################
### Itérateurs ###
##################

    
def deuxConséc(t):
    """ Renvoie un itérateur sur les couples d'éléments consécutifs de t."""
    n = len(t)
    for i in range(n-1):
        yield t[i], t[i+1]

def union(t1, t2):
    """
    Entrée : t1 itérable, t2 itérable ou itérateur.
    Sortie : itérateur sur t1 ∪ t2, doublons enlevés.
    Utilisation de « in t1 ».
    """
    for x in t1:
        yield x
    for x in t2:
        if x not in t1:
            yield x

            
def union_liste(l):
    """
    Entrée : l, iterable d’itérables
    Sortie : itérateur sur l’union des éléments de l
    """
    for x in l:
        for y in x:
            yield y


def intersection(t1, t2):
    """ Itérateur sur t1 ∩ t2."""
    for x in t1:
        if x in t2:
            yield x



            

########################################
#### Modif de la base par lots ####
########################################


def morceaux_tableaux(t, taille):
    """
    Itérateurs sur des tranches de tableaux de taille taille.
    """
    i = 0  # Au cas où len(t)<taille
    for i in range(taille, len(t), taille):
        yield t[i-taille: i]
    yield t[i:]



def supprime_objets_par_lots(l, taille_lots=2000):
    n = 0
    for lot in morceaux_tableaux(l, taille_lots):
        with transaction.atomic():
            for x in lot:
                x.delete()
        n += taille_lots
        print(f"{n} objets supprimés")


def sauv_objets_par_lots(l, taille_lots=2000):
    n = 0
    for lot in morceaux_tableaux(l, taille_lots):
        with transaction.atomic():
            for x in lot:
                x.save()
        n += taille_lots
        print(f"{n} objets sauvegardés")



###################
### Benchmarking###
###################


def chrono(tic, tâche, bavard=1, force=False):
    """
    Entrée : tic, float
             tâche, str
             force, bool
    Effet : log (time.perf_counter()-tic) pour la tâche précisée
            Si force est faux, ne log que pour un temps>.1s
    Sortie : instant où a été lancé cette fonction.
    """
    tac = time.perf_counter()
    temps = tac-tic
    if temps>.1 or force:
        LOG(f"{round(time.perf_counter()-tic, 2)}s pour {tâche}", "perfs", bavard=bavard)
    return tac


# Une fabrique de décorateurs.
def mesure_temps(nom, temps, nb_appels):
    """
    Entrées : temps et nb_appels deux dicos dont nom est une clef.
    """
    def décorateur(f):
        def nv_f(*args, **kwargs):
            tic=time.perf_counter()
            res=f(*args, **kwargs)
            temps[nom]+=time.perf_counter()
            nb_appels[nom]+=1
            return res
        return nv_f
    return décorateur
        




##############
### Divers ###
##############


def sauv_fichier(chemin):
    """
    Crée une copie du fichier dans le sous-répertoire « sauv » du répertoire contenant le fichier. Le sous-répertoire « sauv » doit exister au préalable.
    """
    dossier, nom = os.path.split(chemin)
    dossier_sauv = os.path.join(dossier,"sauv")
    os.makedirs(dossier_sauv, exist_ok=True)
    nom_sauv = nom+str(datetime.datetime.now())
    shutil.copyfile(
        chemin,
        os.path.join(dossier_sauv, nom_sauv)
    )

def sauv_fichier(chemin):
    """
    Crée une copie du fichier dans le sous-répertoire « sauv » du répertoire contenant le fichier. Le sous-répertoire « sauv » doit exister au préalable.
    """
    dossier, nom = os.path.split(chemin)
    dossier_sauv = os.path.join(dossier,"sauv")
    os.makedirs(dossier_sauv, exist_ok=True)
    nom_sauv = nom+str(datetime.datetime.now())
    shutil.copyfile(
        chemin,
        os.path.join(dossier_sauv, nom_sauv)
    )


def multi_remplace(d, texte):
    """
    Entrées : d (str -> str dict)
              texte (str)
    Sortie : texte où chaque itération d’une clef de d a été remplacée par la valeur correspondante.
    """
    #https://stackoverflow.com/questions/6116978/how-to-replace-multiple-substrings-of-a-string
    remp = { re.escape(c):v for c,v in d.items()}
    regexp = re.compile("|".join(remp.keys()))
    return regexp.sub(lambda m:remp[re.escape(m.group(0))], texte)


########################################
#### Manip de tableaux ####
########################################

def fusionne_tab_de_tab(t1, t2):
    """
    Entrées:
       t1 et t2 tableaux de tableaux
    Effet:
        Pour tout i dans [|0, max(len(t1), len(t2))[|, rajoute les éléments de t2[i] dans t1[i]. (Cases créées dans t1 si besoin)
    """
    dl = len(t2)-len(t1)
    if dl > 0:
        t1.extend([[] for _ in range(dl)])
    for i in range(len(t2)):
        t1[i].extend(t2[i])


def ajouteDico(d, clef, val):
    """d est un dico de listes.
       Ajoute val à la liste de clef donnée si pas encore présente."""
    if clef in d:
        if val not in d[clef]:
            d[clef].append(val)
    else:
        d[clef] = [val]



def zip_dico(clefs, vals):
    """
    Sortie : dico contenant les clefs de clefs, associées aux valeurs de vals, respectivement.
    """
    return {c: v for (c, v) in zip(clefs, vals)}

# geopy.geocoders.options.default_user_agent = "pau à vélo"
# localisateur = geopy.geocoders.Nominatim(user_agent="pau à vélo")
# def recherche_inversée(coords, bavard=0):
#     if bavard>0:print("Pause de 1s avant la recherche inversée")
#     time.sleep(1)
#     return(localisateur.reverse(coords))
