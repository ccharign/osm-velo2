from __future__ import annotations
import abc
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dijk.progs_python.graphe_par_django import Graphe_django

import dijk.models as mo
from dijk.progs_python.petites_fonctions import milieu

# from lecture_adresse.normalisation0 import découpe_adresse
from dijk.progs_python.lecture_adresse.normalisation import Adresse
from dijk.progs_python.lecture_adresse.recup_noeuds import nœuds_of_étape, un_seul_nœud


class Étape(abc.ABC):
    """
    Classe mère pour des étapes utilisables dans les variantes de Dijkstra.
    """

    def __init__(self):
        self.nœuds = set()
        self.nom = ""
        self.coords = None

        
    def __str__(self):
        return self.nom

    def __contains__(self, nœud):
        return nœud in self.nœuds

    def __len__(self):
        return len(self.nœuds)
    

    def infos(self):
        """
        Renvoie un dico avec les infos connues. Sera utilisé notamment pour les marqueurs leaflet.
        A pour vocation à être écrasée dans les sous-classes.
        """
        res = {"nom": str(self)}
        return res

    
    @abc.abstractmethod
    def pour_marqueur(self):
        """
        Renvoie le dico sérialisable pour envoyer à js.
        """
        raise RuntimeError(f"Étape.marqueur_leaflet est une méthode abstraite. Le type de self est {type(self)}")

        
    def pour_marqueur_of_sommet_osm(self, s: int):
        """
        Renvoie le dico pour marqueur, avec en plus les coords fixées à celles du sommet dont l’id osm est passé en arg.
        Sera écrasé dans les sous-classes.
        """
        # lon, lat = Sommet.objects.get(id_osm=s).coords()
        # rés = self.pour_marqueur()
        # rés["coords"] = {"lat": lat, "lng": lon}
        # return rés
        return None


    @classmethod
    def of_texte(cls, texte, g, z_d, nv_cache=1, bavard=0):
        """
        Si de la forme 'Arêtelon;lat', renvoie l’objet de type ÉtapeArête correspondant à ces coords.
        Sinon lit l’adresse et renvoie l’objet de type Étape classique.
        """

        # 1) Voyons si le texte venait d’un ÉtapeArête.__str__
        essai = re.match("^Arête(.*),(.*)", texte)
        if essai:
            lon, lat = map(float, essai.groups())
            return ÉtapeArête.of_coords((lon, lat), g, z_d)


        # 2) voyons s’il venait d’un ÉtapeArête.joli_texte
        essai2 = re.match("^Arête numéro ([0-9]*).*", texte)
        if essai2:
            pk = map(int, essai.groups())
            return ÉtapeArête.of_pk(pk)

        
        # Cas général : le texte est une adresse.
        return ÉtapeAdresse.of_texte(texte, g, z_d, bavard=bavard)


    @classmethod
    def of_dico(cls, d: dict, g: Graphe_django, z_d: mo.Zone, bavard=0):
        """
        Entrée :
           d, dico contenant a priori les params d’un get.
           champ, nom du champ dans lequel chercher le texte de l’étape.

        Sortie :
                 - si d["type_étape"]=="lieu", renvoie l’objet ÉtapeLieu correspondant au lieu de pk dans ["pk"]
                 - si d["type_étape"]=="rue", renvoie l’objet ÉtapeAdresse obtenue en utilisant la rue de pk dans ["pk"]
                 - si d["type_étape"]=="gtl", renvoie l’objet ÉtapeEnsLieux obtenue en utilisant la rue de pk dans ["pk"]
                 - si d["arête_étape"]=="arête", renvoie l’objet ÉtapeArête obtenu en utilisant les coords trouvées dans d["lon"] et d["lat"].

            - S’il existe un champ nommé 'coords_'+champ et qu’il est rempli, sera utilisé pour obtenir directement les sommets via arête_la_plus_proche. L’objet renvoyé sera alors une ÉtapeArête

            - sinon, renvoie une ÉtapeAdresse en lisant d[champ]

        Effet:
            dans le cas d["type"] == rue, et num présent, on complète d avec les coords de l’adresse.
        """
        assert isinstance(d, dict)
        type_étape = d.get("type_étape")
        
        if type_étape == "lieu":
            # ÉtapeLieu
            return ÉtapeLieu(mo.Lieu.objects.get(pk=int(d["pk"])))

        elif type_étape == "rue":
            # Adresse venant d’une autocomplétion
            # extrait la rue de la pk, le num, bis_ter et coords de d
            if "lon" in d:
                d["coords"] = d["lon"], d["lat"]
            ad = Adresse.of_pk_rue(d)

            res = ÉtapeAdresse.of_adresse(g, ad, bavard=bavard)
            # ad.coords a pu être rempli par la ligne ci-dessus
            if ad.coords and not d["coords"]:
                print("Coordonnées trouvées dans ad. Je les enregistre dans d.")
                d["coords"] = ad.coords
            return res

        elif type_étape == "gtl":
            # Groupe de types de lieux
            return ÉtapeEnsLieux.of_gtl_pk(d["pk"], z_d)

        elif type_étape == "arête":
            # ÉtapeArête
            coords = d["lon"], d["lat"]
            return ÉtapeArête.of_coords(coords, g, z_d)

        elif type_étape == "adresse_texte":
            # ÉtapeAdresse
            return ÉtapeAdresse.of_texte(d["adresse"], g, z_d)

        else:
            raise ValueError(f"Type d’étape non reconnu: {d.get('type')}")
    
    
class ÉtapeAdresse(Étape):
    """
    Étape venant d’une adresse postale.
    Attributs :
        adresse (instance de Adresse)
    """
    
    def __init__(self):
        self.adresse = Adresse()
        self.nœuds = set()
        self.nom = ""

    def str_pour_chemin(self):
        return str(self)

    def __str__(self):
        return str(self.adresse)
        

    @classmethod
    def of_adresse(cls, g, ad, bavard=0):
        """
        Entrée:
             ad (Adresse) dont l’attribut ad.rue_osm est déjà un objet mo.Rue.
        Sortie:
            Objet ÉtapeAdresse avec un seul nœud si num présent, tous les nœuds de la rue sinon.
        """
        res = cls()
        res.adresse = ad
        res.nom = str(ad)
        nœuds_de_la_rue = ad.rue_osm.nœuds()
        assert nœuds_de_la_rue, f"Pas de nœuds récupérées pour {ad}"
        if ad.num:
            res.nœuds = un_seul_nœud(g, None, ad, nœuds_de_la_rue=nœuds_de_la_rue, bavard=bavard)
            # ad.coords a été complété au passage
        else:
            # Pas de num : on prend tous les nœuds de la rue
            res.nœuds = set(nœuds_de_la_rue)
        return res

    
    @classmethod
    def of_texte(cls, texte, g: Graphe_django, z_d, bavard=0):
        """
        texte est une adresse postale, de la forme « [num] [bis|ter] rue, ville [, pays]
        """
        res = cls()
        n, res.adresse = nœuds_of_étape(texte, g, z_d, bavard=bavard)
        res.nœuds = set(n)
        res.nom = texte
        return res

    
    @classmethod
    def of_rue(cls, rue: mo.Rue):
        rés = cls()
        rés.nom = rue.nom_complet
        rés.nœuds = set(rue.nœuds())
        rés.adresse.rue_osm = rue
        return rés

        
    def infos(self):
        return {"adresse": str(self.adresse)}

    def pour_marqueur(self):
        return self.adresse.pour_marqueur()



class ÉtapeArête(Étape):
    """
    Pour représenter une étape qui est une arête. Dispose de l’attribut nœud et de la méthode __str__ afin d’être utilisée dans un chemin comme la classe Étape.

    Attributs:
        nœuds (int set), set d’id_osm de sommets
        coords_ini (float×float), coords du point dont cette arête était la plus proche. Servira de str pour l’enregistrement dans un Chemin_d dans la base.
        pk (int), clef primaire de l’arête dans la table models.Arête.
        nom (str), nom de la rue la contenant
    """
    
    def __init__(self):
        self.nœuds = set()
        self.coords_ini = None
        self.pk = None
        self.adresse = Adresse()
        self.nom = None

        
    @classmethod
    def of_arête(cls, a, coords, ad=None):
        res = cls()
        res.coords = coords
        res.nœuds = set((a.départ.id_osm, a.arrivée.id_osm))
        res.nom = a.nom
        res.pk = a.pk
        if ad:
            res.adresse = ad
        else:
            res.adresse.rue_initiale = a.nom
        res.adresse.coords = coords
        return res

    
    @classmethod
    def of_pk(cls, pk):
        """
        Je prend ici le milieu du premier segment de l’arête pour le champ coords.
        """
        a = mo.Arête.objects.get(pk=pk)
        premier_segment = a.géométrie()[:2]
        coords = milieu(*premier_segment)
        return cls.of_arête(a, coords)
        
    
    @classmethod
    def of_coords(cls, coords: tuple, g, z_d: mo.Zone, d_max=50, ad=None):
        """
        coords au format (lon, lat)
        """
        # longitude = méridiens, latitude = parallèles
        assert coords[0] < coords[1], f"J’ai reçu lon,lat={coords}. Êtes-vous sûr de ne pas avoir échangé lon et lat ?"
        a, d = g.arête_la_plus_proche(coords, z_d)
        if d > d_max:
            raise RuntimeError(f"Les coords {coords} sont trop loin de la zone {z_d} : {int(d)}m.")
        return cls.of_arête(a, coords, ad=ad)
    
    
    # def str_pour_chemin(self):
    #     """
    #     Sera utilisé pour enregistrement dans la base.
    #     """
    #     return f"Arête{self.coords_ini[0]},{self.coords_ini[1]}"
    
        
    def __str__(self):
        """
        Pour affichage utilisateur.
        """
        return f"{self.nom}"


    def pour_marqueur(self):
        """
        NB: pas de méthode pour_marqueur dans la classe Arête, car je veux disposer de coords_ini. Ce dernier a été créé par js lors du clic sur la carte.
        """
        lon, lat = self.coords
        return {
            "type": "arête",
            "pk": self.pk,
            "nom": self.nom,
            "coords": {"lat": lat, "lng": lon}
        }

        
class ÉtapeLieu(Étape):
    """
    Étape venant d’un Lieu de la base.
    """

    def __init__(self, l: mo.Lieu):
        self.lieu = l
        self.nom = l.nom
        self.nœuds = set((l.arête.départ.id_osm, l.arête.arrivée.id_osm))
        self.adresse = l.adresse
        self.coords = l.coords()

    # def str_pour_chemin(self):
    #     """
    #     Sera utilisé pour enregistrement dans la base.
    #     NB : au chargement du chemin, deviendra une ÉtapeArête.
    #     """
    #     return f"Arête{self.lieu.lon},{self.lieu.lat}"

    def __str__(self):
        return str(self.lieu)

    def pour_marqueur(self):
        return self.lieu.pour_marqueur()

    # def pour_marqueur_of_sommet_osm(self, s: int):
    #     """
    #     Rema : comme ce type d’étape n’a qu’un seul lieu, le paramètre s est ici inutile.
    #     Il est là pour compatibilité avec la méthode éponyme des autres sous-classes d’Étape.
    #     Du coup, le marqueur sera placé sur le lieu, et non sur le sommet atteint.
    #     """
    #     return self.lieu.pour_marqueur()



class ÉtapeEnsLieux(Étape):
    """
    Pour enregistrer un ensemble de lieux.

    Attributs particuliers:
        nœuds est dans cette sous-classe un dico id_osm d’un sommet -> Lieu correspondant

    Méthode particulière :
        marqueur_leaflet_of_sommet qui place le marqueur sur le lieu correspondant au sommet indiqué.
    """

    def __init__(self, gtl: mo.GroupeTypeLieu, z_d: mo.Zone):
        super().__init__()
        self.dico_lieux = {l.arête.départ.id_osm: l for l in gtl.lieux(z_d)}
        self.dico_lieux.update({l.arête.arrivée.id_osm: l for l in gtl.lieux(z_d)})
        self.nœuds = self.dico_lieux  # Pas un set, mais l’appartenance et l’itération fonctionneront pareil...
        self.nom = str(gtl)
        self.gtl = gtl
        assert self.nœuds, f"Aucun lieu trouvé pour {gtl}!"
    
 
    def pour_marqueur_of_sommet_osm(self, s: int):
        """
        Renvoie le marqueur du lieu correspondant à s.
        """
        return self.nœuds[s]


    @classmethod
    def of_gtl_pk(cls, pk, z_d):
        """
        Renvoie l’objet ÉtapeEnsLieux correspondant aux lieux d’un type dans le gtl de pk pk et dans la zone z_d.
        """
        return cls(mo.GroupeTypeLieu.objects.get(pk=pk), z_d)

    def pour_marqueur(self):
        raise ValueError("Pas de marqueur possible pour une ÉtapeEnsLieux!")
    
    # def pour_js(self):
    #     assert False, "Pas supposé être utilisé actuellement"
    #     return self.gtl.pour_js()
    

