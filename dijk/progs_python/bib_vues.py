# -*- coding:utf-8 -*-

"""
Fonctions utiles à views.py
"""

import json

from dijk.progs_python.chemins import ÉtapeEnsLieux, Étape





def chaîne_avec_points_virgule_renversée(c: str):
    """
    c contient des point-virgules
    Sortie : la même en inversant l’ordre des morceaux séparés par les points-virgules.
    """
    return ";".join(
        reversed(
            c.split(";")
        )
    )


def dict_of_get(g):
    """
    Un simple dict(g) semble ne pas fonctionner...
    """
    return dict(g.items())


def récup_données(dico, cls_form, validation_obligatoire=True):
    """
    Entrée :
        dico, contient le résultat d’un GET ou d’un POST
        cls_form, classe du formulaire correspondant.
    Effet:
        lève une exception si form pas valide et validation_obligatoire est True.
    Sortie:
       dico transformé en un vrai type dict, auquel est rajouté le contenu du form.cleaned_data, ainsi que le formulaire, associé à la clef 'form'.
    """
    form = cls_form(dico)
    if not form.is_valid():
        if validation_obligatoire:
            raise ValueError(f"Formulaire pas valide : {form}.\n Erreurs : {form.errors}")
        else:
            print(f"Formulaire pas valide : {form}.\n Erreurs : {form.errors}")
    données = dict_of_get(dico)
    données.update(form.cleaned_data)
    données['form'] = form
    return données


def z_é_i_d(g, données):
    """
    Entrée (dico) : résultat d’un GET ou d’un POST d’un formulaire de recherche d’itinéraire.

    Sortie (Zone, Étapes list, Étapes list, Étapes list, float list) : (zone, étapes, étapes_interdites, étapes_sommets, ps_détours)
       - étapes est la liste ordonnée des étapes desquelles emprunter au moins une arête
       - étapes_interdites est la liste non ordonnée des étapes desquelles n’emprunter aucune arête
       - étapes_sommets est la liste non ordonnée des étapes desquelles emprunter au moins un sommet.

    Effet :
       la zone est chargée si pas déjà le cas.
       données est éventuellement complété dans le cas d’une adresse venant d’une autocomplétion par les coords de l’adresse obtenues sur data.gouv
    """
    
    z_d = g.charge_zone(données["zone"])
    ps_détour = list(map(
        lambda x: float(x)/100,
        données["pourcentage_détour"].split(";")
    ))

    # # Pour les étapes interdites, on peut rassembler celles des clics et celles du form car pas de pb d’ordre.
    # TODO...
    é_interdites = []

    étapes_dicos = json.loads(
        données["toutes_les_étapes"]
    )
    étapes = [Étape.of_dico(d, g, z_d) for d in étapes_dicos]

    # Il est possible que des coords aient été rajoutées : en cas d’adresse avec numéro de rue, les coords ot été récupérées sur data.gouv.
    # Je sauvegarde ceci.
    # NB : on pourrait faire en sorte de ne le faire que si modif.

    # données["toutes_les_étapes"] = json.dumps(étapes_dicos)
    # recréation du champ toutes_les_étapes : il y aura éventuellement plus d’infos.
    données["toutes_les_étapes"] = json.dumps([
        é.pour_marqueur() for é in étapes
    ])
    
    # Étapes sommet
    étapes_sommets = []
    if données["passer_par"]:
        étapes_sommets.append(ÉtapeEnsLieux(données["passer_par"], z_d))

    return z_d, étapes, é_interdites, étapes_sommets, ps_détour


def bool_of_checkbox(dico, clef):
    """
    Entrée : dico issu d’un POST
             clef
    Renvoie True si la clef est présente dans le dico et la valeur associée est  'on'
    """
    return clef in dico and dico[clef] == "on"


def énumération_texte(l):
    """
    Entrée : liste de str
    Sortie : une str contenant les éléments de l séparés par des virgules, sauf dernier qui est séparé par le mot « et »
    """
    if len(l) == 0:
        return ""
    elif len(l) == 1:
        return l[0]
    else:
        return ", ".join(l[:-1]) + " et " + l[-1]

