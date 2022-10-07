
À FAIRE :

Y-a-t-il encore des requête overpass dans la lecture des chemins ?

Améliorer l’initialisation des lieux
	- Ne pas faire une recherche ds la base pour récupérer le type de lieu dans Lieu.of_dico. Passer type_lieu en arg.

nom des arêtes
	- pour affichage dans «enregistrer contrib »
	
	
Ménage:
   - static dans dijk

Amenities :
	Afficher le nom dans les popups
	
    Faire un passer par un(e) ...

	Faire des regroupements, comme « logement », « restauration »
		- Table GroupeDeTypes
		- init : charger les groupes dans le fichier de config, créer des singletons pour ce qui reste.
		- changer le formulaire de recherche. Au passage : chercher dans la bb plutôt qu’avec un rayon.

AutourDeMoi:
	recherche dans le cadre d’affichage


Type polyline de Django pour le champ nœuds des rues



BUG de la place Clémenceau. Il semble qu’il y manque des arêtes.



Recherche dans l’arbre lex dans la complétion automatique, avec tolérance à faute de frappe.
    -> Mettre le nom de rue aux feuilles


Rechargement et entraînement pratique...
   - apprentissage auto. Tous les chemin qui ont un score de dernière modif>0
   - réinit base ?


Mettre une case à cocher pour enregistrer dans le cache ?
   -> utils.itinéraire renvoie les corrections qui ont été faites
   -> voir le template rés_itinéraire_base
Voire récup dans osm tous les noms de lieux ?



Tester vue générique pour chemins


corriger géom ville
Graphe des villes
Recherche dans ville voisine


modif du graphe:
      - place_en_clique


NOTES :


Vaut-il mieux mettre les nœuds d'une rue en texte dans la base, ou avec une relation many to many ? Benchmarking ?



À FAIRE (un jour)

Afficher les étapes sur la carte


Si un sommet change lors d’une màj de g, que se passe-t-il dans le cache ? -> recréer (à partir de la liste des chemins) ou supprimer le cache lors d’une màj ?

Mettre une case pour donner un bonus/malus à une rue dans la recherche ?

Y-a-t-il des risques de conflit si deux utilisateurs en même temps ?

- Accélérer l'apprentissage ?
  	    Éliminer au fur et à mesure les zones où plus de changement
  	    Sauvegarder les trajets calculé par Dijkstra ?


- Gestion des transitions entre deux rues.
  	  - rajouter un coeff de transition entre deux arêtes

