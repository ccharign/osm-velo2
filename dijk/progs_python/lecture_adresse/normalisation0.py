# -*- coding:utf-8 -*-

### Programmes de normalisation qui n’utilisent pas les modèles (pour éviter les dépendances circulaires) ###

import re
from dijk.progs_python.petites_fonctions import multi_remplace, LOG


class AdresseMalFormée(Exception):
    pass


def int_of_code_insee(c: str) -> int:
    """
    Entrée : (str) code INSEE
    Sortie (int) : entier obtenu en remplaçant A par 00 et B par 01 (à cause de la Corse) et en convertissant le résultat en int.
    """
    return int(c.replace("A", "00").replace("B", "01"))


def partie_commune(c: str) -> str:
    """ Appliquée à tout : nom de ville, de rue, et adresse complète
    Met en minuscules
    Supprime les tirets
    Remplace les appostrophes utf8 par des single quote
    Enlève les accents sur les e et les a"""
    remplacements = [("-", " "), ("é|è|ê|ë", "e"), ("à|ä", "a"), ("’", "'"), ("ç", "c")]
    res = c.strip().lower()
    for e, r in remplacements:
        res = re.sub(e, r, res)
    
    return res
    

def normalise_adresse(c):
    """
    Utilisé pour normaliser les adresses complètes, pour améliorer le cache.
    Actuellement c’est partie_commune(c)
    """
    return partie_commune(c)


def découpe_adresse(texte: str, bavard=0) -> tuple[str, str, str, str]:
    """
    Entrée : texte (str)
    Sortie (str*str*str*str) : num, bis_ter, rue, ville
    """
    # Découpage selon les virgules
    trucs = texte.split(",")
    if len(trucs) == 1:
        num_rue, ville_t = trucs[0], ""
    elif len(trucs) == 2:
        num_rue, ville_t = trucs
    elif len(trucs) == 3:
        num_rue, ville_t, pays = trucs
    else:
        raise AdresseMalFormée(f"Trop de virgules dans {texte}.")
    ville_t = ville_t.strip()

    # numéro de rue et rue
    num, bis_ter, rue_initiale = re.findall("(^[0-9]*) *(bis|ter)? *(.*)", num_rue)[0]

    LOG(f"(découpe_adresse) Analyse de l’adresse : num={num}, bis_ter={bis_ter}, rue_initiale={rue_initiale}, ville={ville_t}", bavard=bavard)
    return num, bis_ter, rue_initiale, ville_t


DICO_REMP = {
    "avenue": "α",
    "rue": "ρ",
    "boulevard": "β",
    "allée": "λ",
    "lotissement": "∘"
}

def sansDoublesEspaces(c: str):
    """
    Renvoie la chaîne c où tous les facteurs de plusieurs espaces ont été remplacé par une seul espace.
    """
    return re.sub("  +", " ", c)


def prétraitement_rue(rue):
    """
    Après l’étape "partie_commune", supprime les «de », «du », «de la ».
    Si deux espaces consécutives, supprime la deuxième.
    Remplace les mots « avenue », « rue », etc par une lettre grecque. (Pour que la confusion rue/avenue compte pour une seule fautede frappe.)
    Remplace enfin tous les caractères non alphanumériques par une espace.
    """
    
    étape1 = partie_commune(rue)
    
    # les chaînes suivantes seront remplacées par une espace.
    à_supprimer = [" du ", " de la ", " de l'", " de ", " des ", " d'", "  "]  # Mettre "de la " avant "de ". Ne pas oublier les espaces.
    regexp = "|".join(à_supprimer)
    fini = False
    res = étape1
    # Pour les cas comme « rue de du Forbeth »
    while not fini:
        suivant = re.sub(regexp, " ", res)
        if suivant == res:
            fini = True
        else:
            res = suivant

    # Remplacer « rue », « avenue », etc par un symbole utf-8 pour qu’ils ne comptent que comme une faute de frappe.
    étape3 = multi_remplace(DICO_REMP, res)

    # Éliminer tous les caractères spéciaux
    étape4 = re.sub("[^a-z0-9αρβλ∘]", " ", étape3)

    # Et les espaces multiples ayant pu apparaître
    return re.sub("  +", " ", étape4.strip())
