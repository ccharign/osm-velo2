 Recherche d'itinéaires cyclables par apprentissage supervisé.
 =============================================================


 Ce projet permet d'utiliser les données d'openstreetmap pour calculer des itinéraires cyclables. Il se présente sous la forme d’une appli Django.

 Son intérêt est d'implémenter une partie apprentissage supervisé : après récupération d'une banque d'itinéraires entrés par des cyclistes, une note de cyclabilité est attribuée à chaque tronçon, et les itinéraires sont calculés en en tenant compte.
 
 Les lieux publics (point d’eau, boutiques, cafés, lieux culturels ou sportif, administration...) présents sur openstreetmap sont également proposés à l’autocomplétion, et les informations présentes (horaires, téléphone, ...) affichées.

 L'option "passer par " permet des recherches du type "de chez moi à mon café préféré en passant par une boulangerie".

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


Algos
=====

D’un point de vue algorithmique, on trouvera ici:

- quelques variantes de Dijkstra : passer par un sommet d’une étape intermédiaire (aller de A à B en passant par une boulangerie) ou par une arête (aller de A à B en empruntant la rue R);
- des arbres lexicographiques, un calcul de la distance de Levenshtein (pour trouver le nom de rue le plus proche de celui tapé par l’utilisateur), et une complétion avec tolérance à un nombre fixé de fautes de frappes;
- des Q-arbres et le calcul de l’arête la plus proche par branch and bound;
- un petit réseau de neurones.
