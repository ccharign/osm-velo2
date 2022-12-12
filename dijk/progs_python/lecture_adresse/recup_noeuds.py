# -*- coding:utf-8 -*-

from lecture_adresse.normalisation import Adresse
from recup_donnees import cherche_adresse_complète, rue_of_coords, cherche_lieu
from petites_fonctions import distance_euc
from params import LOG_PB, LOG


### Module pour associer une liste de nœuds à une adresse. ###


class PasTrouvé(Exception):
    pass



def nœuds_of_étape(c: str, g, z_d, nv_cache=1, bavard=0):
    """ c : chaîne de caractères décrivant une étape. Optionnellement un numéro devant le nom de la rue, ou une ville entre parenthèses.
        g : graphe.
        z_d (Zone) : pour la ville par défaut
        nv_cache (int), niveau de mise en cache
        Sortie : (liste de nœuds (id osm) de g associé à cette adresse, l’adresse de type Adresse)
           Si un numéro est indiqué, la liste de nœuds est le singleton du nœud de la rue le plus proche.
           Sinon c’est la liste de tous les nœuds connus de la rue.
    """

    # Recherche dans le cache
    essai = g.dans_le_cache(c)
    if essai:
        LOG(f"(nœuds_of_étape) Adresse dans le cache : {c}", bavard=bavard-1)
        return essai, c
    else:
        LOG(f"(nœuds_of_étape) Pas dans le cache : {c}", bavard=1)

        
    # Lecture de l’adresse
    assert c != ""
    ad = Adresse.of_texte(g, z_d, c, nv_cache=nv_cache, bavard=bavard-1)  # Actuellement, ceci lance déjà un nominatim si la rue n’est pas dans la base.

    # Si c était dans la table des amenities :
    if ad.amen:
        a, _ = g.arête_la_plus_proche(ad.coords, z_d)
        return [a.départ.id_osm, a.arrivée.id_osm], ad
    

    
    def renvoie(res, mettre_en_cache=False):
        """
        Entrée : res (int list)
        Sortie : res, adresse
        Effet : si mettre_en_cache, rajoute res dans le cache.
        """
        assert len(res) > 0
        if mettre_en_cache:
            g.met_en_cache(ad, res)
            print(f"(nœuds_of_étape) Mis en cache : {res} pour {ad}")
        return res, ad

    
    if ad.num is None:
        ## Pas de numéro de rue -> soit c’est une rue entière, soit c’est un batiment spécial
        ## -> liste de tous les nœuds de la rue
        LOG("(nœuds_of_étape) Pas de numéro de rue, je vais renvoyer une liste de nœuds", bavard=bavard)
        if ad.rue == "":
            raise SyntaxError(f"adresse mal formée : {c}")
        else:
            res = tous_les_nœuds(g, z_d, ad, bavard=bavard-1)
            return renvoie(res)

    else:
        ## Numéro de rue -> renvoyer un singleton
        LOG("(nœuds_of_étape) Numéro de rue présent : je vais renvoyer un seul nœud", bavard=bavard)
        return renvoie(un_seul_nœud(g, z_d, ad, bavard=bavard-1))




def tous_les_nœuds(g, z_d, adresse, nv_cache=1, bavard=0):
    """ Entrée : g (graphe)
                 adresse : instance de Adresse sans numéro de rue.
        Paramètres :
            nv_cache (int) : 1 -> cache après overpass
                             2 -> cache après Nominatim # À FAIRE
        Sortie : liste des nœuds de cette adresse, dans l’ordre topologique si possible.


    Méthode actuelle :
       - essai 1 :  via la méthode g.nœuds_of_rue (en local)
       - essai 3 : récupérer les nodes de la recherche Nominatim, et garder ceux qui sont dans g
       - essai 4 : coordonnés du premier objet renvoyé par la recherche, et nœud de g le plus proche d’icelui.
    """
    LOG(f"\n\n(tous_les_nœuds) Lancement de tous_les_nœuds(g, {adresse})", bavard=bavard)


    
    ## Essai 1 : dans la table des rues de la base.
    essai1 = g.nœuds_of_rue(adresse, persévérant=False, bavard=bavard-1)  # Ne pas se lancer dans la bb enveloppante à ce stade.
    if essai1:
        return essai1
    else:
        ## dans le cache ?
        essai = g.dans_le_cache(str(adresse))
        if essai:
            LOG(f"Trouvé dans le cache : {adresse}", bavard=bavard)
            return essai
        
        LOG(f"(recup_nœuds.tous_les_nœuds) adresse pas en mémoire : {adresse}.", bavard=bavard)

        lieu = adresse.rés_nominatim
        if not lieu:
            lieu = cherche_lieu(adresse, bavard=bavard-1)
        if lieu:

        #     nouveau_nom = normalise_rue(g, z_d, truc["display_name"].split(",")[0], adresse.ville, bavard=bavard-1)
        #     adresse.rue_osm = nouveau_nom # Modif de l’adresse
        #     LOG(f"(recup_nœuds.tous_les_nœuds) Nouveau nom trouvé sur Nominatim : {adresse.rue_osm}", bavard=bavard)
            
        #     # essai 2 : avec ce nouveau nom
        #     essai = g.nœuds_of_rue(adresse, persévérant=False, bavard=bavard-1) # toujours pas en mode persévérant
        #     if essai :
        #         return essai
            
            ## Essai 3, avec les nodes trouvés
            nœuds_osm = [t.raw for t in lieu if t.raw["osm_type"]=="node"]
            if nœuds_osm:
                LOG(f"(recup_nœuds.tous_les_nœuds) La recherche Nominatim a donné les nœuds {nœuds_osm}", bavard=bavard+1)
                nœuds_de_g = [ n["osm_id"] for n in nœuds_osm if n["osm_id"] in g ]
                if len(nœuds_de_g) > 0:
                    LOG("J’ai trouvé des nœuds de g dans le résultat de Nominatim", bavard=bavard+1)
                    g.met_en_cache(adresse, nœuds_de_g)
                    return nœuds_de_g
            
            
            ## Essai 4 : en se basant sur les coords enregistrées dans osm pour le premier élément renvoyé par Nominatim
            ## Ce devrait être la situation notamment pour toutes les recherches qui ne sont pas un nom de rue (bâtiment public, bar, commerce...)
            truc = lieu[0].raw
            LOG(f"Essai 4 : Je vais chercher le nœud de g le plus proche de {truc}.", bavard=bavard)
            coords = (float(truc["lon"]), float(truc["lat"]))
            rue, ville, code = rue_of_coords(coords, bavard=bavard)
            ad = Adresse.of_texte(g, z_d, f"{rue}, {ville}")
            ad.coords = coords
            res = nœud_sur_rue_le_plus_proche(g, ad, bavard=bavard)
            if res:
                g.met_en_cache(adresse, [res])
                return [res]
            #return [g.nœud_le_plus_proche( coords, recherche=f"Depuis tous_les_nœuds pour {adresse}." )]
        
        
        raise PasTrouvé(f"Pas réussi à trouver de nœud pour {adresse}.")


    
# def filtre_nœuds(nœuds, g):
#     """ 
#     Entrées : liste de nœuds récupérés par cherche_lieu. Chacun doit être un dictionnaire avec pour clefs au moins "osm_id", "lon", "lat".
#     Renvoie les éléments de nœuds qui sont dans g ; si aucun renvoie le nœud de g le plus proche de nœuds[0].
#     """
#     nœuds_de_g = [ n["osm_id"] for n in nœuds if n["osm_id"] in g]
#     if nœuds_de_g != []:
#         return nœuds_de_g
#     else:
#         n = nœuds[0]
#         return [g.nœud_le_plus_proche( (float(n["lon"]), float(n["lat"])), recherche=f"Depuis tous_les_nœuds pour {nom_rue} ({ville})" )]

    

def un_seul_nœud(g, z_d, adresse, nœuds_de_la_rue=None, bavard=0):
    """ Renvoie un singleton si on dispose d’assez de données pour localiser le numéro. Sinon renvoie tous les nœuds de la rue."""
    try:
        #if bavard > 0: print(f"Je lance coords_of_adresse pour {adresse}.")
        #coords = coords_of_adresse(adresse)
        #return [nœud_sur_rue_le_plus_proche(g, coords, adresse)]
        if bavard>0:print(f"Récupération des coordonnées de {adresse} via adresse.data.gouv.fr")
        coords = cherche_adresse_complète(adresse, bavard=bavard)
        adresse.coords = coords
        return [nœud_sur_rue_le_plus_proche(g, adresse, nœuds=nœuds_de_la_rue, bavard=bavard-1)]
    except Exception as e:
        LOG_PB(f"Échec dans cherche_adresse_complète : {e}. Je vais renvoyer tous les nœuds pour {adresse}). J’efface le numéro de l’adresse.")
        adresse.num=None
        if nœuds_de_la_rue:
            return nœuds_de_la_rue
        else:
            return tous_les_nœuds(g, z_d, adresse, bavard=bavard)
        

    







def nœuds_rue_of_arête(g, s, t):
    """Entrée : g (digraph)
                s, t : deux sommets adjacents
       Sortie : liste des nœuds de la rue contenant l’arête (s, t). La rue est identifiée par le paramètre "name" dans le graphe."""

    déjàVu = {}  # En cas d’une rue qui boucle.
    nom = g[s][t]["name"]
    
    def nœud_dans_direction(g, s, t, res):
        """ Mêmes entrées, ainsi que res, tableau où mettre le résultat.
        t sera mis dans res et noté déjÀVu, mais pas s.

        Renvoie les nœuds uniquement dans la direction (s,t), càd ceux auxquels on accède via t et non via s."""

        res.append(t)
        déjàVu[t] = True
        voisins = [v for v in g[t] if v not in déjàVu and v!=s and g[t][v].get("name", "") == nom]
        if len(voisins) == 0:
            return res
        elif len(voisins) == 1:
            return nœud_dans_direction(g, t, voisins[0], res)
        else:
            print(f"Trop de voisins pour le nœud {t} dans la rue {nom}.")
            return nœud_dans_direction(g, t, voisins[0], res)
       
    return list(reversed(nœud_dans_direction(g, s, t, []))) + nœud_dans_direction(g, t, s, [])


def nœuds_rue_of_nom_et_nœud(g, n, nom):
    """ Entrée : n (int) un nœud de la rue
                 nom (str) le nom de la rue. Doit être le nom exact utilisé par osm et reporté dans le graphe.
        Sortie : liste des nœuds de la rue, dans l’ordre topologique."""

    for v in g[n]:
        if g[n][v].get("name", "") == nom:
            return nœuds_rue_of_arête(g, n, v)
    raise PasTrouvé(f"Pas trouvé de voisin pour le nœud {n} dans la rue {nom}")




def nœud_sur_rue_le_plus_proche(g, adresse, nœuds=None, bavard=0):
    """ 
    Entrée : g (graphe)
             adresse (instance de Adresse)
             nœuds, nœuds de la rue.
    Renvoie le nœud sur la rue nom_rue le plus proche de coords.
    Les nœuds de la rue seront récupérée via g.nœuds_of_rue.
    """
    coords = adresse.coords
    if nœuds is None:
        nœuds = g.nœuds_of_rue(adresse, bavard=bavard)
    #nœuds = tous_les_nœuds(g, adresse, bavard=bavard-1) ## Ceci peut planter si la rue n'est pas en mémoire...
    
    if nœuds is not None:
        LOG(f"Nœuds récupérés pour la rue de {adresse} : {nœuds}", bavard=bavard)
        tab = [ (distance_euc(g.coords_of_id_osm(n), coords), n) for n in nœuds ]
        LOG(f"distances aux nœuds de la rue : {tab}", bavard=bavard)
        _, res = min(tab)
        return res
