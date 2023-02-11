# -*- coding:utf-8 -*-

"""
Arbres quaternaires. Le type correspond plutôt aux R-arbres, mais la fonction of_list crée dans le cas général quatre fils par nœud.
"""


from time import perf_counter
from math import cos, pi
from dijk.progs_python.petites_fonctions import distance_euc, R_TERRE, chrono, deuxConséc, fusionne_tab_de_tab, zip_dico, sauv_objets_par_lots


def produit_scalaire(u, v):
    return sum(ui*vi for (ui, vi) in zip(u, v))


def union_bb(lbb):
    """
    Entrée : une liste de bounding box
    Sortie : la plus petite bounding box contenant celles de lbb
    """
    return (
        min(bb[0] for bb in lbb),
        min(bb[1] for bb in lbb),
        max(bb[2] for bb in lbb),
        max(bb[3] for bb in lbb)
    )


def fonction_distance_pour_feuille(départ: (float, float), arrivée: (float, float), coords: (float, float)):
    """
    Entrée : début et fin d’un segment d’arête. coords d’un autre point.
    Sortie : distance entre le point et le segment.
    """
    
    lon_d, lat_d = départ
    lon_a, lat_a = arrivée

    le_cos = cos(lat_a*pi/180)  # Je considère que c’est le même que pour lat_d.
    vec_ad = ((lon_d-lon_a)*le_cos, lat_d-lat_a)
    

    x, y = coords
    vec_ac = ((x-lon_a)*le_cos, y-lat_a)


    if produit_scalaire(vec_ad, vec_ac) <= 0:
        # Le point de a le plus proche est son arrivée
        return distance_euc(coords, (lon_a, lat_a))

    elif produit_scalaire(vec_ad, ((x-lon_d)*le_cos, y-lat_d)) >= 0:
        # Le point le plus proche est le départ de a.
        return distance_euc(coords, (lon_d, lat_d))

    else:
        # Le point le plus proche est dans le segment a.
        # La distance au carré est AC**2 - <AB|AC>/AD**2
        d_carré = produit_scalaire(vec_ac, vec_ac) - produit_scalaire(vec_ad, vec_ac)**2 / produit_scalaire(vec_ad, vec_ad)
        # Si la distance est trop petite, on va se retrouver avec un d_carré<0 à cause des erreurs des flottants
        if abs(d_carré) < 10**-18:  # Cela fera de l’ordre de 1cm sur le résultat final.
            return 0.
        else:
            return d_carré ** .5 * pi/180 * R_TERRE



    

class Quadrarbre():
    """
    Attributs :
        fils (tuple de Quadarbres)
        bb (float, float, float, float) : bounding box minimale contenant les nœuds de l’arbre. (s,o,n,e)
        étiquette : doit être munie d’une méthode « coords » qui renvoie (lon, lat).
        distance (pour les feuilles) : fonction qui a une coords associe la distance à la feuille.
    """

    def __init__(self):
        """
        Fonction init bidon car cette classe ne sera jamais utilisée seule : que des sous-classes.
        """
        pass
        # self.fils = None
        # self.bb = None
        # self.étiquette = None
        # self.distance = None

    def __lt__(self, autre):
        """
        Sert dans la recherche de l’étiquette la plus proche, quand on trie selon la distance à la bbox.
        """
        return True
        
    @classmethod
    def of_list(cls, l, f_lon, f_lat, feuille):
        
        """
        Entrée :
            l, liste d’objets à mettre dans l’abre.
            f_lon, fonction qui a un objet de l associe la longitude selon laquelle trier.
            f_lat, fonction qui a un objet de l associe la latitude selon laquelle trier.
            feuille, fonction qui a un objet associe la feuille correspondante.
        Sortie (Quadrarbre) : arbre quad contenant les éléments l.
        """
        
        assert isinstance(l, list), f"Pas une liste : {l}"
        assert l, "Reçu une liste vide"

        if len(l) == 1:
            return feuille(l[0])
        
        else:
            l.sort(key=f_lon)  # tri selon la longitude.
            ouest = l[:len(l)//2]
            est = l[len(l)//2:]

            ouest.sort(key=f_lat)  # tri selon la latitude
            so = ouest[:len(ouest)//2]
            no = ouest[len(ouest)//2:]

            est.sort(key=f_lat)  # tri selon la latitude
            se = est[:len(est)//2]
            ne = est[len(est)//2:]

            res = cls()
            res.fils = tuple(cls.of_list(sl) for sl in (so, no, ne, se) if sl)
            res.bb = union_bb(tuple(f.bb for f in res.fils))
            return res

    
    def __len__(self):
        """ Renvoie le nb de feuilles."""
        if self.fils is None:
            return 1
        else:
            return sum(len(f) for f in self.fils)

        
    def bbox_contient(self, bb: (float, float, float, float)) -> bool:
        """
        Indique si bb est inclue dans self.bb
        """
        s, o, n, e = bb
        ss, os, ns, es = self.bb
        return ss <= s and n <= ns and os <= o and e <= es

    
    def __contains__(self, nœud):
        """
        Indique si nœud figure parmis les descendants de self.
        """
        if self == nœud:
            return True
        else:
            for f in self.fils:
                if f.bbox_contient(nœud.bb) and nœud in f:
                    return True
            return False
        
    
    def majorant_de_d_min(self, coords: (float, float)):
        """
        Sortie : en O(1) un majorant de la plus petite distance entre coords et un élément de l’arbre. (Pour le branch and bound de la recherche de nœud le plus proche.)
        Basé sur le fait qu’il existe au moins un objet sur chaque bord de la bbox.
        """

        s, o, n, e = self.bb
        # Il existe au moins un élément sur chaque bord de la bounding box
        dno = distance_euc(coords, (o, n))
        dso = distance_euc(coords, (o, s))
        dne = distance_euc(coords, (e, n))
        dse = distance_euc(coords, (e, s))
        
        # Il existe un élément sur le bord ouest
        d1 = max(dno, dso)
        # bord est
        d2 = max(dne, dse)
        # sud
        d3 = max(dse, dso)
        # nord
        d4 = max(dno, dne)
        
        return min(d1, d2, d3, d4)
    
    
    def minorant_de_d_min(self, coords: (float, float)):
        """
        Sortie : en O(1), un minorant de la distance min entre coords et un nœud de l’arbre.
        C’est la distance entre coords et la bounding box de self.
        """
        s, o, n, e = self.bb
        lon, lat = coords  # lon : ouest-est
        res_carré = 0
        le_cos = cos(lat*pi/180)
        
        if lon < o:
            res_carré += (o-lon)**2 * le_cos
        elif lon > e:
            res_carré += (lon-e)**2 * le_cos
        if lat < s:
            res_carré += (s-lat)**2
        elif lat > n:
            res_carré += (lat-n)**2
        
        return res_carré**.5 * R_TERRE * pi/180

    
    # exemple : Barthou/SaintLouis (-0.37054131408589847, 43.295030439425645)
    # (-0.371292129834015, 43.29535229996814)
    def étiquette_la_plus_proche(self, coords: (float, float)):
        """
        Sortie (étiquette×float) : (étiquette, distance) de la feuille plus la proche de coords.
        """
        
        if not self.fils:
            return self.étiquette, self.distance(coords)
        
        else:
            d_min = float("inf")
            res = None
            for m, fils in sorted( ((f.minorant_de_d_min(coords), f) for f in self.fils) ):  # On commence par le fils qui a le plus probablement le nœud le plus proche.
                if m < d_min:
                    s, dist = fils.étiquette_la_plus_proche(coords)
                    if dist < d_min:
                        d_min, res = dist, s
            return res, d_min


    def sauv(self, chemin):
        """
        Sauvegarde l’arbre dans le fichier situé à chemin, via un parcours en profondeur.
        On suppose que les étiquettes ont un attribut pk, c’est ce qui sera inscrit dans le fichier.
        """

        with open(chemin, "w") as sortie:
            def aux(a):
                if a.fils:
                    # Nœud interne
                    sortie.write(f"N{','.join(map(str, a.bb))},{len(a.fils)}\n")
                    for f in a.fils:
                        aux(f)
                else:
                    # Feuille
                    sortie.write( f"F{','.join(map(str, a.bb))},{a.étiquette}\n"  )
            aux(self)


    def sous_arbre_contenant_naïf(self, l: list):
        """
        Renvoie le plus petit sous-arbre de self contenant les éléments de l.
        Algo naïf...
        """
        print(f"Arrivée au nœud {self}")
        for f in self.fils:
            if all(n in f for n in l):
                return f.sous_arbre_contenant_naïf(l)
        return self

    def toutes_les_feuilles(self)->list:
        """
        Renvoie la liste des feuilles de self
        """
        if self.fils:
            res = []
            for f in self.fils:
                res.extend(f.toutes_les_feuilles())
            return res
        else:
            return [self]

    
    @classmethod
    def of_fichier(cls, chemin: str, récup_objet, feuille):
        """
        Entrées :
             chemin, adresse du fichier
             récup_objet, fonction qui à la chaîne écrite dans le fichier associe l’objet à mettre dans les étiquettes des feuilles. (Fonction réciproque du __str__ de l’étiquette.)
             feuille, fonction qui à l’objet associe la feuille.
        """
        with open(chemin) as entrée:
            def aux():
                
                ligne = entrée.readline().strip()
                
                if ligne[0] == "F":
                    s,o,n,e, c = ligne[1:].split(',')
                    étiquette = récup_objet(c)
                    return feuille(étiquette)
                
                elif ligne[0] == "N":
                    s, o, n, e, nb_fils = ligne[1:].split(',')
                    res = cls()
                    res.bb = tuple(map(float, (s,o,n,e)))
                    res.fils = [aux() for _ in range(int(nb_fils))]
                    return res

                else:
                    raise RuntimeError(f"Ligne ne commençant ni par F ni par N : {ligne}")
                
            return aux()





class QuadrArbreSommet(Quadrarbre):
    """
    Conçu pour des objets ponctuels (une seule coord).
    """
    
    def __init__(self):
        pass
                

    @classmethod
    def feuille(cls, s):
        """ feuille contenant le sommet s."""
        lon, lat = s.coords()
        res = cls()
        res.bb = lat, lon, lat, lon  # bbox réduite à un point.
        res.étiquette = s
        res.distance = lambda c: distance_euc(s.coords(), c)
        return res

    
    @classmethod
    def of_list(cls, l):
        return super().of_list(l, lambda x:x.coords()[0], lambda x:x.coords()[1], cls.feuille)

    


class ArêteSimplifiée():
    """
    Classe pour représenter des segments faisant partie d’arêtes de la base Django.

    Attributs:
        départ (float×float) : coordonnées d’une extrémité
        arrivée (float×float)  : coordonnées de l’autre extrémité
        pk (int) : pk de l’arête django contenant celle-ci.
    """
    def __init__(self, départ, arrivée, pk):
        self.départ = départ
        self.arrivée = arrivée
        self.pk = pk

    def __str__(self):
        lon_d, lat_d = self.départ
        lon_a, lat_a = self.arrivée
        return f"{lon_d};{lat_d};{lon_a};{lat_a};{self.pk}"


class QuadrArbreArête(Quadrarbre):
    """
    Prévu pour contenir des arêtes.
    En pratique, les étiquettes doivent avoir un attribut « départ » et « arrivée », qui renvoient des objets ayant un attribut « coords ».
    Les arêtes sont supposées être des segments : découper au préalable en cas de géométrie plus complexe.
    """

    def __init__(self, *args, **kwargs):
        self.fils = None
        self.bb = None
        self.distance = None
        self.etiquette = None


    @classmethod
    def feuille(cls, a):
        """
        Entrée : a (ArêteSimplifiée)
        Sortie : la feuille correspondante. càd un objet de cls dont fils vaut None et étiquette vaut a. Muni également de la méthode distance qui prend des coords et renvoie la distance entre celle-ci et l’arête.
        """
        
        lon_d, lat_d = a.départ
        lon_a, lat_a = a.arrivée
        assert (lon_a, lat_a) != (lon_d, lat_d)
        o, e = sorted((lon_d, lon_a))
        s, n = sorted((lat_d, lat_a))
        res = cls()
        res.bb = (s, o, n, e)
        
        res.étiquette = a

        res.distance = lambda coords: fonction_distance_pour_feuille(a.départ, a.arrivée, coords)
        return res

    
    @classmethod
    def of_list(cls, l):
        return super().of_list(l, lambda x:x.départ[0], lambda x:x.départ[1], cls.feuille)

    
    @classmethod
    def of_list_darêtes_d(cls, l):
        """
        Entrée : l, liste de mo.Arête. Plus précisèment, les objets de l doivent avoir une méthode « géométrie » qui renvoie une liste de coords, et un attribut pk (clef primaire).
        Sortie : arbre quad contenant les ArêteSimplifiée obtenues en découpant les Arêtes selon leur géom.
        Les arêtes sont désorientées : une seule est gardée en cas d’aller-retour.
        """
        lf = []
        déjà_vues = set()
        for a_d in l:
            for (d, a) in deuxConséc(a_d.géométrie()):
                (d, a) = sorted((d, a))
                if not (d, a) in déjà_vues:
                    lf.append(ArêteSimplifiée(d, a, a_d.pk))
                    déjà_vues.add((d, a))
        return cls.of_list(lf)
    

    @classmethod
    def of_ville(cls, v_d):
        return cls.of_list_darêtes_d(list(v_d.arêtes()))

    
    @classmethod
    def of_fichier(cls, chemin, bavard=0):
        """
        """
        tic = perf_counter()
        def arête_of_str(c):
            lon_d, lat_d, lon_a, lat_a, pk = c.split(";")
            dép = tuple(map(float, (lon_d, lat_d)))
            arr = tuple(map(float, (lon_a, lat_a)))
            return ArêteSimplifiée(dép, arr, int(pk))
        res = super().of_fichier(
            chemin,
            arête_of_str,
            cls.feuille
        )
        chrono(tic, f"Chargement de l’arbre des arêtes depuis {chemin}", bavard=bavard)
        return res


    def vers_django(self, nv_nœud, nv_segment, père):
        """
        Entrées:
            crée_nœud : fonction à utiliser pour créer un nœud. En pratique, models.ArbreArête.
            crée_segment : fonction à utiliser pour créer un segment d’arête. Sera mis dans le champ « segment » des feuilles. En pratique models.SegmentArête.
            père (models.ArbreArête ou None) : le père du nœud actuel.

        Sortie :
            (feuiles, nœuds), où:
                   - nœuds contient les objets Django qui représentent l’arbre. Il faut encore les sauver étage par étage à cause des contraintes de clef étrangère.  Tableau de tableaux où les nœuds sont rangés par profondeur. Racine en tête.
                   - feuilles contient les segments d’arête nécessaires aux feuilles : à sauver en dernier.
        """

        nœuds = []
        feuilles = []

        données = zip_dico(["borne_sud", "borne_ouest", "borne_nord", "borne_est"], self.bb)  # Pour envoyer à nv_nœud pour créer le nœud actuel.
        données["père"] = père
        nœud_actuel = nv_nœud(**données)
        nœuds.append([nœud_actuel])
        
        if self.fils is None:
            # Cas d’une feuille : on crée un segment d’arête qu’on relie à nœud_actuel.
            d_lon, d_lat = self.étiquette.départ
            a_lon, a_lat = self.étiquette.arrivée
            feuilles.append(nv_segment(
                arête_id=self.étiquette.pk,  # self.étiquette est une instance de ArêteSimplifiée. pk est la pk de l’arête complète la contenant.
                d_lon=d_lon, d_lat=d_lat,
                a_lon=a_lon, a_lat=a_lat,
                feuille=nœud_actuel
            ))

        else:
            for f in self.fils:
                feuilles_de_f, nœuds_de_f = f.vers_django(nv_nœud, nv_segment, nœud_actuel)
                fusionne_tab_de_tab(nœuds, [[]]+nœuds_de_f)
                feuilles.extend(feuilles_de_f)
            
        return feuilles, nœuds


    def sauv_dans_base(self, nv_nœud, nv_segment):
        """
        Effet : sauve l’arbre dans la base.
        Sortie : racine de l’objet mo.ArbreArête
        """
        print("Création des objets")
        feuilles, nœuds = self.vers_django(nv_nœud, nv_segment, None)
        print(f"Fini. {len(feuilles)} feuilles et {len(nœuds)} nœuds.\n")

        print("Sauvegarde des nœuds")
        # La racine
        nœuds[0][0].save()
        num_étage = 1
        for étage in nœuds[1:]:     # De haut en bas
            print(f"étage {num_étage}")
            num_étage += 1
            for n in étage:
                n.père_id = n.père.id
            sauv_objets_par_lots(étage)

        print("Ajout du feuille_id dans les feuilles (pour vieille version de Django)")
        for f in feuilles:
            f.feuille_id = f.feuille.id  # f.feuille.id a été créé lors de la sauvegarde de f.feuille ci dessus, mais f.feuille_id n’avait pas été mis à jour...
            
        print("Sauvegarde des segments d’arêtes des feuilles")
        sauv_objets_par_lots(feuilles)
        return nœuds[0][0]
    

