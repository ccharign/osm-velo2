# -*- coding:utf-8 -*-

"""
Ce module définit les classes Chemin et Étape.
  - un Chemin représente une recherche utilisateur. Il contient une liste d’étapes.
  - une Étape contient une liste de nœuds. On voudra passer par une arête ou un sommet selon les cas de chaque étape.

rema : Les fonctions de dijkstra.py prennent des Chemins et renvoient des « Itinéraires » (classe définie dans dijkstra.py).

NB: ce sont les chemins qui sont enregistrés dans la base.
"""


import re
from pprint import pprint

from dijk.models import Chemin_d, Arête, Lieu, Sommet, GroupeTypeLieu

from dijk.progs_python.petites_fonctions import milieu
from params import LOG

# from lecture_adresse.normalisation0 import découpe_adresse
from lecture_adresse.normalisation import Adresse
from lecture_adresse.recup_noeuds import nœuds_of_étape, un_seul_nœud


def sans_guillemets(c):
    if c[0] == '"':
        assert c[-1] == '"', f"Guillemets pas comme prévu, dans la chaîne {c}"
        return c[1:-1]
    else:
        return c

    
class ÉchecChemin(Exception):
    pass


class Étape():
    """
    Classe mère pour des étapes utilisables dans les variantes de Dijkstra.
    """

    def __init__(self):
        self.nœuds = set()
        self.nom = ""

        
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

        
    def marqueur_leaflet(self, coords):
        """
        Renvoie le code js pour créer un marqueur pour cette étape.
        """
        lon, lat = coords
        res = self.infos()
        res["lon"] = lon
        res["lat"] = lat
        return res

    
    def marqueur_leaflet_of_sommet(self, s: int):
        """
        Renvoie le code js pour créer un marqueur pour cette étape. Marqueur situé sur le sommet s.
        """
        s_d = Sommet.objects.get(id_osm=s)
        return self.marqueur_leaflet(s_d.coords())
    

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
    def of_dico(cls, d, g, z_d, bavard=0):
        """
        Entrée :
           d, dico contenant a priori le résultat d’un get.
           champ, nom du champ dans lequel chercher le texte de l’étape.

        Sortie :
                 - si d["type"]=="lieu", renvoie l’objet ÉtapeLieu correspondant au lieu de pk dans ["pk"]
                 - si d["type"]=="rue", renvoie l’objet ÉtapeAdresse obtenue en utilisant la rue de pk dans ["pk"]
                 - si d["type"]=="gtl", renvoie l’objet ÉtapeEnsLieux obtenue en utilisant la rue de pk dans ["pk"]
                 - si d["arête"]=="arête", renvoie l’objet ÉtapeArête obtenu en utilisant les coords (lon, lat) trouvées dans d["coords"].

            - S’il existe un champ nommé 'coords_'+champ et qu’il est rempli, sera utilisé pour obtenir directement les sommets via arête_la_plus_proche. L’objet renvoyé sera alors une ÉtapeArête

            - sinon, renvoie une ÉtapeAdresse en lisant d[champ]

        Effet:
            dans le cas d["données_cachées_"+champ]["type"] == rue, et num présent, on complète d avec les coords de l’adresse.
        """
        
        # LOG(f"of_dico lancé. d: {d},\n champ:{champ}", bavard=1)
        # ch_coords = "coords_" + champ

        # if d["données_cachées_"+champ]:
        #     données_supp = json.loads(d["données_cachées_"+champ])
        # else:
        #     données_supp = {}


        if "type" in d:
            if d["type"] == "lieu":
                # ÉtapeLieu
                return ÉtapeLieu(Lieu.objects.get(pk=int(d["pk"])))

            elif d["type"] == "rue":
                # Adresse venant d’une autocomplétion
                ad = Adresse.of_pk_rue(d)

                res = ÉtapeAdresse.of_adresse(g, ad, bavard=bavard)
                # ad.coords a pu être rempli par la ligne ci-dessus
                if ad.coords and not d["coords"]:
                    print("Coordonnées trouvées dans ad. Je les enregistre dans d")
                    d["coords"] = ad.coords
                    # d["données_cachées_"+champ] = json.dumps(données_supp)
                return res

            elif d["type"] == "gtl":
                return ÉtapeEnsLieux.of_gtl_pk(d["pk"], z_d)
            
            
            elif d["type"] == "arête":
                # ÉtapeArête
                coords = d["coords"]
                LOG(f"Coords trouvées dans le dico : {coords}, je vais renvoyer un ÉtapeArête", bavard=bavard)
                # nom, bis_ter, nom, ville = découpe_adresse(d[champ])
                # ad = Adresse()
                # ad.rue_initiale = nom
                # ad.ville = ville
                return ÉtapeArête.of_coords(coords, g, z_d)

            else:
                # ÉtapeAdresse
                LOG("Ni lieu ni arête détecté : je renvoie une ÉtapeAdresse")
                return ÉtapeAdresse.of_texte(d["adresse"], g, z_d)

    
    
class ÉtapeAdresse(Étape):
    """
    Étape venant d’une adresse postale.
    Attributs :
        adresse (instance de Adresse)
    """
    
    def __init__(self):
        self.adresse = None
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
    def of_texte(cls, texte, g, z_d, bavard=0):
        """
        texte est une adresse postale, de la forme « [num] [bis|ter] rue, ville [, pays]
        """
        res = cls()
        n, res.adresse = nœuds_of_étape(texte, g, z_d, bavard=bavard)
        res.nœuds = set(n)
        res.nom = texte
        return res

        
    def infos(self):
        return {"adresse": str(self.adresse)}

    def pour_js(self):
        return self.adresse.pour_js()



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
        res.coords_ini = coords
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
        a = Arête.objects.get(pk=pk)
        premier_segment = a.géométrie()[:2]
        coords = milieu(*premier_segment)
        return cls.of_arête(a, coords)
        
    
    @classmethod
    def of_coords(cls, coords, g, z_d, d_max=50, ad=None):
        # longitude = méridiens, latitude = parallèles
        assert coords[0] < coords[1], f"J’ai reçu lon,lat={coords}. Êtes-vous sûr de ne pas avoir échangé lon et lat ?"
        a, d = g.arête_la_plus_proche(coords, z_d)
        if d > d_max:
            raise RuntimeError(f"Les coords {coords} sont trop loin de la zone {z_d} : {d}m.")
        return cls.of_arête(a, coords, ad=ad)
    
    
    def str_pour_chemin(self):
        """
        Sera utilisé pour enregistrement dans la base.
        """
        return f"Arête{self.coords_ini[0]},{self.coords_ini[1]}"
    
        
    def __str__(self):
        """
        Pour affichage utilisateur.
        """
        return f"{self.nom}"


    def pour_js(self):
        """
        NB: pas de méthode pour_js dans la class Arête, car je veux disposer de coords_ini. Ce dernier a été créé par js lors d’u clic sur la carte.
        """
        return {
            "type": "arête",
            "pk": self.pk,
            "nom": self.nom,
            "coords": self.coords_ini
        }


class ÉtapeLieu(Étape):
    """
    Étape venant d’un Lieu de la base.
    """

    def __init__(self, l: Lieu):
        self.lieu = l
        self.nom = l.nom
        self.nœuds = set((l.arête.départ.id_osm, l.arête.arrivée.id_osm))
        self.adresse = l.adresse

    def str_pour_chemin(self):
        """
        Sera utilisé pour enregistrement dans la base.
        NB : au chargement du chemin, deviendra une ÉtapeArête.
        """
        return f"Arête{self.lieu.lon},{self.lieu.lat}"

    def __str__(self):
        return str(self.lieu)

    def marqueur_leaflet_of_sommet(self, s):
        """
        Rema : comme ce type d’étape n’a qu’un seul lieu, le paramètre s est  ici inutile.
        Il est là pour compatibilité avec la méthode éponyme des autres sous-classes d’Étape.
        """
        return self.lieu.pour_marqueur_leaflet()

    

class ÉtapeEnsLieux(Étape):
    """
    Pour enregistrer un ensemble de lieux.

    Attributs particuliers:
        nœuds est dans cette sous-classe un dico id_osm d’un sommet -> Lieu correspondant

    Méthode particulière :
        marqueur_leaflet_of_sommet qui place le marqueur sur le lieu correspondant au sommet indiqué.
    """

    def __init__(self, gtl, z_d):
        super().__init__()
        self.dico_lieux = {l.arête.départ.id_osm: l for l in gtl.lieux(z_d)}
        self.nœuds = self.dico_lieux  # Pas un set, mais l’appartenance et l’itération fonctionneront pareil...
        self.nom = str(gtl)
        self.gtl = gtl
        assert self.nœuds, f"Aucun lieu trouvé pour {gtl}!"
    
 
    def marqueur_leaflet_of_sommet(self, s):
        return self.nœuds[s].pour_marqueur_leaflet()


    @classmethod
    def of_gtl_pk(cls, pk, z_d):
        """
        Renvoie l’objet ÉtapeEnsLieux correspondant aux lieux d’un type dans le gtl de pk pk et dans la zone z_d.
        """
        return cls(GroupeTypeLieu.objects.get(pk=pk), z_d)

    
    def pour_js(self):
        assert False, "Pas supposé être utilisé actuellement"
        return self.gtl.pour_js()
    





def dico_arête_of_nœuds(g, nœuds):
    """
    Entrée : nœuds (Sommet iterable), un ensemble de sommets
    Sortie : dictionnaire (s -> voisins de s qui sont dans nœuds)
    """
    return {
        s: set((t for t in g.voisins_nus(s) if t in nœuds))
        for s in nœuds
    }


def arêtes_interdites(g, z_d, étapes_interdites, bavard=0):
    """
    Entrée : g (graphe)
             z_d (Zone)
             étapes_interdites (Étapes iterable), liste de noms de rues à éviter
    Sortie : dico des arêtes correspondant (s->voisins de s interdits)
    """
    interdites = {}
    for é in étapes_interdites:
        interdites.update(
            dico_arête_of_nœuds(g,
                                é.nœuds
                                )
        )
    return interdites



class Chemin():
    """ Attributs : - p_détour (float)
                    - couleur (str), couleur à utiliser pour le tracer sur la carte
                    - étapes (Étape list), liste de nœuds
                    - interdites : arêtesi interdites. dico s->sommets interdits depuis s
                    - noms_rues_interdites : str, noms des rues interdites séparées par ; (pour l’enregistrement en csv)
                    - AR (bool), indique si le retour est valable aussi.
                    - texte (None ou str), texte d'où vient le chemin (pour déboguage)
                    - zone (models.Zone)
    """
    def __init__(self, z_d, étapes, étapes_sommets, p_détour, couleur: str, AR, interdites={}, texte_interdites=""):
        assert isinstance(étapes_sommets, list)
        assert p_détour >= 0 and p_détour <= 2, "Y aurait-il confusion entre la proportion et le pourcentage de détour?"
        self.étapes = étapes
        self.étapes_sommets = étapes_sommets
        self.p_détour = p_détour
        self.couleur = couleur
        self.AR = AR
        self.texte = None
        self.interdites = interdites
        self.noms_rues_interdites = texte_interdites
        self.zone = z_d
    

    @classmethod
    def of_django(cls, c_d, g, bavard=0):
        return cls.of_données(g, c_d.zone, c_d.ar, c_d.p_détour, c_d.étapes_texte, c_d.interdites_texte, bavard=bavard)

    
    def vers_django(self, utilisateur=None, bavard=0):
        """
        Transfert le chemin dans la base.
        Sortie : l’instance de Chemin_d créée, ou celle déjà présente le cas échéant.
        """
        assert not self.étapes_sommets, "Les étapes chemins avec étapes_sommets ne sont pas conçus pour être enregistrés."
        étapes_t = ";".join(é.str_pour_chemin() for é in self.étapes)
        rues_interdites_t = self.noms_rues_interdites
        début, fin = étapes_t[:255], étapes_t[-255:]
        interdites_début, interdites_fin = rues_interdites_t[:255], rues_interdites_t[-255:]

        test = Chemin_d.objects.filter(
            p_détour=self.p_détour,
            ar=self.AR,
            début=début,
            fin=fin,
            interdites_début=interdites_début,
            interdites_fin=interdites_fin
        )
        if test.exists():
            LOG(f"Chemin déjà dans la base : {self}")
            return test.first()
        else:
            c_d = Chemin_d(
                p_détour=self.p_détour,
                ar=self.AR, étapes_texte=étapes_t,
                interdites_texte=rues_interdites_t,
                utilisateur=utilisateur,
                début=début,
                fin=fin,
                interdites_début=interdites_début,
                interdites_fin=interdites_fin,
                zone=self.zone
            )
            c_d.save()
            return c_d

    
    @classmethod
    def of_ligne(cls, ligne, g, tol=.25, bavard=0):
        """ Entrée : ligne (str), une ligne du csv de chemins. Format AR|pourcentage_détour|étapes|rues interdites.
                     g (Graphe). Utilisé pour déterminer les nœuds associés à chaque étape.
        tol indique la proportion tolérée d’étapes qui n’ont pas pu être trouvées.
        """

        ## Extraction des données
        AR_t, pourcentage_détour_t, étapes_t, rues_interdites_t = ligne.strip().split("|")
        p_détour = int(pourcentage_détour_t)/100.
        AR = bool(AR_t)
        return cls.of_données(g, AR, p_détour, étapes_t, rues_interdites_t, bavard=bavard)

        
    @classmethod
    def of_données(cls, g, z_d, AR, p_détour, étapes_t, rues_interdites_t, bavard=0):
        """
        Entrée :
            - AR (bool)
            - p_détour (float)
            - étapes_t (str) : étapes séparées par ;
            - rues_interdites_t (str) : rues interdites, séparées par ;
        """
        
        # rues interdites
        if len(rues_interdites_t) > 0:
            noms_rues = rues_interdites_t.split(";")
            étapes_interdites = (Étape.of_texte(n, g, z_d, nv_cache=2) for n in noms_rues)
            interdites = arêtes_interdites(g, z_d, étapes_interdites, bavard=bavard)
        else:
            interdites = {}
        
        # étapes
        noms_étapes = étapes_t.split(";")
        étapes = []
        for c in noms_étapes:
            étapes.append(Étape.of_texte(c.strip(), g, z_d, nv_cache=2, bavard=bavard-1))

        
        ## Création de l’objet Chemin
        chemin = cls(z_d, étapes, [], p_détour, "black", AR, interdites=interdites, texte_interdites=rues_interdites_t)
        chemin.texte = étapes_t
        return chemin


    def sauv_bdd(self):
        """
        Enregistre le chemin dans la base.
        """
        c = Chemin_d(p_détour=self.p_détour,
                     étapes=";".join(é.str_pour_chemin() for é in self.étapes),
                     ar=self.AR,
                     interdites=self.noms_rues_interdites,
                     )
        c.sauv()


    @classmethod
    def of_étapes(cls, z_d, étapes, pourcentage_détour, AR, g, étapes_interdites=[], nv_cache=1, bavard=0):
        """
        Entrées : étapes (Étape list).
                  pourcentage_détour (int)
                  AR (bool)
                  g (Graphe)
                  étapes_interdites (Étape list)
        Sortie : instance de Chemin
        """
        noms_rues_interdites = [str(é) for é in étapes_interdites]
        return cls(z_d, étapes, [], pourcentage_détour/100, "black", AR,
                   interdites=arêtes_interdites(g, z_d, étapes_interdites),
                   texte_interdites=";".join(noms_rues_interdites)
                   )
    
    
    def départ(self):
        return self.étapes[0]
    
    def arrivée(self):
        return self.étapes[-1]

    def renversé(self):
        assert self.AR, "chemin pas réversible (AR est faux)"
        return Chemin(self.zone, list(reversed(self.étapes)), self.étapes_sommets, self.p_détour, self.couleur, self.AR, interdites=self.interdites)

    # def chemin_direct_sans_cycla(self, g):
    #     """ Renvoie le plus court chemin du départ à l’arrivée."""
    #     return dijkstra.chemin_entre_deux_ensembles(g, self.départ(), self.arrivée(), 0)
    
    def direct(self):
        """ Renvoie le chemin sans ses étapes intermédaires."""
        
        return Chemin([self.départ(), self.arrivée()], self.p_détour, True)
    
    def __str__(self):
        res = f"AR : {self.AR}\np_détour : {self.p_détour}\nÉtapes : " + ";".join(map(str, self.étapes))
        if self.noms_rues_interdites:
            res += f"\n Rues interdites : {self.noms_rues_interdites}"
        return res

    def __hash__(self):
        return hash(str(self))

    def str_sans_retour_charriot(self):
        return str(self).replace("\n", "")
    
    def str_joli(self):
        res = f"Itinéraire de {self.départ()} à {self.arrivée()}"
        milieu = self.étapes[1:-1]
        if milieu:
            res += f" en passant par {','.join(map(str,milieu))}"
        if self.noms_rues_interdites:
            res += f" et en évitant {','.join(self.noms_rues_interdites)}"
        return res+"."
        

    def texte_court(self, n_étapes=4):
        if len(self.étapes) <= n_étapes:
            return str(self)
        else:
            à_garder = self.étapes[0:-1:len(self.étapes)//n_étapes] + [self.étapes[-1]]
            return ";".join(map(str, à_garder))



# def lecture_étape(c):
#     """ Entrée : chaîne de caractère représentant une étape.
#         Sortie : nom de rue, ville, pays
#     """
#     e = re.compile("([^()]*)(\(.*\))")  # Un texte puis un texte entre parenthèses
#     essai1 = re.findall(e, c)
#     if len(essai1) > 0:
#         rue, ville = essai1[0]
#         return rue.strip(), ville[1:-1].strip()  # retirer les parenthèses
#     else:
#         f = re.compile("^[^()]*$")  # Pas de parenthèse du tout
#         if re.findall(f, c):
#             return c.strip(), VILLE_DÉFAUT
#         else:
#             raise ValueError(f"chaîne pas correcte : {c}")



