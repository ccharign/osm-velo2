 Recherche d'itinéaires cyclables par apprentissage supervisé.
 =============================================================


 Ce projet permet d'utiliser les données d'openstreetmap pour calculer des itinéraires cyclables. Il se présente sous la forme d’une appli Django.

 Son intérêt est d'implémenter une partie apprentissage supervisé : après récupération d'une banque d'itinéraires entrés par des cyclistes, une note de cyclabilité est attribuée à chaque tronçon, et les itinéraires sont calculés en en tenant compte.

 Il est testable ici : http://trajet.pauavelo.fr/

Installation
============

 - Une fois le dépôt cloné, le settings.py configuré (notamment pour paramétrer le serveur de base de données) et le `python manage.py migrate` effectués pour initialiser la base, ouvrir un shell pour la remplir (`python manage.py shell`)
 - `from dijk.pour_shell import *`
 - `charge_ville()` charge les données INSEE sur les villes de France. Patience...
 - `charge_zone([("ville 1", code postal1), ("ville2", code postal 2), ...], zone = "nom_de_la_zone", ville_défaut = "nom_de_la_ville_par_défaut", code = code_postal_de_la_ville_par_défaut)`
 - patience encore, l’appli va télécharger et analyser les données osm de toutes les villes indiquées...


