 Recherche d'itinéaires cyclables par apprentissage supervisé.
 =============================================================


 Ce projet permet d'utiliser les données d'openstreetmap pour calculer des itinéraires cyclables. Il se présente sous la forme d’une appli Django.

 Son intérêt est d'implémenter une partie apprentissage supervisé : après récupération d'une banque d'itinéraires entrés par des cyclistes, une note de cyclabilité est attribuée à chaque tronçon, et les itinéraires sont calculés en en tenant compte.

 Il est testable ici : http://trajet.pauavelo.fr/

Installation
============

 - `git clone https://github.com/ccharign/osm-velo2.git`
 - `cd osm-velo2`
 - `pip install -r requirements.txt`
 - Configurer le settings.py, notamment pour paramétrer le serveur de base de données.
 - `python manage.py migrate` pour initialiser la base
 - Ouvrir un shell Django pour la remplir : `python manage.py shell`
 - `from dijk.pour_shell import *`
 - `charge_villes()` charge les données INSEE sur les villes de France. Patience...
 - `crée_zone([("ville 1", code postal1), ("ville2", code postal 2), ...], zone = "nom_de_la_zone")`. La première ville de la liste sera désignée ville par défaut.
 - patience encore, l’appli va télécharger et analyser les données osm de toutes les villes indiquées...


