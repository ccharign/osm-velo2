import json
from pprint import pformat
import os
from itertools import chain

from django.db import models, close_old_connections
from dijk.progs_python.params import LOG, DONNÉES
from dijk.progs_python.lecture_adresse.normalisation0 import partie_commune

from petites_fonctions import distance_euc


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


def découpe_chaîne_de_nœuds(c):
    return tuple(map(int, c.split(",")))


class Ville(models.Model):
    nom_complet = models.CharField(max_length=100)
    nom_norm = models.CharField(max_length=100)
    code = models.IntegerField(null=True)
    code_insee = models.IntegerField(null=True, default=None, blank=True)
    population = models.IntegerField(null=True, default=None, blank=True)
    #densité = models.SmallIntegerField(null=True, default=None, blank=True)
    superficie = models.FloatField(null=True, default=None, blank=True)
    géom_texte = models.TextField(null=True, default=None, blank=True)
    données_présentes = models.BooleanField(default=False)
    #zone = models.ManyToManyField(Zone) # pb car la classe Zone n’est pas encore définie.

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["nom_norm", "code_insee"], name="Le couple (nom_norm, code_insee) doit être unique."),
        ]
    
    def __str__(self):
        return self.nom_complet

    def avec_code(self):
        return f"{self.code} {self.nom_complet}"

    def voisine(self):
        rels = Ville_Ville.objects.filter(ville1=self).select_related("ville2")
        return tuple(r.ville2 for r in rels)

    def zones(self):
        return (rel.zone for rel in Ville_Zone.objects.filter(ville=self).prefetch_related("zone"))

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

        
class Zone(models.Model):
    """
    Une zone délimite une zone dont le graphe sera mis en mémoire au chargement.
    """
    nom = models.CharField(max_length=100, unique=True)
    ville_défaut = models.ForeignKey(Ville, on_delete=models.CASCADE)

    class Meta:
        ordering = ["nom"]
    
    def villes(self):
        return (rel.ville for rel in Ville_Zone.objects.filter(zone=self).prefetch_related("ville"))

    # def arêtes(self):
    #     """
    #     Générateur des arêtes de self.
    #     Beaucoup trop lent !
    #     """
    #     for v in self.villes():
    #         for a in v.arête_set.all():
    #             yield a

    def arêtes(self):
        """
        Sortie (queryset) : les arêtes des villes de la zone
        """
        villes = self.villes()
        return Arête.objects.filter(villes__in=villes).prefetch_related("départ", "arrivée")
        
    def sommets(self):
        """
        Générateur des sommets de self.
        """
        for v in self.villes():
            for s in v.sommet_set.all():
                yield s

    def ajoute_ville(self, ville):
        rel = Ville_Zone(ville=ville, zone=self)
        rel.save()
                
    def __str__(self):
        return self.nom
    
    def __hash__(self):
        return self.pk

    
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
                    ar = ar=="True",
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
    
    def nœuds(self):
        return découpe_chaîne_de_nœuds(self.nœuds_à_découper)



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
    deuc = distance_euc(s_d.coords(), t_d.coords())
    if a["length"] < deuc:
        print(f"Distance euc ({deuc}) > a['length'] ({a['length']}) pour l’arête {a} de {s_d} à {t_d}")
        return deuc
    else:
        return a["length"]


class Arête(models.Model):
    """
    Attributs:
        départ (Sommet)
        arrivée (Sommet)
        longueur (float)
        cycla (float) : cyclabilité calculée par l'IA. None par défaut.
        cycla_défaut (float) : cyclabilité obtenue par les données présentes dans osm. Via la fonction vers_django.cycla_défaut lors du remplissage de la base.
        rue (Rue). Ce champ est-il utile ?
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
        super(Chemin_d, self).save()
                                     
    def sauv(self):
        """
        Sauvegarde le chemin si pas déjà présent.
        Si déjà présent, et si un utilisateur est renseigné dans self, met à jour l’utisateur.
        """
        déjà_présent, c_d = self.déjà_présent
        if déjà_présent and self.utilisateur:
            c_d.utilisateur = self.utilisateur
            c_d.save()
        else:
            self.save()
            
            
    def étapes(self):
        return self.étapes_texte.split(";")

    
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


class TypeLieu(models.Model):
    """
    catégorie est le nom du tag osm (amenity, shop, tourism...)
    nom_osm est la valeur de ce tag.
    """
    catégorie = models.CharField(max_length=200)
    nom_osm = models.CharField(max_length=200)
    nom_français = models.TextField(blank=True, default=None, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["catégorie", "nom_osm"], name="Une seule entrée pour chaque (catégorie, nom_osm).")
        ]

    def __str__(self):
        return f"{self.nom_français} ({self.catégorie})"


    def __hash__(self):
        return self.nom_osm.__hash__()

    def pour_overpass(self):
        """
        Renvoie la chaîne de caractère [catégorie=nom_osm]
        """
        return f"[{self.catégorie}~{self.nom_osm}]"



## Faire des regroupements, comme « logement », « restauration »

class Lieu(models.Model):
    """
    Pour enregistrer un lieu public, bar, magasin, etc
    nb : __eq__ consiste à comparer les id_osm. Sachant que l’attribut id_osm a la contrainte « unique ».
    """
    
    nom = models.TextField(blank=True, default=None, null=True)
    type_lieu = models.ForeignKey(TypeLieu, on_delete=models.CASCADE)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE, blank=True, default=None, null=True)
    #rue = models.ForeignKey(Rue, on_delete=models.CASCADE, blank=True, default=None, null=True)
    adresse = models.TextField(blank=True, default=None, null=True)
    lon = models.FloatField()
    lat = models.FloatField()
    horaires = models.TextField(blank=True, default=None, null=True)
    tél = models.TextField(blank=True, default=None, null=True)
    id_osm = models.BigIntegerField(unique=True)
    json_initial = models.TextField(blank=True, default=None, null=True)
    json_nettoyé = models.TextField(blank=True, default=None, null=True)
    arête = models.ForeignKey(Arête, on_delete=models.CASCADE, blank=True, default=None, null=True)  # Arête la plus proche


    def __hash__(self):
        return self.id_osm

    def __eq__(self, autre):
        return self.id_osm == autre.id_osm
    
    def coords(self):
        return self.lon, self.lat

    def nœuds(self):
        """
        Renvoie les deux Sommets de l’arête la plus proche.
        """
        return set((self.arête.départ, self.arête.arrivée))
        
    
    def toutes_les_infos(self):
        """
        Renvoie le dico des données présentes sur osm.
        """
        return json.loads(self.json_initial)

        
    def ville_ou_pas(self):
        """
        Renvoie ', nom_de_la_ville' si connue, et '' sinon
        """
        if self.ville:
            return f", {self.ville}"
        else:
            return ""
    
        
    def __str__(self):
        return f"{self.nom} ({self.type_lieu}){self.adresse}, {self.ville_ou_pas()}"

    def str_pour_formulaire(self):
        """
        Renvoie la chaîne  « nom, ville »
        """
        return f"{self.nom}, {self.ville}"

    def marqueur_leaflet(self, nomCarte):
        """
        Renvoie le code js pour créer un marqueur leaflet pour ce lieu.
        """
        return f"""marqueur_avec_popup({self.lon}, {self.lat}, {self.json_nettoyé}, {nomCarte});"""


    # def save(self, *args, **kwargs):
    #     """
    #     Avant la sauvegarde normale, complète les champs ville et rue.
    #     """
        
    #     if not self.ville:
    #         self.ajoute_ville_et_rue()
    #     super().save(self, *args, **kwargs)


    def ajoute_arête_la_plus_proche(self, arbre_arêtes):
        """
        Entrée :
            arbre_arêtes un Q arbre d’arêtes
        Effet:
            l’arête la plus proche de self est ajoutée dans l’attribut arête.
            La modif n’est *pas* sauvegardée, pour permettre un bulk_update ultérieur.
        """
        self.arête = arbre_arêtes.arête_la_plus_proche((self.lon, self.lat))[0]


    # def ajoute_ville_et_rue(self, bavard=0):
    #     """
    #     Va chercher ville et rue sur data.gouv grâce aux coords et les ajoute à self.
    #     Les erreurs sont ignorées...
    #     La modif n’est pas sauvegardée pour permettre un bulk_update ultérieur.
    #     """
    #     try:
    #         nom_rue, nom_ville, code_postal = rue_of_coords((self.lon, self.lat))
    #         try:
    #             res1 = Ville.objects.filter(nom_norm=partie_commune(nom_ville))
    #             if res1.count() == 1:
    #                 v_d = res1.first()
    #             elif res1.count() > 1:
    #                 v_d = Ville.objects.get(nom_norm=partie_commune(nom_ville), code=code_postal)
    #             else:
    #                 raise ValueError(f"Pas de ville dans la base pour le nom {nom_ville}, normalisé en {partie_commune(nom_ville)}.")
    #             self.ville = v_d
    #             rue = Rue.objects.get(nom_norm=prétraitement_rue(nom_rue), ville=v_d)
    #             self.rue = rue
            
    #         except Rue.DoesNotExist as e:
    #             LOG(f"Problème lors de la récupération de la rue de {self}.\n Nom de rue obtenu sur data.gouv.fr : {nom_rue}, normalisé en {prétraitement_rue(nom_rue)}\n Erreur : {e}\n", bavard=bavard)
        
    #     except Exception as e:
    #         LOG(f"Problème dans ajoute_ville_et_rue pour {self}\n Erreur : {e}.", bavard=1)

    
    @classmethod
    def of_dico(cls, d, tous_les_id_osm=None, créer_type=False):
        """
        Entrée:
            d (str-> T dico)

        Sortie (Lieu×bool×bool) :
            (l, créé, utile) : (l’objet, l’objet ne figurait pas dans la base, l’objet figurait mais des modifs ont été détectées.)
            Si utile==True, l’ancien objet a été mis à jour.

        params:
            créer_type : si vrai, l’objet TypeLieu correspond au champ d["type"] est créé s’il n’existait pas.

            tous_les_id_osm : si présent créé sera Faux si l’id_osm du lieu y figure, et utile vrai ssi des différences avec celui de la base sont détectées.
                              Si tous_les_id_osm est None, créé sera vrai.


        La création ou la modif n’est pas sauvegardée pour permettre un bulk_create ou bulk_update ultérieur.
        """

        champs_obligatoires = ["type", "catégorie", "lon", "lat", "id_osm"]
        if not all(x in d for x in champs_obligatoires):
            raise RuntimeError("Il manquait des champs pour {d} : {(c for c in champs_obligatoires if c not in d)}")
        
        # Champs « normaux ». Inclus les obligatoires sans opération de traitement à effectuer.
        champs = {"name": "nom", "lon": "lon", "lat": "lat", "opening_hours": "horaires", "phone": "tél", "id_osm": "id_osm"}
        d_nettoyé = {
            cf: d.get(ce, None)
            for ce, cf in champs.items()
        }
        d_nettoyé["id_osm"] = int(d_nettoyé["id_osm"])
        nv_json_nettoyé = json.dumps(d_nettoyé)  # Sert à détecter une modif

        # Création ou récup de l’ancien lieu
        if tous_les_id_osm and d_nettoyé["id_osm"] in tous_les_id_osm:
            ancien = Lieu.objects.get(id_osm=d_nettoyé["id_osm"])
            if not ancien.ville or ancien.json_nettoyé == nv_json_nettoyé:
                # tout est déjà dans la base
                return ancien, False, False
            else:
                # lieu à mettre à jour
                res = ancien
                for attr, value in d_nettoyé.items():
                    setattr(res, attr, value)
                créé, utile = False, True
        else:
            # Nouveau lieu
            res = cls(**d_nettoyé)
            créé = True
            utile = True

        # texte_tout
        res.json_initial = json.dumps(d)
        res.json_nettoyé = nv_json_nettoyé

        # Type osm du lieu
        # À optimiser : passer le type le lieu en arg
        if créer_type:
            tls = TypeLieu.objects.filter(nom_osm=d["type"], catégorie=d["catégorie"])
            if tls:
                tl = tls.first()
            else:
                nom_français = input(f"Traduction de {d['type']} ({d['catégorie']}) ? C’est pour {d['name']}. ")
                close_old_connections()
                tl = TypeLieu(nom_français=nom_français, nom_osm=d["type"], catégorie=d["catégorie"])
                tl.save()
                if not nom_français:
                    print(f"J’ignorerai à l’avenir le type {d['type']}")

        else:
            tl = TypeLieu.objects.get(nom_osm=d["type"], catégorie=d["catégorie"])
        res.type_lieu = tl

        # Adresse
        if "addr:street" in d:
            res.adresse = d["addr:street"]
            if "addr:housenumber" in d:
                res.adresse = d["addr:housenumber"] + res.adresse
        




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
