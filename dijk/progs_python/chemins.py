# -*- coding:utf-8 -*-

"""
Ce module définit les classes Chemin et Étape.
  - un Chemin représente une recherche utilisateur. Il contient une liste d’étapes.
  - une Étape contient une liste de nœuds. On voudra passer par une arête ou un sommet selon les cas de chaque étape.

rema : Les fonctions de dijkstra.py prennent des Chemins et renvoient des « Itinéraires » (classe définie dans dijkstra.py).

NB: ce sont les chemins qui sont enregistrés dans la base.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, List

import json




from dijk.models import Chemin_d
import dijk.models as mo

from dijk.progs_python.étapes import Étape, ÉtapeEnsLieux, ÉtapeArête
from dijk.progs_python.params import LOG
from dijk.progs_python.apprentissage import lecture_meilleur_chemin  # Uniquement pour la conversion à la nouvelle manière d’enregistrer les chemins.

if TYPE_CHECKING:
    from dijk.progs_python.graphe_par_django import Graphe_django


def sans_guillemets(c):
    if c[0] == '"':
        assert c[-1] == '"', f"Guillemets pas comme prévu, dans la chaîne {c}"
        return c[1:-1]
    else:
        return c






def dico_arête_of_nœuds(g: Graphe_django, nœuds):
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
                    - étapes_sommets (bool) : indique si au moins une étapes est de type « passer par un sommet »

    NB: si p_détour est nul, on supprime des étapes intermédaires.
    """
    def __init__(
            self, z_d: mo.Zone, étapes: List[Étape], p_détour: float, couleur: str, AR: bool, interdites={}, texte_interdites=""
    ):
        assert 0 <= p_détour <= 2, "Y aurait-il confusion entre la proportion et le pourcentage de détour?"
        if p_détour:
            self.étapes = étapes
        else:
            # Pour p_détour==0, on veut le trajet direct, donc on ne prend pas en compte les étapes intermédiaires
            self.étapes = [étapes[0], étapes[-1]]
            
        self.étapes_sommets = any(isinstance(é, ÉtapeEnsLieux) for é in étapes)
        
        self.p_détour = p_détour
        self.couleur = couleur
        self.AR = AR
        self.texte = None
        self.interdites = interdites
        self.noms_rues_interdites = texte_interdites
        self.zone = z_d
    

    @classmethod
    def of_django_vieux(cls, c_d, g, bavard=0):
        """
        Quand les étapes étaient enregistrées par leur adresse.
        """
        return cls.of_données(g, c_d.zone, c_d.ar, c_d.p_détour, c_d.étapes_texte, c_d.interdites_texte, bavard=bavard)

    
    @classmethod
    def convertit_tous_chemins(cls, g):
        """
        Convertit tous les chemins de la base : ce seront les coords des étapes qui seront enregistrées.
        """
        for c_d in Chemin_d.objects.all():
            g.charge_zone(c_d.zone)
            c_d.zone.calculeCyclaMinEtMax()
            if c_d.étapes_texte[:2] != "[[":
                c = cls.of_django_vieux(c_d, g, bavard=1)
                lecture_meilleur_chemin(g, c, bavard=0)  # Pour remplir les coords de départ et arrivée
                c.vers_django()
                c_d.delete()
            
    
    @classmethod
    def of_django(cls, c_d: Chemin_d, g, bavard=0):
        """
        Note : la couleur sera « purple ».
        Pas d’arêtes interdites.
        """
        étapes = [ÉtapeArête.of_coords(coords, g, c_d.zone) for coords in c_d.étapes_c()]
        return cls(c_d.zone, étapes, c_d.p_détour, "purple", c_d.ar)
        
    
    def vers_django(self, utilisateur=None, bavard=0):
        """
        Effet : Sauvegarde le chemin dans la base.
        Sortie : l’instance de Chemin_d créée, ou celle déjà présente le cas échéant.
        """
        assert not self.étapes_sommets, "Les étapes chemins avec étapes_sommets ne sont pas conçus pour être enregistrés."
        #étapes_t = ";".join(é.str_pour_chemin() for é in self.étapes)
        étapes_c = [é.coords for é in self.étapes]
        assert all(c for c in étapes_c)
        étapes_t = json.dumps(étapes_c)
        rues_interdites_t = self.noms_rues_interdites
        début, fin = étapes_t[:255], étapes_t[-255:]
        interdites_début, interdites_fin = rues_interdites_t[:255], rues_interdites_t[-255:]

        test = mo.Chemin_d.objects.filter(
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
        
    
    # @classmethod
    # def of_ligne(cls, ligne, g, tol=.25, bavard=0):
    #     """ Entrée : ligne (str), une ligne du csv de chemins. Format AR|pourcentage_détour|étapes|rues interdites.
    #                  g (Graphe). Utilisé pour déterminer les nœuds associés à chaque étape.
    #     tol indique la proportion tolérée d’étapes qui n’ont pas pu être trouvées.
    #     """

    #     ## Extraction des données
    #     AR_t, pourcentage_détour_t, étapes_t, rues_interdites_t = ligne.strip().split("|")
    #     p_détour = int(pourcentage_détour_t)/100.
    #     AR = bool(AR_t)
    #     return cls.of_données(g, AR, p_détour, étapes_t, rues_interdites_t, bavard=bavard)

        
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
        chemin = cls(z_d, étapes, p_détour, "black", AR, interdites=interdites, texte_interdites=rues_interdites_t)
        chemin.texte = étapes_t
        return chemin


    # def sauv_bdd(self):
    #     """
    #     Enregistre le chemin dans la base.
    #     """
    #     c = Chemin_d(p_détour=self.p_détour,
    #                  étapes=";".join(é.str_pour_chemin() for é in self.étapes),
    #                  ar=self.AR,
    #                  interdites=self.noms_rues_interdites,
    #                  )
    #     c.sauv()


    @classmethod
    def of_étapes(cls, z_d, étapes, pourcentage_détour, AR, g, étapes_interdites=[], bavard=0):
        """
        Entrées : étapes (Étape list).
                  pourcentage_détour (int)
                  AR (bool)
                  g (Graphe)
                  étapes_interdites (Étape list)
        Sortie : instance de Chemin
        """
        noms_rues_interdites = [str(é) for é in étapes_interdites]
        return cls(z_d, étapes, pourcentage_détour/100, "black", AR,
                   interdites=arêtes_interdites(g, z_d, étapes_interdites),
                   texte_interdites=";".join(noms_rues_interdites)
                   )
    
    
    def départ(self):
        return self.étapes[0]
    
    def arrivée(self):
        return self.étapes[-1]

    def renversé(self):
        assert self.AR, "chemin pas réversible (AR est faux)"
        return Chemin(self.zone, list(reversed(self.étapes)), self.p_détour, self.couleur, self.AR, interdites=self.interdites)

    # def chemin_direct_sans_cycla(self, g):
    #     """ Renvoie le plus court chemin du départ à l’arrivée."""
    #     return dijkstra.chemin_entre_deux_ensembles(g, self.départ(), self.arrivée(), 0)
    
    # def direct(self):
    #     """ Renvoie le chemin sans ses étapes intermédaires."""
        
    #     return Chemin([self.départ(), self.arrivée()], self.p_détour, True)
    
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
