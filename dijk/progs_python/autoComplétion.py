"""Gère les demandes d’auto-complétion de champs de formulaire de recherche."""

# -*- coding:utf-8 -*-

import json
import re

from django.db.models import Subquery

from .lecture_adresse.normalisation0 import prétraitement_rue, partie_commune, découpe_adresse
import dijk.models as mo


### Auto complétion ###


class Résultat:
    """
    Pour enregistrer le résultat à renvoyer.

    Un nouvel élément d n’est ajouté que si son label n’est pas déjà présent et si le nb de résultats est < self.n_max
    """

    def __init__(self, n_max):
        self.res = []
        self.n_max = n_max
        self.déjà_présent = set()
        self.nb = 0
        self.trop_de_rés = False

    def __len__(self):
        return self.nb

    def ajoute(self, réponse: dict):
        """
        Ajoute un élément aux résultats.

        Entrées:
             réponse: le dico à mettre dans le rés
        """
        if self.nb < self.n_max:
            # àAfficher = réponse["label"]
            # if àAfficher not in self.déjà_présent:
            #    self.déjà_présent.add(àAfficher)
            self.res.append(réponse)
            self.nb += 1
        else:
            self.trop_de_rés = True

    def ajoute_un_paquet(self, réponses):
        """
        Ajoute plusieurs éléments aux résultats.

        Entrée: un iterable de dicos
        Effet: ajoute les élément de réponses s’il y a assez de place. Dans le cas contraire, n’ajoute rien, et passe self.trop_de_rés à True.

        NB: le principe est d’utiliser ajoute_un_paquet pour les types de réponses par ordre de priorité.
        """
        if self.trop_de_rés or len(réponses) + self.nb > self.n_max:
            self.trop_de_rés = True
        else:
            for r in réponses:
                self.ajoute(r)

    def vers_json(self) -> str:
        """Renvoie le json de la liste de dicos à renvoyer."""
        return json.dumps(self.res)


def complétion(à_compléter: str, nbMax: int, z_d: mo.Zone) -> Résultat:
    """
    Fonction principale pour la complétion.

    Entrée : à_compléter, chaîne de car à compléter.
    En cas de présence de parenthèse, on considère qu’il s’agit d’un lieu, et que dans la parenthèse il y a l’adresse.
    
    Sortie: l’objet de la classe Résultat contenant les complétions possibles.
    """
    
    à_compléter = à_compléter.strip()
    str_ville = ""
    
    # cas 1 : parenthèse
    # dans ce cas le contenu de la parenthèse peut avoir une adresse complète, ou juste un nom de ville.
    # et la première partie est un nom de lieu
    regexp_lieu = re.compile("(.*)\(([^)]*)\)?")
    avec_parenthèse = regexp_lieu.fullmatch()
    if avec_parenthèse:
        str_lieu, str_adresse = avec_parenthèse.groups()
        # Dans la parenthèse, il peut y avoir une adresse complète, ou juste une ville
        str_ville = avec_parenthèse.group(2)
    else:
        # Sinon on ne sait pas su la chaîne cherchée est un lieu ou une adresse
        str_lieu = à_compléter
        str_adresse = à_compléter

    
    
    
    # Découpage de la chaîne à chercher
    num, bis_ter, str_rue, déb_ville = découpe_adresse(str_adresse)
    if déb_ville:
        # Si on a trouvé une ville dans l’adresse, on garde celle-ci
        # (càd si l’adresse contenait une virgule)
        str_ville = déb_ville
        
    str_ville_norm = partie_commune(str_ville)

    # prétraitement_rue est la fonction qui normalise à la fois les noms de rue et de lieux
    à_chercher = prétraitement_rue(str_rue)
    
    print(f"Recherche de {à_chercher} dans la ville {str_ville_norm}")
    breakpoint()
    # Villes : dans la zone et contient la partie après la virgule de à_compléter
    villes = mo.Ville_Zone.objects.filter(
        zone=z_d, ville__nom_norm__startswith=déb_ville
    )
    req_villes = Subquery(villes.values("ville"))

    res = Résultat(nbMax)

    cherche_dans_gtls(str_lieu, res)
    
    cherche_un_lieu(str_lieu, res, req_villes)

    cherche_une_adresse(num, bis_ter, str_rue, res, req_villes)
    
    return res


# Complétion dans l’arbre lexicographique (pour les fautes de frappe...)
# Fonctionne sauf qu’on ne récupère pas la ville pour l’instant
# dans_l_arbre = g.arbre_lex_zone[z_d].complétion(à_chercher, tol=2, n_max_rés=nbMax)
# print(dans_l_arbre)


def cherche_une_adresse(num: str, bis_ter: str, str_rue: str, res: Résultat, req_villes) -> None:
    # Recherche dans les rues
    début = " ".join(x for x in [num, bis_ter] if x)
    if début:
        début += " "
    rues = mo.Rue.objects.filter(
        nom_norm__icontains=str_rue,
        ville__in=req_villes
    ).prefetch_related("ville")
    res.ajoute_un_paquet([r.pour_autocomplète(num, bis_ter) for r in rues])



def cherche_un_lieu(à_chercher: str, res: Résultat, req_villes) -> None:
    """Cherche un Lieu"""
    # Recherche dans les lieux
    mots = à_chercher.split(" ")
    lieux = mo.Lieu.objects.filter(
        ville__in=req_villes,
    ).prefetch_related(
        "ville", "type_lieu"
    )
    for mot in mots:
        lieux = lieux.filter(nom_norm__contains=mot)
    print(f"{len(lieux)} lieux trouvées")

    res.ajoute_un_paquet([l.pour_js() for l in lieux])


def cherche_dans_gtls(à_chercher: str, res: Résultat):
    """
    Recherche dans les groupes de types de lieu
    Exemple: Une boulangerie
    """
    essais = re.findall("(une?) (.*)", à_chercher)
    if len(essais) == 1:
        déterminant, texte = essais[0]
        gtls = mo.GroupeTypeLieu.objects.filter(
            nom__istartswith=texte, féminin=déterminant == "une"
        )
        res.ajoute_un_paquet([gtl.pour_js() for gtl in gtls])
