"""Définit l’API."""

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
from dijk.progs_python.étapes import HorsZone

g = Graphe_django()


api = NinjaAPI()



class Erreur(Schema):
    """Schema pour les messages d’erreur."""
    
    message: str


@api.get("/init")
def getZonesEtGtls(request):
    """
       Renvoie la liste des zones (List[str]) et des groupes de types de lieu pour « passer par un(e) ».

    format {"value": ..., "label": ...}
    """
    return {
        "zones": [str(z) for z in mo.Zone.objects.all()],
        "gtls": [gtl.pour_js() for gtl in mo.GroupeTypeLieu.objects.all()],
    }


@api.get("/charge-zone/{nom_zone}")
def loadZone(request, nom_zone: str) -> str:
    """
    Charge en mémoire la zone indiquée, afin de gagner du temps par la suite.

    Sortie: le nom de la zone
    """
    g.charge_zone(nom_zone)
    return nom_zone


class ÉtapeJsonEntrée(Schema):
    """Un objet pour représenter une étape tel que reçu par le serveur."""

    type_étape: str
    pk: int = None
    num: bool = None
    lon: float = None
    lat: float = None
    adresse: str = None


class ÉtapeJsonSortie(Schema):
    """Représente un dico renvoyé par le serveur lors d’une autocomplétion."""

    type_étape: str
    pk: int = None
    géom: List[List[float]]  # liste de [lon, lat]
    nom: str

    def vers_entrée(self) -> ÉtapeJsonEntrée:
        """Convertit le dico dans vers le format utilisé en entrée."""
        dico = dict(self)
        lon, lat = dico.pop("géom")[0]
        print(dico)
        return ÉtapeJsonEntrée(**(dico | {"lon": lon, "lat": lat}))


@api.get("/completion")
def complétion(request, zone: str, term: str) -> List[ÉtapeJsonSortie]:
    """Renvoie les lieux de la base pour la zone indiquée et dont le nom contient term."""
    z_d = mo.Zone.objects.get(nom=zone)
    return ac.complétion(term, 20, z_d).res


@api.get("/itineraire/{nom_zone}", response={200: List, 500: Erreur})
def itinéraire(_request: WSGIRequest, nom_zone: str, étapes_str: str) -> List:
    """Renvoie l’itinéraire entre les étapes indiquées en params."""
    try:
        z_d = g.charge_zone(nom_zone)
        étapes = [Étape.of_dico(é, g, z_d) for é in json.loads(étapes_str)]
        res = [
            iti.vers_js()
            for iti in itinéraire_of_étapes(
                étapes, [0, 0.15, 0.3], g, z_d, rajouter_iti_direct=False
            )["itinéraires"]
        ]
        res[0]["nom"] = "Trajet direct"
        res[1]["nom"] = "Intermédiaire"
        res[2]["nom"] = "Priorité confort"
        return res
    except HorsZone:
        return 500, {"message": f"Étape en dehors de la zone chargée ({nom_zone})"}
    except Exception as e:
        return 500, {"message": f"Erreur: {e}"}


@api.post("/contribuer/{nom_zone}")
def enregistrerContribution(
    request: WSGIRequest,
    nom_zone: str,
    étapes_str: List[ÉtapeJsonEntrée],
    pourcentages_détour: List[int],
    AR: bool = False,
):
    """Crée les objets Chemin dans la base, et lance l’apprentissage dessus."""
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
    return "Fini"
