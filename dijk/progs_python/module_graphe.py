# -*- coding:utf-8 -*-
from petites_fonctions import chrono
from time import perf_counter

# tic=perf_counter()
# import networkx as nx
# #from networkx import Digraph
# chrono(tic, "networkx", bavard=2)
# tic=perf_counter()
# from osmnx import nearest_nodes #plot_graph,
# chrono(tic, "osmn.nearest_nodes", bavard=2)
# import os


from params import LOG_PB, D_MAX_POUR_NŒUD_LE_PLUS_PROCHE, CHEMIN_CACHE, CHEMIN_CYCLA, LOG
import dijkstra
from recup_donnees import coords_lieu, cherche_lieu, nœuds_sur_tronçon_local
from lecture_adresse.normalisation import VILLE_DÉFAUT, normalise_rue
from petites_fonctions import distance_euc, deuxConséc, sauv_fichier
from collections import deque
#from dijk.progs_python.lecture_adresse.recup_nœuds import tous_les_nœuds
#from graphe_minimal import Graphe_minimaliste

#from graphe_par_networkx import Graphe_nw # À terme, cet import doit disparaître
from graphe_par_django import Graphe_django


class PasTrouvé(Exception):
    pass

class TropLoin(Exception):
    """ Pour le cas où le nœud de g trouvé serait trop loin de l’emplacement initialement recherché."""
    pass


class Graphe_mélange(Graphe_django): #, Graphe_nw):
    """
    Ceci devrait être temporaire...
    Prend les méthode en priorité dans la classe Graphe_django, et se rabat sur la classe Graphe_nw si elles ne sont pas implémentées.
    """
    def __init__(self, g):
        """
        Entrée : g, graphe de networkx
        """
        #Graphe_nw.__init__(self, g)
        Graphe_django.__init__(self)

        
class Graphe():
    """
    Attributs : - g, instance de Graphe_nw ou de Graphe_django.
    Cette classe sert juste à permettre d’avoir indifféremment un graphe networkx ou enregistré dans la bdd de django dans le reste du code.
    (Est-ce vraiment utile ?)

    """
   
    def __init__(self, gr):
        """ Entrée : gr, instance de Graphe_nw ou de Graphe_django."""
        self.g=gr
        self.cycla_max = self.g.cycla_max()
        self.cycla_min = self.g.cycla_min()


    ### "Fausses méthodes", elles ne font qu’appeler la méthode correspondante de self.g
    def __contains__(self, n):
        return n in self.g

    def voisins(self, s, p_détour, interdites={}):
        return self.g.voisins(s , p_détour, interdites=interdites)
        
    def coords_of_nœud(self,n):
        return self.g.coords_of_id_osm(n)

    def coords_of_id_osm(self,n):
        return self.g.coords_of_id_osm(n)
    
    def d_euc(self, n1, n2):
        """ distance euclidienne entre n1 et n2."""
        return distance_euc(self.coords_of_nœud(n1), self.coords_of_nœud(n2))

    def liste_voisins(self, s):
        return list(self.voisins)

    
    def nœuds_of_cache(self, texte):
        """
        Renvoie les nœuds associés à texte dans le cache, ou None si texte n’est pas présent
        """
        return self.g.nœuds_of_cache(texte)

    def met_en_cache(self, texte, nœuds):
        """
        Associe dans le cache nœuds à la valeur texte.
        """
        return self.g.met_en_cache(texte, nœuds)

    def nœuds_of_rue(self, adresse, bavard=0):
        """
        Entrées : adresse (normalisation.Adresse)
        Sortie : la liste des nœuds en mémoire pour la rue indiquée.
        """
        try:
            return self.g.nœuds_of_rue(adresse, bavard=bavard)
        except Exception as e:
            LOG(f"Pas trouvé dans g.nœuds_of_rue les nœuds de {adresse}  {e}", bavard=bavard)
            return None
    
    def longueur_arête(self, s, t):
        return self.g.longueur_arête(s,t)

    def nœud_le_plus_proche(self, coords, recherche = "", d_max = D_MAX_POUR_NŒUD_LE_PLUS_PROCHE ):
        """
        recherche est la recherche initiale qui a eu besoin de cet appel. Uniquement pour compléter l’erreur qui sera levée si le nœud le plus proche est à distance > d_max.
        Les coords doivent être dans l’ordre (lon, lat).
        """
        return self.g.nœud_le_plus_proche(coords, recherche=recherche, d_max=d_max)


    def incr_cyclabilité(self, a, dc):
        """ 
        Augmente la cyclabilité de l'arête a (couple de nœuds), ou l'initialise si elle n'était pas encore définie.
        Met à jour self.cycla_max si besoin
        Formule appliquée : *= (1+dc)
        """
        self.g.incr_cyclabilité(a, dc)
        self.cycla_max=self.g.cycla_max

        
    def rue_of_nœud(self, n):
        """ renvoie le nom de la rue associée dans le cache au nœud n"""
        return self.g.rue_of_nœuds(n)
       

    def voisins_nus(self, n):
        """ Itérateur sur les voisins de s, sans la longueur de l’arête."""
        return self.g.voisins_nus(n)

    def geom_arête(self,s,t,p):
        """
        Entrée : deux sommets s et t tels que (s,t) est une arête
                 p, proportion détour
        Sortie : liste des coordonnées décrivant la géométrie de l’arête, nom de l'arête
        """
        return self.g.geom_arête(s,t,p)

    ### Méthodes vraiment créées dans cette classe. ###
    
    # def longueur_itinéraire(self, iti):
    #     """
    #     Entrée : un itinéraire (liste de sommets)
    #     Sortie : partie entière de sa « vraie » longueur.
    #     """
    #     return int(sum(self.longueur_arête(s,t) for s,t in deuxConséc(iti)))

    def longueur_itinéraire(self, iti, p):
        return self.g.longueur_itinéraire(iti, p)
    
    def nom_arête(self,s,t):
        return self.g.nom_arête(s,t)
    
    def chemin(self, d, a, p_détour):
        return dijkstra.chemin(self, d, a, p_détour)
  
    def chemin_étapes_ensembles(self, c, bavard=0):
        """ Entrée : c, objet de la classe Chemin"""
        return dijkstra.chemin_étapes_ensembles(self, c, bavard=bavard)

         

        
    # def nœud_centre_rue(self, nom_rue, ville=VILLE_DÉFAUT, pays="France"):
    #     """ Renvoie le nœud le plus proche des coords enregistrées dans osm pour la rue.
    #     Pb si trop de nœuds ont été supprimés par osmnx ? """
    #     coords = coords_lieu(nom_rue, ville=ville, pays="France")
    #     return self.nœud_le_plus_proche(coords)

    # def un_nœud_sur_rue(self, nom_rue,  ville=VILLE_DÉFAUT, pays="France"):
    #     """
    #     OBSOLÈTE
    #     Renvoie un nœud OSM de la rue, qui soit présent dans le graphe. Renvoie le nœud médian parmi ceux présents.
    #     Si échec, renvoie un nœud le plus proche de la coordonnée associé à la rue par Nominatim."""
    #     raise RuntimeError("Cette fonction n’est plus censée être utilisée")
    #     nom_rue = nom_rue.strip()
    #     ville = ville.strip()
    #     pays = pays.strip()
    #     clef = f"{nom_rue},{ville},{pays}"
     
    #     def renvoie(res):
    #         self.nœud_of_rue[clef] = res
    #         print(f"Mis en cache : {res} pour {clef}")
    #         return res
     
    #     if clef in self.nœud_of_rue:  # Recherche dans le cache
    #         return self.nœud_of_rue[clef]
    #     else:
    #         #try:
    #             print(f"Recherche d'un nœud pour {nom_rue}")
    #             nœuds = nœuds_rue_of_adresse(self.digraphe, nom_rue, ville=ville, pays=pays)
    #             n = len(nœuds)
    #             if n > 0:
    #                 return renvoie(nœuds[n//2])
    #             else:
    #                 print(f"Pas trouvé de nœud exactement sur {nom_rue} ({ville}). Je recherche le nœud le plus proche.")
    #                 return renvoie(self.nœud_centre_rue(nom_rue, ville=ville, pays=pays))
    #         #except Exception as e:
    #         #    print(f"Erreur lors de la recherche d'un nœud sur la rue {nom_rue} : {e}")

               


    def sauv_cache(self):
        """ L’adresse du fichier csv est dans CHEMIN_CACHE."""
        sauv_fichier(CHEMIN_CACHE)
        sortie = open(CHEMIN_CACHE, "w", encoding="utf-8")
        
        for c, v in self.g.cache_lieu.items():
            à_écrire = ",".join(map(str, v))
            sortie.write(f"{c}:{à_écrire}\n")
        sortie.close()




