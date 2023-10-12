from ninja import NinjaAPI
import dijk.models as mo
from dijk.progs_python.graphe_par_django import Graphe_django
import dijk.progs_python.autoComplétion as ac

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
