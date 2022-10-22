# -*- coding:utf-8 -*-
from petites_fonctions import chrono
from time import perf_counter

tic=perf_counter()
import networkx as nx
chrono(tic, "networkx", bavard=2)

from petites_fonctions import distance_euc, LOG
#from time import perf_counter
from params import LOG_PB, D_MAX_POUR_NŒUD_LE_PLUS_PROCHE#, CHEMIN_CACHE, CHEMIN_CYCLA

# tic=perf_counter()
# from osmnx import nearest_nodes
# chrono(tic, "osmnx (pour nearest_nodes)", bavard=1)

class Graphe_nx():
    """
    Classe de graphe basée sur le graphe networkx tiré d’osm.
    Pour être utilisé lors de la phase d’initialisation quand aucune donnée n’a encore été obtenue.
    Munie tout de même des méthodes rue_dune_arête et ville_dune_sommet. Le première fonctionne grâce au champ « name » présent dans les arêtes dans le graphe renvoyé par osm. La seconde grâce au dico ville_of_nœud, rempli par ajoute_villes.

    Attributs:
        multidigraphe
        digraphe
        villes_of_nœud : dictionnaire nœud -> liste des villes
    """
    
    def __init__(self, g):
        """ Entrée : g, MultiDiGraph de networkx"""
        self.multidigraphe = g
        print("Calcul de la version sans multiarêtes")
        #tic= perf_counter()
        self.digraphe = nx.DiGraph(g)  # ox.get_digraph(g)
        #chrono(tic, "conversion en digraph simple.")

        # Anciennement dans la classe Graphe:
        self.villes_of_nœud = {}
        self.cyclabilité = {}
        self.cache_lieu = {}  # le cache chaîne de car tapée -> nœuds
        self.nœuds = {}  # donne les nœuds de chaque rue

    def __contains__(self, n):
        """ Indique si le nœud n est dans g"""
        return n in self.digraphe.nodes
    
    def voisins_nus(self, s):
        """ Itérateur sur les voisins de s, sans la longueur de l’arête."""
        return self.digraphe[s].keys()

    
    def est_arête(self, s, t):
        return t in self.digraphe[s]

    
    def nb_arêtes(self):
        return sum(len(self.digraphe[s]) for s in self.digraphe.nodes)

    
    def geom_arête(self, s, t):
        """
        Entrée : deux sommets s et t tels que (s, t) est une arête
        Sortie : (liste des coordonnées décrivant la géométrie de l’arête la plus courte de s à t, nom de l’arête).
        Obtenues dans l’attribut geometry de l’arête.
        """
        
        arête = min((a for _,a in self.multidigraphe[s][t].items()), key=lambda a: a["length"] )
        if "name" in arête:
            nom=arête["name"]
        else:
            nom=None
        return arête["geometry"].coords, nom
    

    def nom_arête(self,s,t):
        try:
            return self.digraphe[s][t]["name"]
        except Exception as e:
            return None
    
    def coords_of_nœud(self, n):
        """ Renvoie le couple (lon, lat)
         dans osmnx : x=lon, y=lat.
        """
        return self.multidigraphe.nodes[n]["x"], self.multidigraphe.nodes[n]["y"]


    def simplifie(self):
        """
        Supprime tous les attributs des arêtes, hormis 'length', 'name' et 'geometry'
        """
        à_garder=["length", "name", "geometry"]
        for s in self.multidigraphe.nodes:
            for t in self.multidigraphe[s]:
                for i in self.multidigraphe[s][t]:
                    à_supprimer = [att for att in self.multidigraphe[s][t][i] if att not in à_garder ]
                    for att in à_supprimer:
                        self.multidigraphe[s][t][i].pop(att)
        

    
    def rue_dune_arête(self, s, t, bavard=0):
        """ Liste des couple (nom, est_une_place_piétonne) des rues contenant l’arête (s,t). Le plus souvent un singleton.
            Renvoie None si celui-ci n’est pas présent (pas de champ "name" dans les données de l’arête)."""
        res = []
        for a in self.multidigraphe[s][t].values():
            if "name" in a:
                piétonne = a.get("highway")=="pedestrian"
                if isinstance(a["name"], str):
                    res.append((a["name"], piétonne and "place" in a["name"].lower()))
                else:
                    res.extend( (r, piétonne and "place" in r.lower()) for r in a["name"])
        if len(res)==0:
            LOG(f"L’arête {(s, t)} n’a pas de nom. Voici ses données\n {self.digraphe[s][t]}", bavard=bavard)
        return res

    ### Remplacé par villes_dun_sommet
    # def ville_dune_arête(self, s, t, bavard=0):
    #     """ Liste des villes contenant l’arête (s,t).
    #     """
    #     try:
    #         return self.digraphe[s][t]["ville"] 
    #     except KeyError:
    #         if bavard>0: print(f"Pas de ville en mémoire pour l’arête {s,t}.  Voici ses données\n {self.digraphe[s][t]}")
    #         return []

    def villes_dun_sommet(self, s, bavard=0):
        """
        Entrée : s (int), sommet du graphe.
        Sortie : liste des villes de ce sommet.
        """
        try:
            return self.villes_of_nœud[s]
        except KeyError:
            if bavard>0: print(f"Pas de ville en mémoire pour le sommet {s}.  Voici ses données\n {self.digraphe[s]}.")
            return []

    def nb_arêtes_avec_ville(self):
        return sum(
            len([t for t in self.digraphe[s] if "ville" in self.digraphe[s][t]])
            for s in self.digraphe.nodes 
        )
    
    def parcours_largeur(self, départ, dmax=float("inf")):
        """Itérateur sur les sommets du graphe, selon un parcours en largeur depuis départ. On s’arrête lorsqu’on dépasse la distance dmax depuis départ."""
        àVisiter = deque()
        déjàVu = set({})
        àVisiter.appendleft((départ, 0))
        fini = False
        while len(àVisiter) > 0 and not fini:
            (s, d) = àVisiter.pop()
            if d > dmax: fini = True
            else:
                yield s
                for t in self.digraphe[s].keys():
                    if t not in déjàVu:
                        àVisiter.appendleft((t, d+1))
                        déjàVu.add(t)

    def vers_csv(self, chemin):
        """
        Crée un csv avec la liste des arêtes et leurs longueurs.
        """
        with open(chemin,"w") as sortie:
            for s in self.digraphe.nodes:
                for t, données in self.digraphe[s].items():
                    sortie.write(f"{s},{t},{données['length']}\n")

    def voisins(self, s, p_détour, interdites={}):
        """
        La méthode utilisée par dijkstra. Renvoie les couples (voisin, longueur de l'arrête) issus du sommet s.
        La longueur de l'arrête (s, t) est sa longueur physique divisée par sa cyclabilité (s'il y en a une).
        Paramètres :
             - p_détour (float) : proportion de détour accepté.
             - interdites : arêtes interdites.
        """
        #assert s in self.digraphe.nodes, f"le sommet {s} reçu par la méthode voisins n’est pas dans le graphe"
        # Formule pour prendre en compte p_détour : cycla**(p_détour*1.5)
        def cycla_corrigée(voisin):
            return self.cyclabilité.get((s, voisin), 1.)**( p_détour*1.5)
        if s in interdites:
            return ( ( voisin, données["length"]/cycla_corrigée(voisin) )
                     for (voisin, données) in self.digraphe[s].items() if voisin not in interdites[s]
                    )
        else:
            return ( ( voisin, données["length"]/cycla_corrigée(voisin) )
                     for (voisin, données) in self.digraphe[s].items()
                    )

    def longueur_arête(self, s, t):
        return self.digraphe[s][t]["length"]

    # Supprimé car nécessite de charger osmnx
    # def nœud_le_plus_proche(self, coords, recherche = "", d_max = D_MAX_POUR_NŒUD_LE_PLUS_PROCHE ):
    #     """
    #     recherche est la recherche initiale qui a eu besoin de cet appel. Uniquement pour compléter l’erreur qui sera levée si le nœud le plus proche est à distance > d_max.
    #     Les coords doivent être dans l’ordre (lon, lat).
    #     """
        
    #     n, d = nearest_nodes(self.multidigraphe, *coords, return_dist = True)
    #     if d > d_max:
    #         print(f" Distance entre {self.coords_of_nœud(n)} et {coords} supérieure à {d_max}.")
    #         raise TropLoin(recherche)
    #     else:
    #         return n

    def incr_cyclabilité(self, a, dc):
        """ Augmente la cyclabilité de l'arête a (couple de nœuds), ou l'initialise si elle n'était pas encore définie.
            Met à jour self.cycla_max si besoin
        Formule appliquée : *= (1+dc)
        """
        assert dc > -1, "Reçu un dc <= -1 "
        if a in self.cyclabilité:
            self.cyclabilité[a] *= (1+dc)
            if self.cyclabilité[a]>self.cycla_max:
                self.cycla_max=self.cyclabilité[a]
        else: self.cyclabilité[a] = 1. + dc

    def réinitialise_cyclabilité(self):
        self.cyclabilité = {}

    def rue_of_nœud(self, n):
        """ renvoie le nom de la rue associée dans le cache au nœud n"""
        for c, v in self.cache_lieu.items():
            if n in v:
                return c
        raise KeyError("Le nœud {n} n'est pas dans le cache")

    def charge_cache(self):
        print("Chargement du cache cache_lieu.")
        entrée = open(CHEMIN_CACHE, encoding="utf-8")
        for ligne in entrée:
            c, v = ligne.strip().split(":")
            l = list(map(int, v.split(",")))
            self.cache_lieu[c] = l
        entrée.close()

    def vide_cache(self):
        print("J’efface le cache des adresses")
        entrée = open(CHEMIN_CACHE, "w", encoding="utf-8")
        entrée.close()
        self.cache_lieu={}

    def nœuds_of_rue(self, ville_n, rue_n):
        """
        Entrées : ville_n, rue_n (str) : noms normalisés d’une ville et d’une rue de celle-ci.
        Sortie : la liste des nœuds en mémoire pour la rue indiquée.
        """
        if ville_n in self.nœuds and rue_n in self.nœuds[ville_n]:
            return self.nœuds[ville_n][rue_n]
        else:
            return None
        
    def nœuds_of_cache(self, texte):
        """
        Renvoie les nœuds associés à texte dans le cache, ou None si texte n’est pas présent
        """
        if texte in self.cache_lieu:
            return self.cache_lieu[texte]
        else:
            return None

    def met_en_cache(self, texte, nœuds):
        """
        Associe dans le cache nœuds à la valeur texte.
        """
        self.cache_lieu[texte]=nœuds
       
    def sauv_cycla(self):
        """ enregistre l’état actuel de la cyclabilité"""
        print("Sauvegarde de la cyclabilité")
        sortie = open(CHEMIN_CYCLA, "w", encoding="utf-8")
        for (s, t), v in self.cyclabilité.items():
            sortie.write(f"{s};{t};{v}\n")
        sortie.close()

    def charge_cycla(self):
        """ Charge la  cycla depuis le csv, et enregistre le max en attribut du graphe.
        Renvoie la cyclabilité maximale.
        """
        print("Chargement de la cyclabilité")
        entrée = open(CHEMIN_CYCLA, encoding="utf-8")
        maxi=0
        for ligne in entrée:
            s, t, v = ligne.strip().split(";")
            s=int(s); t=int(t); v=float(v)
            maxi=max(v, maxi)
            self.cyclabilité[(s, t)] = v
        entrée.close()
        self.cycla_max = maxi
        return maxi


def vérif_arêtes(g):
    """ Vérifie que les arêtes de g sont bien des couples de sommets de g."""
    res = []
    for s in g.digraphe.nodes:
        for t in g.voisins_nus(s):
            if t not in g.digraphe.nodes:
                res.append(t)
        for t, _ in g.voisins(s, 0):
            if t not in g.digraphe.nodes:
                res.append(t)
    return res
