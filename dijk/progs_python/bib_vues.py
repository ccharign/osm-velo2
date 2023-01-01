# -*- coding:utf-8 -*-

import re

from dijk.progs_python.chemins import Étape, ÉtapeArête



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
       données est éventuellement complété dans le cas d’une adresse venant d’une autocomplétion par les coords de l’adresse.
    """
    
    z_d = g.charge_zone(données["zone"])
    ps_détour = list(map(
        lambda x: float(x)/100,
        données["pourcentage_détour"].split(";")
    ))

    # Le départ (possiblement des coords gps)
    if "partir_de_ma_position" in données and données["partir_de_ma_position"]:
        coords = tuple(map(float, données["localisation"].split(",")))
        assert len(coords) == 2, f"coords n'est pas de longueur 2 {coords}"
        données["départ_coords"] = str(coords)[1:-1]
        breakpoint()
        départ = ÉtapeArête.of_coords(coords, g, z_d)
    else:
        départ = Étape.of_dico(données, "départ", g, z_d)

        
    # L’arrivée
    arrivée = Étape.of_dico(données, "arrivée", g, z_d)

    
    # Les étapes intermédiaires et interdites:
    
    é_inter = []
    é_interdites = []
    # Voyons s’il y en a venant des clics sur la carte :
    for c, v in données.items():
        if "étape_coord" in c:
            num = int(re.match("étape_coord([0-9]*)", c).groups()[0])
            coords = tuple(map(float, v.split(",")))
            a, _ = g.arête_la_plus_proche(coords, z_d)
            é_inter.append((num, ÉtapeArête.of_arête(a, coords)))
            
        elif "interdite_coord" in c:
            coords = tuple(map(float, v.split(",")))
            a, _ = g.arête_la_plus_proche(coords, z_d)
            é_interdites.append(ÉtapeArête.of_arête(a, coords))
    é_inter.sort()
    é_inter = [é for _, é in é_inter]
    
    if not é_inter:
        # Pas d’étape inter venant d’un clic : prendre celles présentes dans le formulaire.
        é_inter = [Étape.of_texte(é, g, z_d) for é in données["étapes"].strip().split(";") if len(é) > 0]
        
    étapes = [départ] + é_inter + [arrivée]

    # Pour les étapes interdites, on peut rassembler celles des clics et celles du form car pas de pb d’ordre.
    é_interdites += [Étape.of_texte(r, g, z_d) for r in données["rues_interdites"].strip().split(";") if len(r)>0]


    # Étapes sommet
    étapes_sommets = []
    if données["passer_par"]:
        étapes_sommets.append(Étape.of_groupe_type_lieux(données["passer_par"], z_d))

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

    
# def sans_style(texte):
#     """
#     Entrée : du code html (str)
#     Sortie : le code sans les lignes entourées de balises <style>...</style>
#     """
    
#     x = re.findall("(.*?)<style>.*?</style>(.*)", texte)  # ? : non greedy
#     if x:
#         return x[0][0] + sans_style(x[0][1])
#     else:
#         return texte

    
# def récup_head_body_script(chemin):
#     """ Entrée : adresse d’un fichier html
#         Sortie : la partie body de celui-ci
#     """
#     with open(chemin) as entrée:
#         tout=entrée.read()
        
#         head, suite = tout.split("</head>")
#         lignes_head = head.split("<head>")[1].split("\n")
#         à_garder = []
#         for ligne in lignes_head:
#             if not ("bootstrap in ligne"):
#                 à_garder.append(ligne)
#         head_final = "\n".join(à_garder)
        
        
#         body, suite = suite.split("</body>")
#         body = body.split("<body>")[1]

#         script = suite.split("<script>")[1].split("</script>")[0]
#     return head, body, script

