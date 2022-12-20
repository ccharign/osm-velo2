# -*- coding:utf-8 -*-

from time import perf_counter
import os
from django.db.models import Max, Min, Subquery
from django.db import transaction, close_old_connections

from dijk.models import Rue, Ville, Arête, Sommet, Cache_Adresse, Zone, Ville_Zone
import dijk.models as mo

import recup_donnees as rd
from params import LOG, DONNÉES, LOG_PB
from petites_fonctions import deuxConséc, chrono, distance_euc
import dijkstra
from lecture_adresse.arbresLex import ArbreLex
import lecture_adresse.normalisation as no
#from quadrarbres import QuadrArbreArête


class VillePasTrouvée(Exception):
    pass


class Itinéraire():
    """
    Pour enregistrer le résultat d’un Dijkstra.
    Attributs:
        liste_sommets (int list)
        liste_arêtes (Arête list)
        longeur (float), longeur ressentie
        couleur (str)
    """
    
    def __init__(self, g, sommets, longeur: float, couleur: str, p_détour: float):
        self.liste_sommets = sommets
        self.liste_arêtes = g.liste_Arête_of_iti(sommets, p_détour)
        self.longueur = longeur
        self.couleur = couleur

    def longueur_vraie(self):
        """
        Renvoie la longeur physique de l’itinéraire.
        """
        return sum(a.longueur for a in self.liste_arêtes)

    def liste_coords(self):
        """
        Sortie  ((float×float) list) : liste des (lon,lat) décrivant l’itinéraire.
        """
        res = []
        for a in self.liste_arêtes:
            res.extend(a.géométrie())
        return res

    def vers_leaflet(self, nom_carte="laCarte"):
        """
        Sortie (str) : code js pour afficher l’itinéraire.
        """
        return f"""
        var ligne = L.polyline({[[lat,lon] for lon,lat in self.liste_coords()]}, {{color: '{self.couleur}'}}).addTo({nom_carte});
        """

    def bbox(self, g):
        cd = g.coords_of_id_osm(self.liste_sommets[0])
        ca = g.coords_of_id_osm(self.liste_sommets[-1])
        o, e = sorted((cd[0], ca[0]))  # lon
        s, n = sorted((cd[1], ca[1]))  # lat
        return s, o, n, e

    
class Graphe_django():
    """
    Cette classe sert d'interface avec la base Django.
    Attribut:
        dico_voisins (dico int -> (int, Arête) list) associe à un id_osm la liste de ses (voisins, arête)
        dico_Sommet (dico int->Sommet) associe le sommet à chaque id_osm
        arbre_villes : arbre lex des villes (toutes les villes de la base pour l’instant). Noms normalisée.
        cycla__min
        cycla__max
        zones (liste de Zone)
        ville_défaut (instance de models.Ville)
        arbres_des_rues : dico (ville_norm -> ArbreLex)
        arbre_arêtes : dico (nom de zone -> arbreQuad des arêtes).
        arbre_lex_zone : dico (zone -> ArbreLex des noms de rue) (Pour autocomplétion)
    """
    
    def __init__(self):
        self.dico_voisins = {}
        self.cycla_max = {}
        self.cycla_min = {}
        self.arbre_villes = ArbreLex()
        self.dico_Sommet = {}
        self.dico_voisins = {}
        self.arbres_des_rues = {}
        self.zones = []
        self.cycla_max = {}
        self.cycla_min = {}
        self.arbre_cache = {}
        self.arbre_arêtes = {}
        self.arbre_lex_zone = {}
    
        
    def charge_zone(self, zone_t, bavard=0):
        """
        Charge les données présentes dans la base concernant la zone indiquée.
        """
        close_old_connections()
        z_d = Zone.objects.get(nom=zone_t)
        if z_d not in self.zones:
            print(f"Zone pas en mémoire : {z_d}. Voici les zones que j’ai chargées : {self.zones}")

            dossier_données = os.path.join(DONNÉES, str(z_d))
            os.makedirs(dossier_données, exist_ok=True)
            
            ## Dicos des villes et des rues
            print("Chargement des arbres lex pour villes et rues...")
            tic = perf_counter()
            self.arbre_lex_zone[z_d] = ArbreLex()
            for v_d in z_d.villes():
                self.arbre_villes.insère(v_d.nom_norm)
                self.arbres_des_rues[v_d.nom_norm] = ArbreLex.of_fichier(os.path.join(DONNÉES, v_d.nom_norm))
                self.arbre_lex_zone[z_d].rajoute(self.arbres_des_rues[v_d.nom_norm])
            chrono(tic, " les arbres lex.")

            
            ## Cache
            print("Chargement du cache")
            villes = Ville_Zone.objects.filter(zone=z_d)
            self.arbre_cache[zone_t] = ArbreLex.of_iterable(
                [str(a.adresse) for a in Cache_Adresse.objects.filter(ville__in=Subquery(villes.values("ville")))]
            )

            ## Sommets
            tic = perf_counter()

            for s in z_d.sommets():
                self.dico_Sommet[s.id_osm] = s
                self.dico_voisins[s.id_osm] = []
            tic = chrono(tic, "Chargement des sommets")

            
            ## Arêtes
            d_arête_of_pk = {}  # Pour le chargement de l’arbre quad.
            arêtes_de_z = z_d.arêtes()
            cyclaMin = float("inf")
            cyclaMax = 0.
            for a in arêtes_de_z:
                cyclaMax = max(cyclaMax, a.cyclabilité())
                cyclaMin = min(cyclaMin, a.cyclabilité())
                s = a.départ.id_osm
                t = a.arrivée.id_osm
                d_arête_of_pk[a.pk] = a
                if a.cyclabilité() > 0:  # ceci supprime les autoroutes actuellement
                    self.dico_voisins[s].append((t, a))
            tic = chrono(tic, "Chargement des arêtes.")

            ## Vérif que les sommets d’arrivée sont dans le dico des sommets
            print("Vérif que les sommets d’arrivée sont connus")
            for l in self.dico_voisins.values():
                for s, _ in l:
                    assert t in self.dico_Sommet
            print("C’est bon")
            
            ## Arbre quad des arêtes:
            #chemin = os.path.join(dossier_données, f"arbre_arêtes_{z_d}")
            tic = perf_counter()
            #LOG(f"Chargement de l’arbre quad des arêtes depuis {chemin}", bavard=bavard)
            LOG("Chargement de l’arbre des arêtes dans la base")
            #self.arbre_arêtes[z_d.nom] = QuadrArbreArête.of_fichier(chemin)
            self.arbre_arêtes[z_d.nom] = mo.ArbreArête.racine()
            tic = chrono(tic, "Chargement de l’arbre quad des arêtes", force=True)
                
                
            ## Cycla min et max
            self.cycla_max[z_d] = cyclaMax
            self.cycla_min[z_d] = cyclaMin
            # self.calcule_cycla_min_max(z_d)
            # chrono(tic, "Calcul des cycla min et max", force=True)
            
            self.zones.append(z_d)
            
        else:
            print(f"Zone déjà en mémoire : {z_d}.")
        return z_d


    def vérif_zone(self, z_t):
        """
        Indique si toutes les arêtes de la zone ont leurs extrémités dans la zone.
        """
        z_d = Zone.objects.get(nom=z_t)
        arêtes = Arête.objects.filter(zone=z_d).prefetch_related("départ", "arrivée")
        for a in arêtes:
            if a.départ.id_osm not in self:
                raise RuntimeError(f"Le départ de l’arête {a} n’est pas dans le graphe pour la zone {z_d}")
            if a.arrivée.id_osm not in self:
                raise RuntimeError(f"L’arrivée de l’arête {a} n’est pas dans le graphe pour la zone {z_d}")
        return True

    
    def __contains__(self, s):
        """
        Entrée : s (int)
        Sortie : il existe un sommet d'identifiant osm s dans la base.
        """
        return Sommet.objects.filter(id_osm=s).exists()

    
    def coords_of_Sommet(self, s):
        return s.coords()

    def coords_of_id_osm(self, s):
        #return Sommet.objects.get(id_osm=s).coords()
        return self.dico_Sommet[s].coords()


    def d_euc(self, s, t):
        cs, ct = self.coords_of_id_osm(s), self.coords_of_id_osm(t)
        return distance_euc(cs, ct)

    def supprime_sommets_isolés(self):
        """
        Supprime de la base les sommets desquels aucune arête ne part.
        """
        à_supprimer = []
        for s_d in self.dico_Sommet.values():
            if len(s_d.voisins_nus()) == 0:
                à_supprimer.append(s_d)
        print(f"Sommets à supprimer : {à_supprimer}")
        with transaction.atomic():
            for s_d in à_supprimer:
                s_d.delete()
                

    def ville_la_plus_proche(self, nom, tol=2):
        """
        Entrée : nom (str), nom normalisé par partie_commune ou pas d’une ville.
        Sortie (Ville) : instance de models.Ville dont le nom normalisé est le plus proche de partie_commune(nom). La distance est la distance d’édition.
        Paramètres :
            tol (int) : nb max de fautes de frappe. Si aucune ville à au plus tol fautes de frappe, lève l’exception VillePasTrouvée.
        """
        noms_proches = self.arbre_villes.mots_les_plus_proches(no.partie_commune(nom), d_max=tol)[0]
        if len(noms_proches) == 0:
            raise VillePasTrouvée(f"Pas trouvé de ville à moins de {tol} fautes de frappe de {nom}. Voici les villes que je connais : {self.arbre_villes.tous_les_mots()}.")
        elif len(noms_proches) > 1:
            raise VillePasTrouvée(f"Jai plusieurs villes à même distance de {nom}. Il s’agit de {noms_proches}.")
        else:
            nom_norm, = noms_proches
            return Ville.objects.get(nom_norm=nom_norm)
    
    
    def meilleure_arête(self, s, t, p_détour):
        """
        Renvoie l'arête (instance d'Arête) entre s et t de longueur corrigée minimale.
        """
        données = ((a.longueur_corrigée(p_détour), a) for (v, a) in self.dico_voisins[s] if v==t)
        _, a = min(données)
        return a

    
    def longueur_meilleure_arête(self, s, t, p_détour):
        longueurs = (a.longueur_corrigée(p_détour) for (v, a) in self.dico_voisins[s] if v==t)
        return min(longueurs)

    
    def geom_arête(self, s, t, p_détour):
        """
        Renvoie la géométrie de la plus courte arête de s à t, compte tenu de la proportion de détour indiquée.
        """
        a = self.meilleure_arête(s, t, p_détour)
        return a.géométrie(), a.nom

    
    def incr_cyclabilité(self, a, p_détour, dc):
        """
        Augmente la cyclabilité de l'arête a (couple de nœuds), ou l'initialise si elle n'était pas encore définie.
        Met à jour self.cycla_max si besoin
        Formule appliquée : *= (1+dc)
        """
        s, t = a
        a_d = self.meilleure_arête(s, t, p_détour)
        a_d.incr_cyclabilité(dc)
        a_d.save()
        # Il faudrait avoir la zone...
        # if dc > 0:
        #     self.cycla_max = max(self.cycla_max, a_d.cycla)
        # else:
        #     self.cycla_min = min(self.cycla_min, a_d.cycla)

        
    def calcule_cycla_min_max(self, z_d, arêtes=None):
        if not arêtes:
            arêtes = z_d.arêtes()
            
        cycla_min = arêtes.aggregate(Min("cycla"))["cycla__min"]
        cycla_défaut_min = arêtes.aggregate(Min("cycla_défaut"))["cycla_défaut__min"]
        if cycla_min is None:
            self.cycla_min[z_d] = cycla_défaut_min
        else:
            self.cycla_min[z_d] = min(cycla_défaut_min, cycla_min)

        cycla_max = arêtes.aggregate(Max("cycla"))["cycla__max"]
        cycla_défaut_max = arêtes.aggregate(Max("cycla_défaut"))["cycla_défaut__max"]
        if cycla_max is None:
            self.cycla_max[z_d] = cycla_défaut_max
        else:
            self.cycla_max[z_d] = max(cycla_défaut_max, cycla_max)
            
        print(f"Cycla min et max : {self.cycla_min[z_d]}, {self.cycla_max[z_d]}")

        
    def liste_Arête_of_iti(self, iti, p_détour):
        return [self.meilleure_arête(s,t,p_détour) for (s,t) in deuxConséc(iti)]

    
    def itinéraire(self, chemin, couleur, bavard=0):
        """
        Entrée : chemin (Chemin)
        Sortie : iti_d, l_ressentie (liste d'Arêtes, float)
        """
        iti, l_ressentie = dijkstra.iti_étapes_ensembles(self, chemin, bavard=bavard)
        #return self.liste_Arête_of_iti(iti, chemin.p_détour), l_ressentie
        return Itinéraire(self, iti, l_ressentie, couleur, chemin.p_détour)

    def itinéraire_sommets(self, chemin, bavard=0):
        """
        Entrée : chemin (Chemin)
        Sortie : iti, l_ressentie (int list, float)
        """
        return dijkstra.iti_étapes_ensembles(self, chemin, bavard=bavard)
    
    
    def longueur_itinéraire(self, iti_d):
        """
        Entrée : iti_d (Arête list)
        Sortie : la vraie longueur de l'itinéraire. Arrondie à l’entier inférieur.
        """
        return int(sum(a.longueur for a in iti_d.liste_arêtes))


    def tous_les_nœuds(self):
        return Sommet.objects.all()


    def voisins(self, s: int, p_détour: float, interdites={}):
        """
        La méthode utilisée par dijkstra.
        Entrées :
            - s (int)
            - p_détour (float), proportion de détour accepté.
            - interdites (dico Sommet -> liste de Sommets), arêtes interdites.

        La méthode utilisée par dijkstra. Renvoie les couples (voisin, longueur de l'arrête) issus du sommet s.
        La longueur de l'arrête (s, t) renvoyée est sa longueur physique divisée par sa cyclabilité**(p_détour*1.5).
        """
        tout = [ (t, a.longueur_corrigée(p_détour) ) for (t, a) in self.dico_voisins[s]]
        if s in interdites:
            return [(t, l) for (t, l) in tout if t not in interdites[s]]
        else:
            return tout

        
    def voisins_nus(self, s):
        return [t for (t, _) in self.dico_voisins[s]]

        
    def nœuds_of_rue(self, adresse, persévérant=True, bavard=0):
        """
        Entrées : adresse (Adresse)
        Sortie : la liste des nœuds pour la rue indiquée.
                 Essai 1 : recherche dans la base (utilise adresse.rue_norm)
                 Essai 2 : via Nominatim et overpass, par recup_donnees.nœuds_of_rue. Ceci récupère les nœuds des ways renvoyés par Nominatim.
                 Essai 3 (si persévérant) recherche dans la bounding box enveloppante des nœuds trouvés à l’essai 2.
                    En cas d'essai 2 concluant, le résultat est rajouté dans la table des Rues.
        """
        
        try:
            # Essai 1 : dans la base
            v = Ville.objects.get(nom_norm=adresse.ville.nom_norm)
            r = Rue.objects.get(nom_norm=adresse.rue_norm, ville=v)
            res = r.nœuds()
            LOG(f"(g.nœuds_of_rue) Trouvé dans la base {list(res)} pour {adresse}", bavard=bavard)
            return res
        
        except Exception as e:
            LOG(f"(graphe_par_django.nœuds_of_rue) Rue pas en mémoire : {adresse} (erreur reçue : {e}), je lance recup_donnees.nœuds_of_rue", bavard=bavard)
            
            # Essai 2 : via rd.nœuds_of_rue, puis intersection avec les nœuds de g
            tout = rd.nœuds_of_rue(adresse)
            LOG(f"(g.nœuds_of_rue) Liste des nœuds osm : {tout}.", bavard=bavard-1)
            res = [ n for n in tout if n in self ]
            if len(res)>0:
                LOG(f"(g.nœuds_of_rue) nœuds trouvés : {res}", bavard=bavard)
                self.ajoute_rue(adresse, res, bavard=bavard)
                return res
            else:
                LOG(f"mais aucun n’est dans le graphe :(", bavard=bavard)
            
            if persévérant and len(tout)>0:
                # essai 3 : recherche de tous les nœuds dans la bb enveloppante de tout.
                bbe = rd.bb_enveloppante(tout, bavard=bavard-1)
                tol=0
                dtol=0.001
                while len(res)==0:
                    LOG(f"(g.nœuds_of_rue) Recherche dans la bb enveloppante avec tol={tol}.", bavard=bavard)
                    res = [ n for n in rd.nœuds_dans_bb(bbe, tol=tol) if n in self]
                    tol+=dtol
                self.ajoute_rue(adresse, res, bavard=bavard)
                return res
            else:
                return []
            # else:
            #     LOG("Aucun de ces nœuds n’est dans g :(. Je calcule les nœuds connectés:", bavard=bavard)
            #     reliés = rd.nœuds_reliés(tout)
            #     if bavard>0: print(f"nœuds reliés : {reliés}")
            #     res = [n for n in rd.nœuds_reliés(tout) if n in self ]
            #     if bavard>0: print(f"Parmi ceux-ci, voici ceux qui sont dans g : {res}")
            #     if len(res)>0:
            #         #self.ajoute_rue(adresse, res, bavard=bavard)
            #         return res

    
    def ajoute_rue(self, adresse, nœuds, bavard=0):
        """
        Effet : ajoute la rue dans la base si elle n'y est pas encore.
        """
        LOG(f"J'ajoute la rue {adresse} dans la base. Nœuds : {nœuds}", bavard=1)
        ville_d = Ville.objects.get(nom_norm=adresse.ville.nom_norm)
        try:
            r = Rue.objects.get(nom_norm=adresse.rue_norm, ville=ville_d)
            LOG(f"rue déjà présente : {r}", bavard=bavard+1)
        except Exception as e:
            nœuds_à_découper = ",".join(map(str, nœuds))
            rue_d = Rue(nom_complet=adresse.rue(), nom_norm=adresse.rue_norm, ville=ville_d, nœuds_à_découper=nœuds_à_découper)
            rue_d.save()

            
    def met_en_cache(self, adresse, res):
        
        str_ad = adresse.pour_cache()
        v_d = Ville.objects.get(nom_complet=adresse.ville.nom_complet)
        essai = Cache_Adresse.objects.filter(adresse=str_ad, ville=v_d)
        if essai:
            print(f"Déjà dans le cache : {essai.first()}")
            raise ValueError("déjà dans le cache")
        else:
            ligne = Cache_Adresse(
                adresse=str_ad,
                ville=v_d,
                nœuds_à_découper=",".join(map(str, res))
            )
            ligne.save()
            LOG(f"Mis en cache : {ligne}", bavard=1)


    def dans_le_cache(self, adresse: str):
        """
        Entrée : adresse (str)
        Sortie : liste des nœuds si présente dans le cache, None sinon
        À FAIRE : arbre lex
        """
        assert isinstance(adresse, str)
        assert "(" not in adresse, f"Adresse reçue : {adresse}"
        _, _, rue, ville = no.découpe_adresse(adresse)
        print(f"Après découpe_adresse : {rue}, {ville}")
        res = Cache_Adresse.objects.filter(adresse__iexact=rue, ville__nom_complet=ville)
        if len(res) == 1:
            return res[0].nœuds()
        elif len(res) > 1:
            LOG_PB(f"Plusieurs valeurs en cache pour {adresse}")


    def vérif_longeurs_arêtes(self):
        """
        Sortie : le max des rapports (d_euc(s,t) / longueur enregistrée de (s,t))
        """
        rapport_max = 1.
        for s, voisins in self.dico_voisins.items():
            for (t, a) in voisins:
                if a.longueur < self.d_euc(s, t):
                    #raise RuntimeError(f"La longeur de {a} est < à la distance euc entre ses sommets {s} et {t} ({self.d_euc(s, t)}))")
                    rapport_max = max(rapport_max, self.d_euc(s,t)/a.longueur)
        return rapport_max


    def arête_la_plus_proche(self, coords, z_d):
        """
        Renvoie l’arête de l’arbre des arêtes de z_d la plus proche de coords.
        """
        return self.arbre_arêtes[z_d.nom].arête_la_plus_proche(coords)


    def complétion_rue(self, début: str, villes, tol=2, n_max_rés=10):
        """
        Entrées : villes (iterable de models.Ville)
        À l’arrache actuellement.
        """
        res = []
        nb_rés_restant = n_max_rés
        for v_d in villes:
            res_dans_v_d = self.arbres_des_rues[v_d.nom_norm].complétion(
                no.prétraitement_rue(début),
                tol=tol,
                n_max_rés=nb_rés_restant
            )
            if len(res_dans_v_d)==0: return []
            for r in res_dans_v_d:
                res.extend(r)
                nb_rés_restant -= len(r)
                if nb_rés_restant < 0:
                    return []
        return [Rue.objects.get(nom_norm=r) for r in res]

