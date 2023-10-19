"""
Définit l’API
"""

from typing import List, Annotated
import json

from django.core.handlers.wsgi import WSGIRequest
from ninja import NinjaAPI, Schema, Query

import dijk.models as mo
from dijk.progs_python.graphe_par_django import Graphe_django
import dijk.progs_python.autoComplétion as ac
from dijk.progs_python.chemins import Étape
from dijk.progs_python.utils import itinéraire_of_étapes

g = Graphe_django()


api = NinjaAPI()



@api.get("/zones")
def getZones(request):
    """
    Renvoie la liste des zones existantes. Format {"value": ..., "label": ...}
    """
    return [
        {"value": str(z), "label": str(z)}
        for z in mo.Zone.objects.all()
    ]


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
def itinéraire(request: WSGIRequest, nom_zone: str, étapes_str: str):
    z_d = g.charge_zone(nom_zone)
    étapes = [Étape.of_dico(é, g, z_d) for é in json.loads(étapes_str)]
    return [iti.vers_js() for iti in itinéraire_of_étapes(étapes, [], [.15, .30], g, z_d)["itinéraires"]]
    
