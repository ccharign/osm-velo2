"""Les steps pour les tests behave."""

from behave import when, then
import dijk.api as api
import json


@when("je charge la zone Pau")
def step_zone_pau(context):
    context.response = api.loadZone(None, "Pau")


@then("je reçois la réponse Pau")
def step_zone_pau_then(context):
    assert context.response == "Pau"


@when("je recherche les complétions {term}")
def when_recherche_term(context, term):
    context.response = api.complétion(None, "Pau", term)


@then("le résultat contient {le_lieu}")
def then_résultat_contient_lieu(context, le_lieu):
    noms = [r["nom"] for r in context.response]
    assert le_lieu in noms


def étapeOfTerme(terme: str) -> api.ÉtapeJsonEntrée:
    """Renvoie le json correspondant à l’étape obtemue par autocomplétion du terme."""
    étape_complétée = api.complétion(None, "Pau", terme)[0]
    return api.ÉtapeJsonSortie(**étape_complétée).vers_entrée()


@when("je recherche un itinéraire entre {départ} et {arrivée}")
def when_recherche_iti(context, départ, arrivée):
    context.départ = étapeOfTerme(départ)
    context.arrivée = étapeOfTerme(arrivée)


@then("j’ai trois résultats")
def step_impl(context):
    itinéraires = api.itinéraire(
        None, "Pau", json.dumps([dict(context.départ), dict(context.arrivée)])
    )
    assert len(itinéraires) == 3
