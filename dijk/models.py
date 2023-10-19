import json
from pprint import pformat
import os
import math
from typing_extensions import Self

from django.db import models, close_old_connections, transaction, connection

from dijk.progs_python.params import LOG, DONNÉES
from dijk.progs_python.lecture_adresse.normalisation0 import partie_commune
import dijk.progs_python.quadrarbres as qa

from dijk.progs_python.lecture_adresse.normalisation0 import prétraitement_rue
from dijk.progs_python.petites_fonctions import deuxConséc


def objet_of_dico(
        cls, d,
        champs_obligatoires=[],
        autres_champs=[],
        dico_champs_obligatoires={},
        dico_autres_champs={},
        autres_valeurs={},
        champs_à_traiter={}
):
    """
    Entrées :
       cls (une classe)
       d (dico str -> *) : les données pour créer le nouvel objet.

       champs_obligatoires (str list)
       autres_champs (str list)
       dico_champs_obligatoirse (dico str->str) : dico nom_de_champ_dans_d -> nom_de_champ_dans_cls
       dico_autres_champs (dico str-> str) : idem
       autres_valeurs (dico str->'a) : données à rajouter directement.
       champs_à_traiter (dico str: str × ('a->'b)) : associe à un nom de champ dans d le nom dans cls et une fonction à appliquer aux données. Ces champs ne sont pas facultatifs.


    Sortie : l’objet créé. Une erreur est levée si un champs de champs_obligatoires n’est pas présent dans d.
    """

    d_nettoyé = {}
    
    # Dico champs obligatoires
    for ci, cf in dico_champs_obligatoires.items():
        if ci not in d:
            raise ValueError(f"(objet_of_dico) Il manque le champ {ci} pour créer un objet de type {cls}.\n Dico reçu : {pformat(d)}\n")
        d_nettoyé[cf] = d[ci]

    # Champs obligatoires
    for c in champs_obligatoires:
        if c not in d:
            raise ValueError(f"(objet_of_dico) Il manque le champ {c} pour créer un objet de type {cls}.\n Dico reçu : {pformat(d)}\n")
        d_nettoyé[c] = d[c]

    # Dico champs facultatifs
    d_nettoyé.update(
        {cf: d.get(ci, None) for (ci, cf) in dico_autres_champs.items()}
    )

    # Champs facultatifs
    d_nettoyé.update(
        {c: d.get(c, None) for c in autres_champs}
    )

    # Autres données
    d_nettoyé.update(autres_valeurs)

    # Champs à traiter
    d_nettoyé.update(
        {cf: f(d[ci]) for (ci, (cf, f)) in champs_à_traiter.items()}
    )
    
    return cls(**d_nettoyé)


def découpe_chaîne_de_nœuds(c: str) -> tuple[int]:
    return tuple(map(int, c.split(",")))


class Ville(models.Model):
    """
    lieux_calculés (date) : pour enregistrer la dernière fois que les lieux ont été mis à jour.
    """
    nom_complet = models.CharField(max_length=100)
    nom_norm = models.CharField(max_length=100)
    code = models.IntegerField(null=True)
    code_insee = models.IntegerField(null=True, default=None, blank=True)
    population = models.IntegerField(null=True, default=None, blank=True)
    #densité = models.SmallIntegerField(null=True, default=None, blank=True)
    superficie = models.FloatField(null=True, default=None, blank=True)
    géom_texte = models.TextField(null=True, default=None, blank=True)
    données_présentes = models.BooleanField(default=False)
    lieux_calculés = models.DateField(null=True, default=None, blank=True)
    #zone = models.ManyToManyField(Zone) # pb car la classe Zone n’est pas encore définie.

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["nom_norm", "code_insee"], name="Le couple (nom_norm, code_insee) doit être unique."),
        ]
    
    def __str__(self):
        return self.nom_complet

    def __gt__(self, autre):
        return self.population > autre.population

    def avec_code(self):
        return f"{self.code} {self.nom_complet}"

    def voisine(self):
        rels = Ville_Ville.objects.filter(ville1=self).select_related("ville2")
        return tuple(r.ville2 for r in rels)

    def zones(self):
        return (rel.zone for rel in Ville_Zone.objects.filter(ville=self).prefetch_related("zone"))

    def arêtes(self):
        return self.arête_set.all()

    def géom(self):
        return json.loads(self.géom_texte)

    def bbox(self):
        """
        Renvoie le plus petit rectangle contenant self au format (s,o,n,e).
        """
        géom = self.géom()
        o = min(lon for (lon, lat) in géom)
        e = max(lon for (lon, lat) in géom)
        s = min(lat for (lon, lat) in géom)
        n = max(lat for (lon, lat) in géom)
        return s, o, n, e
    
    @classmethod
    def of_nom(cls, nom):
        """ Renvoie la ville telle que partie_commune(nom) = ville.nom_norm"""
        return cls.objects.get(nom_norm=partie_commune(nom))

    
    
class Ville_Ville(models.Model):
    """ table d’association pour indiquer les villes voisines."""
    ville1 = models.ForeignKey(Ville, related_name="ville1", on_delete=models.CASCADE)
    ville2 = models.ForeignKey(Ville, related_name="ville2", on_delete=models.CASCADE)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["ville1", "ville2"], name="Pas de relation ville_ville en double."),
        ]



class Sommet(models.Model):
    
    id_osm = models.BigIntegerField(unique=True)
    lon = models.FloatField()
    lat = models.FloatField()
    villes = models.ManyToManyField(Ville)
    
    def __str__(self):
        return str(self.id_osm)

    # Sert dans les tas de Dijkstra au cas où deux sommets aient exactement la même distance au départ
    def __lt__(self, autre):
        return self.id_osm < autre

    def __hash__(self):
        return self.id_osm

    def get_villes(self):
        return self.villes.all()

    def voisins(self, p_détour):
        arêtes = Arête.objects.filter(départ=self).select_related("arrivée")
        return [(a.arrivée, a.longueur_corrigée(p_détour)) for a in arêtes]

    def voisins_nus(self):
        arêtes = Arête.objects.filter(départ=self).select_related("arrivée")
        return [a.arrivée for a in arêtes]

    def coords(self):
        return self.lon, self.lat

    def prédécesseurs(self):
        arêtes = Arête.objects.filter(arrivée=self).select_related("départ")
        return [a.départ for a in arêtes]


# https://docs.djangoproject.com/en/3.2/topics/db/examples/many_to_many/
class Rue(models.Model):
    """
    Une entrée pour chaque couple (rue, ville) : certaines rues peuvent apparaître en double.
    """
    nom_complet = models.CharField(max_length=200)
    nom_norm = models.CharField(max_length=200)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE)
    nœuds_à_découper = models.TextField()  # chaîne de caractères contenant les nœuds à splitter

    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["nom_norm", "ville"], name="une seule rue pour chaque nom_norm pour chaque ville.")
        ]

        
    def __str__(self):
        return f"{self.nom_complet}"
    
    
    def nœuds(self) -> tuple[int]:
        """
        Sortie : tuple des id_osm des nœuds de la rue.
        """
        return découpe_chaîne_de_nœuds(self.nœuds_à_découper)

    
    def géométrie(self) -> list[tuple[float]]:
        """
        Sortie: géométrie de la rue. Liste de (lon,lat).
        Dans le cas où plusieurs arêtes relient deux points, on prend la première...
        """
        res = []
        for (s, t) in deuxConséc(self.nœuds()):
            arête_aller = Arête.objects.filter(départ__id_osm=s, arrivée__id_osm=t)
            if arête_aller:
                res.extend(arête_aller.first().géométrie())
            else:
                arête_retour = Arête.objects.filter(départ__id_osm=t, arrivée__id_osm=s)
                if arête_retour:
                    res.extend(arête_retour.first().géométrie())
        return res

    
    def sommets(self):
        """
        Renvoie le queryset des Sommets de self.
        """
        return Sommet.objects.filter(id_osm__in=self.nœuds())

    
    def pour_autocomplète(self, num, bis_ter):
        à_afficher = ""
        if num:
            à_afficher = f"{num} "
        if bis_ter:
            à_afficher += f"{bis_ter} "
        à_afficher += f"{self}, {self.ville}"
        return {
            "type_étape": "adresse",
            "pk": self.pk,
            "nom": à_afficher,
            "géom": self.géométrie(),
            "avec_num": bool(num),
        }



def formule_pour_correction_longueur(l, cy, p_détour):
    """
    Ceci peut être changé. Actuellement : l / cy**( p_détour*1.5)
    Rappel : cy>1 == bien
             cy<1 == pas bien
    """
    return l / cy**(p_détour*1.5)


def géom_texte(s_d, t_d, ax):
    """
    Entrée : a (dico), arête de nx.
             s_d, t_d (Sommet, Sommet), sommets de départ et d’arrivée de a
             g (Graphe)
    Sortie : str adéquat pour le champ geom d'un objet Arête.
    """
    if "geometry" in ax:
        geom = ax["geometry"].coords
    else:
        geom = (s_d.coords(), t_d.coords())
    coords_texte = (f"{lon},{lat}" for lon, lat in geom)
    return ";".join(coords_texte)


def cycla_défaut(a, sens_interdit=False, pas=1.1):
    """
    Entrée : a, arête d'un graphe nx.
    Sortie (float) : cycla_défaut
    Paramètres:
        pas : pour chaque point de bonus, on multiplie la cycla par pas
        sens_interdit : si Vrai, bonus de -2
    Les critères pour attribuer des bonus en fonction des données osm sont définis à l’intérieur de cette fonction.
    """
    # disponible dans le graphe venant de osmnx :
    # maxspeed, highway, lanes, oneway, access, width
    critères = {
        # att : {val: bonus}
        "highway": {
            "residential": 1,
            "cycleway": 3,
            "step": -10,
            "pedestrian": 1,
            "tertiary": 1,
            "living_street": 1,
            "footway": 1,
        },
        "maxspeed": {
            "10": 3,
            "20": 2,
            "30": 1,
            "70": -2,
            "90": -4,
            "130": -float("inf")
        },
        "sens_interdit": {True: -5}
    }
    bonus = 0
    if sens_interdit:
        bonus += critères["sens_interdit"][True]
    for att in critères:
        if att in a:
            val_s = a[att]
            if isinstance(val_s, str) and val_s in critères[att]:
                bonus += critères[att][val_s]
            elif isinstance(val_s, list):
                for v in val_s:
                    if v in critères[att]:
                        bonus += critères[att][v]
    return pas**bonus



def longueur_arête(s_d, t_d, a):
    """
    Entrées : a (dic), arête de nx
              g (graphe_par_django)
    Sortie : min(a["length"], d_euc(s,t))
    """
    #deuc = distance_euc(s_d.coords(), t_d.coords())
    # if a["length"] < deuc:
    #     print(f"Distance euc ({deuc}) > a['length'] ({a['length']}) pour l’arête {a} de {s_d} à {t_d}")
    #     return deuc
    # else:
    return a["length"]


class Arête(models.Model):
    """
    Attributs:
        départ (Sommet)
        arrivée (Sommet)
        longueur (float)
        cycla (float) : cyclabilité calculée par l'IA. None par défaut.
        cycla_défaut (float) : cyclabilité obtenue par les données présentes dans osm. Via la fonction vers_django.cycla_défaut lors du remplissage de la base.
        rue (Rue). Pour l’instant pas utilisé.
        geom (string). Couples lon,lat séparés par des ;
        nom (str)
        villes ( ManyToMany)
        sensInterdit (BooleanField)
    """
    départ = models.ForeignKey(Sommet, related_name="sommet_départ", on_delete=models.CASCADE, db_index=True)
    arrivée = models.ForeignKey(Sommet, related_name="sommet_arrivée", on_delete=models.CASCADE)
    longueur = models.FloatField()
    cycla = models.FloatField(blank=True, null=True, default=None)
    cycla_défaut = models.FloatField(default=1.0)
    rue = models.ManyToManyField(Rue)
    geom = models.TextField()
    nom = models.CharField(max_length=200, blank=True, null=True, default=None)
    villes = models.ManyToManyField(Ville)
    sensInterdit = models.BooleanField(default=False)

    def __eq__(self, autre):
        return self.geom == autre.geom
    
    # Sert dans meilleure_arête en cas d’égalité des longueurs
    def __lt__(self, autre):
        return self.id < autre
    def __gt__(self, autre):
        return self.id > autre
    
    def __hash__(self):
        return self.pk
    
    def __str__(self):
        return f"{self.id} : ({self.départ}, {self.arrivée}, longueur : {self.longueur}, géom : {self.geom}, nom : {self.nom})"


    def get_villes(self):
        return self.villes.all()

    @classmethod
    def of_arête_nx(cls, s_d: Sommet, t_d: Sommet, a_nx):
        """
        Entrées:
            a_nx, arête d’un multidigraph netwokx
        """
        return cls(départ=s_d,
                   arrivée=t_d,
                   nom=a_nx.get("name", None),
                   longueur=longueur_arête(s_d, t_d, a_nx),
                   cycla_défaut=cycla_défaut(a_nx),
                   geom=géom_texte(s_d, t_d, a_nx)
                   )

    def géométrie(self):
        """
        Sortie ( float*float list ) : liste de (lon, lat) qui décrit la géométrie de l'arête.
        """
        res = []
        for c in self.geom.split(";"):
            lon, lat = c.split(",")
            res.append((float(lon), float(lat)))
        return res

    def cyclabilité(self):
        if self.cycla is not None:
            return self.cycla
        else:
            return self.cycla_défaut

    def incr_cyclabilité(self, dc):
        assert dc > 0, f"j’ai reçu dc={dc}."
        if self.cycla is not None:
            self.cycla *= dc
        else:
            self.cycla = self.cycla_défaut * dc
        self.save()
    
    def longueur_corrigée(self, p_détour):
        """
        Entrée : p_détour (float), proportion de détour.
        Sortie : Longueur corrigée par la cyclabilité.
        """
        cy = self.cyclabilité()
        assert cy > 0, f"cyclabilité ⩽ pour l’arête {self}. Valeur : {cy}."
        return formule_pour_correction_longueur(self.longueur, cy, p_détour)



class ArbreArête(models.Model, qa.Quadrarbre):
    """
    Enregistre un nœud (interne ou feuille) d’un arbre quad.
    C’est le père qui est enregistré. Clef étrangère en cascade donc supprimer la racine supprime tout l’arbre.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # la bbox
    borne_sud = models.FloatField()
    borne_ouest = models.FloatField()
    borne_nord = models.FloatField()
    borne_est = models.FloatField()

    @property
    def bb(self):
        """
        Pour compatibilité avec la classe quadrarbres.QuadrArbre. Renvoie la bb du nœuds courant.
        """
        return self.borne_sud, self.borne_ouest, self.borne_nord, self.borne_est

    @property
    def étiquette(self):
        return self.segment().arêteSimplifiée()
    

    # Si c’est une feuille : un segment d’Arête
    # mais c’est le segment qui a l’attribut vers sa feuille

    # Le père
    père = models.ForeignKey("self", null=True, related_name="related_manager_fils", on_delete=models.CASCADE)

    @property
    def bbox(self):
        return (self.borne_sud, self.borne_ouest, self.borne_nord, self.borne_est)

    def distance(self, coords: (float, float)):
        """
        Précondition : self est une feuille.
        Sortie (float) : distance entre le point de coordonnées coords et le segment représenté par self.
        """
        if not self.fils:
            seg = self.segment()
            res = qa.fonction_distance_pour_feuille(seg.départ, seg.arrivée, coords)
            if not isinstance(res, float):
                breakpoint()
                raise RuntimeError("distance pas réelle")
            return res
        else:
            raise ValueError(f"{self} n’est pas une feuille.")

        
    @property                   # getter
    def fils(self):
        """
        Sortie : queryset des fils de self
        """
        return self.related_manager_fils.all()

    
    @classmethod
    def effaceTout(cls):
        """
        Supprime toutes les entrées directement via du sql, dans les tables des ArbreArête et des SegmentArête.
        """
        with connection.cursor() as cursor:

            requête = 'DELETE FROM {}'.format(cls._meta.db_table)
            print(requête)
            cursor.execute(requête)
            
            requête = 'DELETE FROM {}'.format(SegmentArête._meta.db_table)
            print(requête)
            cursor.execute(requête)


    def ancètre(self):
        """
        Renvoie le nœud le plus haut duquel descend self.
        """
        if self.père is None:
            return self
        else:
            return self.père.ancètre()

        
    def sous_arbre_contenant(self, l):
        """
        Renvoie le plus petit sous-arbre de self contenant tous les éléments de l.
        Algo semi-naïf : on rassemble les frères entre eux tant que possible avant de lancer l’algo naïf (qui est dans la classe générale QuadrArbre)
        """
        print(f"(sous_arbre_contenant) Reçu une liste de {len(l)} feuiles.")

        fini = False
        fils = l
        étage = 0
        
        
        while not fini:
            # Invariant : fils ne doit pas contenir la racine. Càd tous les éléments de fils ont un père.
            
            pères = {}          # dico père-> fils dans fils
            for f in fils:
                p = f.père
                if p not in pères: pères[p] = []
                pères[p].append(f)
                
            # On garde à présent les pères ayant plusieurs fils et les fils uniques
            fini = True
            fils = []
            for (p, fs) in pères.items():
                if len(fs) == 1:  # fils unique
                    fils.append(fs[0])
                else:
                    if p.père is None:
                        print(f"Je suis tombé sur la racine {p}")
                        return p
                    fils.append(p)
                    fini = False
            print(f"Étage {étage} fini. {len(fils)} nœuds restant.")
            étage += 1
        print(f"Après rassemblement des frères il reste {len(fils)} nœuds. Je lance l’algo naïf.")
        return self.sous_arbre_contenant_naïf(fils)
                
            

    # Maintenant il y a plusieurs arbres dans la base. Ne plus utiliser ceci!
    @classmethod
    def uneRacine(cls) -> Self:
        """
        Renvoie une racine d’un arbre la base. Obtenu en remontant depuis le premier élément de la base.
        """
        return cls.objects.all().first().ancètre()


    def getZones(self):
        """
        Sortie: querySet des zones associées à cet arbre. (Càd la racine de l’arbre associé à la zone est self.)
        """
        return Zone.objects.filter(arbre_arêtes=self)
    
    def segment(self):
        """
        Précondition : self est une feuille.
        Renvoie l’objet SegmentArête associé à self.
        """
        segments = tuple(self.related_manager_segment.all())
        if len(segments) == 1:
            return segments[0]
        else:
            raise ValueError(f"{self} ne semble pas être une feuille. J’ai obtenu {len(segments)} segments associés. Ce sont {segments}.")
    
    
    def arête_la_plus_proche(self, coords: (float, float)):
        """
        Sortie : (arête django la plus proche de coords, distance)
        """
        a, d = self.étiquette_la_plus_proche(coords)  # a est une ArêteSimplifiée
        a_d = Arête.objects.get(pk=a.pk)
        return a_d, d
    
    
    @transaction.atomic
    def supprime_n_feuilles(self, n: int):
        """
        Effet : supprime en une seule transaction n feuilles de self. Si self a moins de n feuilles, elles seront toutes supprimées.
        Sortie : nombre de feuilles supprimées
        (Utile pour supprimer l’arbre sur un système avec peu de mémoire)
        """
        
        if self.fils:
            n_restant = n
            for f in self.fils:
                n_restant -= f.supprime_n_feuilles(n_restant)
                if n_restant == 0:
                    return n
            return n-n_restant
        
        else:
            self.delete()
            return 1

        
    def supprime_aieul(self, n: int):
        """
        Supprime le nœuds situé n étage au dessus de self. Vu les contraintes cascade, ça va supprimer tous les cousins du même coup.
        """
        if n == 0:
            self.delete()
        else:
            self.père.supprime_aieul(n-1)

    
    def supprime_étage(self, prof: int):
        """
        Supprime l’étage à la profondeur prof.
        """
        if prof == 0:
            print(self.delete())
        else:
            for f in self.fils:
                f.supprime_étage(prof-1)


    def supprime(self):
        """
        Efface l’arbre issu de self.
        """
        hauteur = int(math.log(ArbreArête.objects.all().count(), 4))  # Approximation de la hauteur
        for prof in range(hauteur-6, 0, -5):
            print(f"(Suppression de l’étage {prof})")
            self.supprime_étage(prof)
        
        print("Suppression de la racine")
        print(self.delete())
    


class SegmentArête(models.Model):
    """
    Enregistre un segment d’une arête. Sera attaché à une feuille de l’arbre d’Arêtes.
    """
    # l’Arête complète contenant le segment
    arête = models.ForeignKey(Arête, on_delete=models.CASCADE, related_name="segments")
    # départ
    d_lon = models.FloatField()
    d_lat = models.FloatField()
    # arrivée
    a_lon = models.FloatField()
    a_lat = models.FloatField()

    feuille = models.ForeignKey(ArbreArête, on_delete=models.CASCADE, related_name="related_manager_segment")

    @property
    def départ(self):
        return self.d_lon, self.d_lat

    @property
    def arrivée(self):
        return self.a_lon, self.a_lat

    def arêteSimplifiée(self):
        """
        Renvoie l’objet ArêteSimplifiée correspondant.
        """
        return qa.ArêteSimplifiée(self.départ, self.arrivée, self.arête.pk)

    
class Zone(models.Model):
    """
    Une zone délimite une zone dont le graphe sera mis en mémoire au chargement.
    """
    nom = models.CharField(max_length=100, unique=True)
    ville_défaut = models.ForeignKey(Ville, on_delete=models.CASCADE)
    arbre_arêtes = models.ForeignKey(ArbreArête, on_delete=models.SET_NULL, null=True)
    inclue_dans = models.ForeignKey("self", related_name="related_manager_sous_zones", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    cycla_min = models.FloatField(default=1.0)
    cycla_max = models.FloatField(default=1.0)
    
    class Meta:
        ordering = ["nom"]
    
    def villes(self) -> tuple:
        return tuple(rel.ville for rel in Ville_Zone.objects.filter(zone=self).prefetch_related("ville"))

    def sousZones(self):
        """
        Renvoie les sous-zones de self.
        """
        filles = self.related_manager_sous_zones

    def plusGrandeZoneContenant(self) -> Self:
        """
        Renvoie la plus grande zone dans laquelle self est inclue, pour la relation inclue_dans
        """
        if not self.inclue_dans:
            return self
        else:
            return self.inclue_dans.plusGrandeZoneContenant()

        
    def estInclueDans(self, autre) -> bool:
        """
        Indique si autre figure parmi les zones contenant self.
        """
        if self == autre:
            return True
        if not self.inclue_dans:
            return False
        return self.inclue_dans.estInclueDans(autre)

    
    def arêtes(self):
        """
        Sortie (queryset) : les arêtes des villes de la zone
        """
        villes = self.villes()
        return Arête.objects.filter(villes__in=villes, cycla_défaut__gt=0.0).prefetch_related("départ", "arrivée")

    
    def sommets(self):
        """
        Générateur des sommets de self.
        """
        for v in self.villes():
            for s in v.sommet_set.all():
                yield s

    
    def ajoute_ville(self, ville):
        if ville not in self.villes():
            rel = Ville_Zone(ville=ville, zone=self)
            rel.save()
            

    def associeArbreArêteAncètre(self):
        """
        Associe à self l’arbreArête de la plus grande zone contenant self.
        """
        ancètre = self.plusGrandeZoneContenant()
        self.arbre_arêtes_id = ancètre.arbre_arêtes_id
        self.save()

        
    def __str__(self):
        return self.nom

    
    def __hash__(self):
        return self.pk


    def calculeCyclaMinEtMax(self):
        """
        Rema : pour cycla__min, la cycla défaut n’est prise en compte que si aucune arête ne dispose de cycla.
               pour cycla_max en revanche elle est toujours prise en compte.
        """
        arêtes = self.arêtes()
            
        self.cycla_min = arêtes.aggregate(models.Min("cycla"))["cycla__min"]
        
        if self.cycla_min is None:
            cycla_défaut_min = arêtes.aggregate(models.Min("cycla_défaut"))["cycla_défaut__min"]
            self.cycla_min = cycla_défaut_min
        # else:
        #     self.cycla_min = min(cycla_défaut_min, cycla_min)

        cycla_max = arêtes.aggregate(models.Max("cycla"))["cycla__max"]
        cycla_défaut_max = arêtes.aggregate(models.Max("cycla_défaut"))["cycla_défaut__max"]
        if cycla_max is None:
            self.cycla_max = cycla_défaut_max
        else:
            self.cycla_max = max(cycla_défaut_max, cycla_max)
            
        print(f"Cycla min et max pour la zone {self}: {self.cycla_min}, {self.cycla_max}")
        self.save()

    
    def sauv_csv(self, chemin_csv=DONNÉES) -> str:
        """
        Renvoie un csv contenant tous les chemins de la table.
        """
        res = ""
        nb = 0
        for c in Chemin_d.objects.filter(zone=self):
            ligne = "|".join(map(str, (c.ar, c.p_détour, c.étapes_texte, c.interdites_texte, c.utilisateur, c.zone)))
            res += ligne + "\n"
            nb += 1
        nom_fichier = os.path.join(chemin_csv, f"sauv_chemins_{self}")
        with open(nom_fichier, "w", encoding="utf-8") as sortie:
            sortie.write(res)
        LOG(f"Les {nb} chemins de la zone {self} ont été sauvegardés dans {nom_fichier}")
        return res

    
    def charge_csv(self, chemin=DONNÉES):
        """
        Charge le csv contenant les chemins
        """
        nom_fichier = os.path.join(chemin, f"sauv_chemins_{self}")
        with open(nom_fichier, encoding="utf8") as entrée:
            nb = 0
            for ligne in entrée:
                ar, p_détour, étapes_texte, interdites_texte, utilisateur, zone = ligne.strip().split("|")
                ch = Chemin_d(
                    ar= ar=="True",
                    p_détour=float(p_détour),
                    étapes_texte=étapes_texte,
                    interdites_texte=interdites_texte,
                    utilisateur=utilisateur,
                    zone=Zone.objects.get(nom=zone)
                )
                if not ch.déjà_présent()[0]:
                    ch.save()
                nb += 1
            LOG(f"{nb} chemins ont été chargés")

    
    def entraîne(self):
        """
        Lance l’entraînement sur tous les chemins de la zone.
        """

        raise NotImplementedError()
        TODO


class Ville_Zone(models.Model):
    """
    Table d’association
    """
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["zone", "ville"], name="Pas de relation en double.")
        ]



class Chemin_d(models.Model):
    """
    Attributs:
        - ar (bool)
        - p_détour (float) proportion détour
        - étapes_texte (str)
        - interdites (str)
        - utilisateur (str)
        - date (DateField) : date de création
        - dernier_p_modif (float) : nb d’arêtes modifiées / distance entre départ et arrivée lors du dernier apprentissage.
        - zone (Zone)
    """
    ar = models.BooleanField(default=False)
    p_détour = models.FloatField()
    étapes_texte = models.TextField()
    interdites_texte = models.TextField(default=None, blank=True, null=True)
    utilisateur = models.CharField(max_length=100, default=None, blank=True, null=True)
    dernier_p_modif = models.FloatField(default=None, blank=True, null=True)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)

    # Les quatre attributs suivant servent uniquement à empêcher les doublons. Mysql n’accepte pas les contraintes Unique sur des champs TextField...
    début = models.CharField(max_length=255)
    fin = models.CharField(max_length=255)
    interdites_début = models.CharField(max_length=255)
    interdites_fin = models.CharField(max_length=255)


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ar", "p_détour", "début", "fin", "interdites_début", "interdites_fin"],
                name="Pas de chemins en double.")
        ]
        ordering = ["-dernier_p_modif", "date"]
    
    def __str__(self):
        return f"Étapes : {self.étapes_texte}\n Interdites : {self.interdites_texte}\n p_détour : {self.p_détour}"

    def déjà_présent(self):
        """
        Renvoie le couple (self est déjà dans la base, la version de la base)
        """
        présents = Chemin_d.objects.filter(
            p_détour=self.p_détour, ar=self.ar, étapes_texte=self.étapes_texte, interdites_texte=self.interdites_texte
        )
        if présents:
            return True, présents.first()
        else:
            return False, None

        
    def save(self):
        """
        Remplit les attributs début, fin, interdites_début et interdites_fin avant de sauvegarder.
        """
        self.début = self.étapes_texte[:min(len(self.étapes_texte), 255)]
        self.interdites_début = self.interdites_texte[:min(len(self.étapes_texte), 255)]
        self.fin = self.étapes_texte[-min(len(self.étapes_texte), 255):]
        self.interdites_fin = self.interdites_texte[-min(len(self.étapes_texte), 255):]
        super().save()

    
    def sauv(self):
        """
        Sauvegarde le chemin si pas déjà présent.
        Si déjà présent, et si un utilisateur est renseigné dans self, met à jour l’utisateur.
        """
        déjà_présent, c_d = self.déjà_présent()
        if déjà_présent and self.utilisateur:
            c_d.utilisateur = self.utilisateur
            c_d.save()
        else:
            self.save()
            
            
    def étapes_c(self) -> list:
        """
        Renvoie la liste des coords des étapes de self.
        """
        return json.loads(self.étapes_texte)

    
    def rues_interdites(self):
        return [r for r in self.interdites_texte.split(";") if len(r) > 0]
    
    # @classmethod
    # def of_ligne_csv(cls, ligne, utilisateur=None):
    #     AR_t, pourcentage_détour_t, étapes_t,rues_interdites_t = ligne.strip().split("|")
    #     p_détour = int(pourcentage_détour_t)/100.
    #     AR = bool(AR_t)
    #     return cls(p_détour=p_détour, ar=AR, étapes_texte=étapes_t, interdites_texte=rues_interdites_t,utilisateur=utilisateur)

    

class Cache_Adresse(models.Model):
    """
    Table d'association ville -> adresse -> chaîne de nœuds
    Note : tout ce qui correspond à des ways dans Nominatim sera enregistré dans la table Rue, via g.nœuds_of_rue.
    Ceci est destiné aux lieux particuliers (bars, bâtiment administratifs, etc. )
    """
    adresse = models.CharField(max_length=200)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE)
    nœuds_à_découper = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["adresse", "ville"], name="Une seule entrée pour chaque (adresse, ville).")
        ]
        
    def __str__(self):
        return f"{self.adresse}, {self.ville}"
    def nœuds(self):
        return découpe_chaîne_de_nœuds(self.nœuds_à_découper)


class CacheNomRue(models.Model):
    """
    Associe à un nom quelconque de rue son nom osm.
    attribut:
      - nom (str) : nom traité par prétraitement_rue
      - nom_osm (str)
      - ville (Ville)
    Une ligne est ajoutée dans cette table lorsqu’une recherche nominatim sur nom a fourni nom_osm.
    """
    nom = models.CharField(max_length=200)
    nom_osm = models.CharField(max_length=200)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["nom", "ville"], name="Une seule entrée pour chaque (nom, ville).")
        ]

    @classmethod
    def ajoute(cls, nom, nom_osm, ville):
        """
        Effet : Crée si pas déjà présent une entrée du cache. Si une entrée est déjà présente pour (nom, z_d), nom_osm est mis à jour.
        Sortie : l’instance créé ou trouvée.
        """
        assert isinstance(nom_osm, str) and isinstance(nom, str)
        essai = cls.objects.filter(nom=nom, ville__nom_complet=ville.nom_complet).first()
        if essai:
            essai.nom = nom_osm
            essai.save()
            return essai
        else:
            res = cls(nom=nom, nom_osm=nom_osm, ville=Ville.objects.get(nom_complet=ville.nom_complet))
            res.save()
            return res



        
##################################################
########## Gestion des lieux ##########
##################################################

"""
Trois modèles : Lieu, TypeLieu et GroupeTypeLieu
"""



class TypeLieu(models.Model):
    
    """
    Enregistre un type de lieu osm.
    catégorie est le nom du tag osm (amenity, shop, tourism...)
    nom_osm est la valeur de ce tag.
    """
    
    catégorie = models.CharField(max_length=200)
    nom_osm = models.CharField(max_length=200)
    nom_français = models.TextField(blank=True, default=None, null=True)

    # Attention à l’ordre ci-dessous : en cas de plusieurs tags, c’est le premier qui sera pris en compte.
    _cat_à_afficher = {"tourism": "(tourisme)", "shop": "(commerce)", "leisure": "(loisirs)", "amenity": "", "railway": "", "public_transport": "(transports en commun)"}
    _types_à_ignorer = {
        "amenity": ("shelter",),
        "public_transport": ("stop_position",),
        "railway": ("rail",)
    }

    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["catégorie", "nom_osm"], name="Une seule entrée pour chaque (catégorie, nom_osm).")
        ]

    def __str__(self):
        """
        Renvoie le nom français suivi de la catégorie si celle-ci est présente dans la variable statique cat_à_afficher
        """
        return f"{self.nom_français} {self._cat_à_afficher.get(self.catégorie, '')}"

    def __hash__(self):
        return self.nom_osm.__hash__()


    def estInutile(self) -> bool:
        """
        Indique si le type figure dans ceux de _types_à_ignorer
        """
        return self.catégorie in self._types_à_ignorer and self.nom_osm in self._types_à_ignorer[self.catégorie]
    
    
    def pour_overpass(self):
        """
        Renvoie la chaîne de caractère [catégorie~nom_osm]
        """
        return f"[{self.catégorie}~{self.nom_osm}]"

    @classmethod
    def of_dico(cls, d: dict, créer_type: bool):
        """
        Entrées:
           d, dico issu d’une recherche overpass
           créer_type : Pour un lieu pas présent dans la base, il sera rajouté si créer_type est vrai, et la fonction renverra None dans le cas contraire.
           json_tout : le json de d. Utilisé uniquement pour traiter le cas des arrêts de bus et autres POI liés aux transports publics.
        Sortie:
           le TypeLieu correspondant à d
        """

        # Recherche d’une éventuelle catégorie connue
        catégorie, nom_osm = "autre", "autre"
        for cat in cls._cat_à_afficher:
            if cat in d:
                nom_osm = d[cat]
                catégorie = cat
                break           # Pour rester sur le premier trouvé.

        # Voyons si déjà présent dans la base
        tls = cls.objects.filter(nom_osm=nom_osm, catégorie=catégorie)
        if tls:
            return tls.first()
        else:
            if créer_type:
                nom_français = input(f"Traduction de {nom_osm} ({catégorie}) ? C’est pour {d['nom']}. Ne rien rentrer pour ignorer ce type de lieux.")
                close_old_connections()
                tl = cls(nom_français=nom_français, nom_osm=nom_osm, catégorie=catégorie)
                tl.save()
                if not nom_français:
                    print(f"J’ignorerai à l’avenir le type {nom_osm}")
                return tl
            else:
                return None

    @classmethod
    def supprimerLesInutiles(cls):
        """
        Supprime toutes les entrées d’un des types de lieu indiqué dans cls._types_à_ignorer
        """
        print("Suppression des types de lieux marqués comme inutiles.")
        for (cat, tls) in cls._types_à_ignorer.items():
            print(cat, tls)
            print(Lieu.objects.filter(type_lieu__nom_osm__in=tls, type_lieu__catégorie=cat).delete())


class GroupeTypeLieu(models.Model):
    """
    Pour enregistrer un rassemblement de types de lieux, pour usage dans un formulaire.
    """
    nom = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True, default=None)
    type_lieu = models.ManyToManyField(TypeLieu)
    féminin = models.BooleanField()

    def __str__(self):
        return self.nom

    def lieux(self, z_d: Zone):
        return Lieu.objects.filter(type_lieu__in=self.type_lieu.all(), ville__in=z_d.villes())

    def déterminant(self):
        if self.féminin:
            return "une"
        else:
            return "un"

    def pour_js(self):
        """
        Sortie : dico sérialisable contenant les données nécessaires à la partie client. À savoir
            - pour construire l’objet ÉtapeLieu dans Django après retour via le formulaire.
        """
        return {
            "type": "gtl",
            "pk": self.pk,
            "nom": self.nom,
        }

    def pour_autocomplète(self):
        return {"nom": self.déterminant() + " " + self.nom,
                "type_étape": "gtl",
                "pk": self.pk,
                }


class Lieu(models.Model):
    """
    Pour enregistrer un lieu public, bar, magasin, etc
    nb : __eq__ consiste à comparer les id_osm. Sachant que l’attribut id_osm a la contrainte « unique ».
    json_tout (str) : contient toutes les données connues du lieu, en json.
    """
    
    nom = models.TextField(blank=True, default=None, null=True)
    autre_nom = models.TextField(blank=True, default=None, null=True)
    nom_norm = models.TextField(blank=True, default=None, null=True)
    type_lieu = models.ForeignKey(TypeLieu, on_delete=models.CASCADE)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE, blank=True, default=None, null=True)
    lon = models.FloatField()
    lat = models.FloatField()
    horaires = models.TextField(blank=True, default=None, null=True)
    tél = models.TextField(blank=True, default=None, null=True)
    id_osm = models.BigIntegerField(unique=True)
    json_tout = models.TextField(blank=True, default=None, null=True)
    arête = models.ForeignKey(Arête, on_delete=models.CASCADE, blank=True, default=None, null=True)  # Arête la plus proche
    num = models.IntegerField(blank=True, default=None, null=True)  # numéro de rue
    

    # Liste des champs à envoyer au constructeur
    _champs = ["nom", "nom_norm", "lon", "lat", "horaires", "tél", "id_osm", "json_tout", "autre_nom"]
    
    
    def __hash__(self):
        return self.id_osm

    def __eq__(self, autre):
        return self.id_osm == autre.id_osm
    
    def coords(self):
        """
        Renvoie le couple (lon, lat)
        """
        return self.lon, self.lat

    def nœuds(self):
        """a
        Renvoie les deux Sommets de l’arête la plus proche.
        """
        return set((self.arête.départ, self.arête.arrivée))

    
    def adresse(self):
        """
        C’est juste le nom associé à l’arête associée à self suivi du nom de la ville actuellement...
        """
        if self.num:
            res = f"{self.num} "
        else:
            res = ""
        return res+", ".join(str(x) for x in (self.arête.nom, self.ville) if x)

        
    def toutes_les_infos(self):
        """
        Renvoie le dico des données présentes sur osm.
        """
        res = json.loads(self.json_tout)
        #res["nom"] = str(self)
        res["adresse"] = self.adresse()
        return res

    def infos(self):
        return json.loads(self.json_autres_données)

        
    def ville_ou_pas(self):
        """
        Renvoie 'nom_de_la_ville' si connue, et '' sinon
        """
        if self.ville:
            return f"{self.ville}"
        else:
            return ""
    
        
    def __str__(self):
        return f"{self.nom} ({self.type_lieu})"

    def str_pour_formulaire(self):
        """
        Renvoie la chaîne  « nom, adresse »
        Pour afficher dans les propositions d’autocomplétion.
        """
        return f"{self.nom}, {self.adresse()}"


    def pour_js(self):
        """
        Sortie : dico sérialisable contenant les données nécessaires pour construire l’objet ÉtapeLieu dans Django après retour via le formulaire.
        En particulier, envoyé pour toutes les propositions d’autocomplétion. -> Doit rester relativement léger.
        """
        lon, lat = self.coords()
        return {
            "type": "lieu",
            "pk": self.pk,
            "lon": lon,
            "lat": lat,
            #"nom": self.nom,
        }
    
    def pour_autocomplète(self):
        """
        Renvoie le dico
        """
        return {
            "type_étape": "lieu",
            "pk": self.pk,
            "géom": [self.coords()],  # géom doit être une liste de coords
            "nom": self.nom,
            "type_lieu": str(self.type_lieu),
            "infos": self.toutes_les_infos(),
        }

    def pour_marqueur(self):
        """
        Renvoie un dico sérialisable contenant les données pour créer un marqueur leaflet.
        Envoyé pour l’affichage du résultat. Contient plus d’infos que pour_js qui est utilisé dans l’autocomplétion.
        """
        res = self.toutes_les_infos()
        lon, lat = self.coords()
        res["coords"] = {"lat": lat, "lng": lon}  # conventions de leaflet
        res["nom"] = str(self)
        res["type"] = "lieu"
        res["pk"] = self.pk
        return res



    def ajoute_arête_la_plus_proche(self, arbre_arêtes: ArbreArête, dmax=30.):
        """
        Entrée :
            arbre_arêtes un Q arbre d’arêtes

        Effet:
            l’arête la plus proche de self est ajoutée dans l’attribut arête.
            Enregistre aussi la ville de l’arête. Dans le cas où l’arête est sur une frontière c’est la ville avec la plus grande population qui est gardée.
            La modif n’est *pas* sauvegardée, pour permettre un bulk_update ultérieur.

        Param :
            dmax, distance max entre coords et l’arête la plus proche pour que l’arête et la ville soient enregistrés. En mètres.
        """
        a, d = arbre_arêtes.étiquette_la_plus_proche(self.coords())  # a est une ArêteSimplifiée
        if d < dmax:
            a_d = Arête.objects.get(pk=a.pk)
            self.arête = a_d
            self.ville = max(self.arête.villes.all())  # La relation d’ordre sur les villes est la population

            
    def rassemble(self, autre):
        """
        Précondition : self et autre ont même arête.
        Effet: autre est supprimé de la base, et ses infos sont fusionnées avec celles de self.
        """
        # TODO
        raise NotImplementedError()

    
    @classmethod
    def of_dico(cls, d: dict, arbre_a: ArbreArête, tous_les_id_osm=None, créer_type=False, force=False):
        """
        Entrée:
            d (str-> T dico), dico contenant les données à utiliser. Au minimum lon et lat. Tous les champs qui ne servent pas à remplir un attribut de l’objet seront jsonisés dans json_autres_données.
            arbre_a, R-arbre d’arêtes dans lequel chercher l’arête la plus proche.

        Sortie (Lieu×bool×bool) :
            (l, créé, utile) : (l’objet, l’objet ne figurait pas dans la base, l’objet figurait mais des modifs ont été détectées.)
            Si utile==True, l’ancien objet a été mis à jour.

        params:
            créer_type : si vrai, l’objet TypeLieu correspond au champ d["type"] est créé s’il n’existait pas.

            tous_les_id_osm : si présent créé sera Faux si l’id_osm du lieu y figure, et utile vrai ssi des différences avec celui de la base sont détectées.
                              Si tous_les_id_osm est None, créé sera vrai.
            force : si Vrai, met à jour le lieu même si aucun changement détecté dans le dico passé en arg par rapport à celui passé la dernière fois.


        La création ou la modif n’est pas sauvegardée pour permettre un bulk_create ou bulk_update ultérieur.
        """

        type_du_lieu = TypeLieu.of_dico(d, créer_type)
        if type_du_lieu.estInutile():
            return None, False, False
        
        nv_json_tout = json.dumps(d)  # le dico d’origine figurera dans l’attribut json_tout
        d_final = {c: d[c] for c in cls._champs if c in d}  # Le dico à envoyer au constructeur
        d_final["nom_norm"] = prétraitement_rue(d["nom"])
        d_final["json_tout"] = nv_json_tout
        if "addr:housenumber" in d_final:
            d_final["num"] = d_final.pop("addr:housenumber")

        # Création ou récup de l’ancien lieu
        if tous_les_id_osm and d["id_osm"] in tous_les_id_osm:
            ancien = Lieu.objects.get(id_osm=d["id_osm"])
            if not force and ancien.json_tout == nv_json_tout:
                # tout est déjà dans la base
                return ancien, False, False
            else:
                # lieu à mettre à jour
                res = ancien
                for attr, val in d_final.items():
                    setattr(res, attr, val)
                créé, utile = False, True
        else:
            # Nouveau lieu
            res = cls(**d_final)
            créé = True
            utile = True

        # texte_tout
        res.json_tout = nv_json_tout
        
        # Type osm du lieu
        res.type_lieu = type_du_lieu
        
        # Adresse
        # Géré via l’arête maintenant... Éventuellement mettre le numéro ?
        # if "addr:street" in d:
        #     res.adresse = d["addr:street"]
        #     if "addr:housenumber" in d:
        #         res.adresse = d["addr:housenumber"] + res.adresse

        
        # Arête et ville
        res.ajoute_arête_la_plus_proche(arbre_a)

        return res, créé, utile

    


class Bug(models.Model):
    """
    Pour enregistrer un rapport de bug.
    """
    titre = models.CharField(max_length=200)
    description = models.TextField()
    message_d_erreur = models.TextField(blank=True, default=None, null=True, verbose_name="(facultatif) Message d’erreur reçu :")
    comment_reproduire = models.TextField(verbose_name="Comment obtenir le comportement non souhaité : ")
    date = models.DateField(auto_now=True)
    importance = models.SmallIntegerField()
    contact = models.TextField(blank=True, default=None, null=True, verbose_name="Contact (facultatif) : pour être tenu au courant du traitement de ceci.")

    class meta:
        ordering = ["importance"]
