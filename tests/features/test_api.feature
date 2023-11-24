Feature: test API

    Scenario: test charge_zone
        When je charge la zone Pau
        Then je reçois la réponse Pau

    @en-cours
    Scenario Outline: test itinéraire
        When je recherche un itinéraire entre <départ> et <arrivée>
        Then j’ai trois résultats
    Examples:
        | départ | arrivée |
        | red lion | le w |
        

    Scenario Outline: test autocomplète
        When je recherche les complétions <un_terme>
        Then le résultat contient <le_lieu>

    Examples:
        | un_terme | le_lieu |
        | rue des Vé | Rue des Véroniques |
        | red li | New Red Lion |

