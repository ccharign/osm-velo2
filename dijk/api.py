"""
Définit l’API
"""

from typing import List
import json

from django.core.handlers.wsgi import WSGIRequest
from ninja import NinjaAPI, Schema

import dijk.models as mo
from dijk.progs_python.graphe_par_django import Graphe_django
import dijk.progs_python.autoComplétion as ac
from dijk.progs_python.chemins import Étape
from dijk.progs_python.utils import itinéraire_of_étapes
from .progs_python.apprentissage import n_lectures
from dijk.progs_python.chemins import Chemin
from dijk.progs_python.params import LOG

g = Graphe_django()


api = NinjaAPI()



@api.get("/init")
def getZonesEtGtls(request):
    """
    Renvoie la liste des zones et des groupes de types de lieu pour « passer par un(e) ».
 Format {"value": ..., "label": ...}
    """
    return {
        "zones": [
            {"value": str(z), "label": str(z)}
            for z in mo.Zone.objects.all()
        ],
        "gtls": [
            gtl.pour_js()
            for gtl in mo.GroupeTypeLieu.objects.all()
        ]
    }


@api.get("/charge-zone/{nom_zone}")
def loadZone(request, nom_zone: str):
    """
    Charge en mémoire la zone indiquée, afin de gagner du temps par la suite.
    """
    g.charge_zone(nom_zone)
    return nom_zone


@api.get("/completion")
def complétion(request, zone: str, term: str):
    """
    Renvoie les lieux de la base pour la zone indiquée et dont le nom contient term.
    """
    z_d = mo.Zone.objects.get(nom=zone)
    return ac.complétion(term, 20, z_d).res




@api.get("/itineraire/{nom_zone}")
def itinéraire(_request: WSGIRequest, nom_zone: str, étapes_str: str):
    z_d = g.charge_zone(nom_zone)
    étapes = [Étape.of_dico(é, g, z_d) for é in json.loads(étapes_str)]
    res = [
        iti.vers_js()
        for iti in itinéraire_of_étapes(étapes, [0, .15, .3], g, z_d, rajouter_iti_direct=False)["itinéraires"]
    ]
    res[0]["nom"] = "Trajet direct"
    res[1]["nom"] = "Intermédiaire"
    res[2]["nom"] = "Priorité confort"
    return res



class ÉtapeJson(Schema):
    """
    Un objet pour représenter une étape.
    """
    type_étape: str
    pk: int = None
    num: bool = None
    lon: float = None
    lat: float = None
    adresse: str = None


@api.post("/contribuer/{nom_zone}")
def enregistrerContribution(request: WSGIRequest, nom_zone: str, étapes_str: List[ÉtapeJson], pourcentages_détour: List[int], AR: bool = False):
    """
    Crée les objets Chemin dans la base, et lance l’apprentissage dessus.
    """
    nb_lectures = 20
    z_d = g.charge_zone(nom_zone)
    étapes = [Étape.of_dico(dict(é), g, z_d) for é in étapes_str]
    for pd in pourcentages_détour:
        c = Chemin.of_étapes(z_d, étapes, pd, AR, g, bavard=2)
        prop_modif = n_lectures(nb_lectures, g, [c], bavard=1)
        c_d = c.vers_django(bavard=1)
        c_d.dernier_p_modif = prop_modif
        c_d.save()

    LOG("Calcul des nouveaux cycla_min et cycla_max", bavard=1)
    z_d.calculeCyclaMinEtMax()
    return("Fini")
