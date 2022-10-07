- Dans crée_graphe.py:
       charge_graphe : rien -> g


- Dans numéros_rues.py:
       extrait_rue_num_coords(chemin=CHEMIN_XML_COMPLET, bavard=0): prend le .osm complet et crée CHEMIN_RUE_NUM_COORDS
       	   Ce dernier contient   ville;rue: (nums impairs, coords);(nums pairs, coords)


- Dans nœuds_des_rues.py:
       Besoin que les villes aient été rentrées dans g via ajoute_villes dans ajoute_villes.py, qui a besoin de CHEMIN_NŒUDS_VILLE
       sortie_csv(g:grapheMinimaliste) -> CHEMIN_NŒUDS_RUES
           Lequel contient Ville;rue;nœuds


- Dans ajoute_villes.py:
       liste_villes() : variable globale avec liste des villes -> liste des villes
       crée_csv() : CHEMIN_RUE_NUM_COORDS -> CHEMIN_NŒUDS_VILLES   (contient ville;nœuds)


- Dans élaguage.py:
       élague_xml(chemin=CHEMIN_XML_COMPLET):   CHEMIN_XML_COMPLET -> CHEMIN_XML