
À FAIRE :


Supprimer folium de carte_cycla pour pouvoir le supprimer définitivement.

Y-a-t-il encore des requête overpass dans la lecture des étapes ?

Améliorer l’initialisation des lieux
	- Ne pas faire une recherche ds la base pour récupérer le type de lieu dans Lieu.of_dico. Passer type_lieu en arg.

nom des arêtes
	- pour affichage dans «enregistrer contrib »
	
	

Type polyline de Django pour le champ nœuds des rues



BUG de la place Clémenceau. Il semble qu’il y manque des arêtes.



Recherche dans l’arbre lex dans la complétion automatique, avec tolérance à faute de frappe.
    -> Mettre le nom de rue aux feuilles


Rechargement et entraînement pratique...
   - apprentissage auto. Tous les chemin qui ont un score de dernière modif>0
   - réinit base ?



Tester vue générique pour chemins


corriger géom ville
Graphe des villes
Recherche dans ville voisine


modif du graphe:
      - place_en_clique


NOTES :


Vaut-il mieux mettre les nœuds d'une rue en texte dans la base, ou avec une relation many to many ? Benchmarking ?



À FAIRE (un jour)


Si un sommet change lors d’une màj de g, que se passe-t-il dans le cache ? -> recréer (à partir de la liste des chemins) ou supprimer le cache lors d’une màj ?

Y-a-t-il des risques de conflit si deux utilisateurs en même temps ?

- Gestion des transitions entre deux rues.
  	  - rajouter un coeff de transition entre deux arêtes

