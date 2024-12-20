# -*- coding:utf-8 -*-

# Ce module regroupe les fonctions de recherche de données géographiques qui utilisent Nominatim, overpass, ou data.gouv.

import time
import requests
import json
import urllib.parse
from pprint import pprint, pformat
import subprocess
from functools import reduce

import geopy
import overpy

from params import LOG_PB
from petites_fonctions import LOG
import dijk.models as mo


geopy.geocoders.options.default_user_agent = "pau à vélo"
localisateur = geopy.geocoders.Nominatim(user_agent="pau à vélo")



    
class LieuPasTrouvé(Exception):
    pass


######################
### Avec data.gouv ###
######################

# https://adresse.data.gouv.fr/api-doc/adresse


def cherche_adresse_complète(adresse, bavard=0):
    """
    Entrée : une adresse avec numéro de rue.
    Sortie : coordonnées (lon, lat) gps de cette adresse obtenue avec api-adresse.data.gouv.fr
    """
    # https://perso.esiee.fr/~courivad/python_bases/15-geo.html
    api_url = "https://api-adresse.data.gouv.fr/search/?q="
    r = requests.get(api_url + urllib.parse.quote(str(adresse)))
    r = r.content.decode('unicode_escape')
    print("\nRequête sur api-adresse.data.gouv")
    return json.loads(r)["features"][0]["geometry"]["coordinates"]



def rue_of_coords(c, bavard=0):
    """
    Entrée : (lon, lat)
    Sortie : (nom, ville, code de postal) de la rue renvoyé par adresse.data.gouv
    """
    lon, lat = c
    api_url = f"https://api-adresse.data.gouv.fr/reverse/?lon={lon}&lat={lat}&type=street"
    try:
        r = requests.get(api_url).content.decode('unicode_escape')
        d = json.loads(r)["features"][0]["properties"]
        res = d["name"], d["city"], int(d["postcode"])
        LOG(f"(rue_of_coords) Pour les coordonnées {c} j'ai obtenu {res}.", bavard=bavard)
        return res
    except Exception as e:
        print(f"Problème dans data.gouv pour les coordonnées {c}.\n Reçu {r}")
        raise e


def adresses_of_liste_lieux(ll, bavard=0, affiche=False):
    """
    Entrée : liste de lieux
    Sortie : liste de dicos obtenus par le reverse de adresse.data.gouv. Contient en particulier les champs result_housenumber, result_name (nom de la rue), result_context (département et région), result_citycode

    https://adresse.data.gouv.fr/api-doc/adresse
    """

    # Création du csv à envoyer au serveur de data.gouv
    csv_entrée = "lon,lat"
    for l in ll:
        csv_entrée += f"\n{l.lon},{l.lat}"  # séparés par des virgules
    LOG(f"csv cré : \n{csv_entrée}", bavard=bavard, affiche=affiche)
    with open("tmp.csv", "w") as tmp:
        tmp.write(csv_entrée)
    # -s dans curl : pas de barre de progression
    réponse = subprocess.check_output(
        ["curl", "-X", "POST", "-F", "data=@tmp.csv", "-s",
         "https://api-adresse.data.gouv.fr/reverse/csv/"],
        text=True
    ).strip().split("\n")
    LOG(f"réponse reçue :\n{pformat(réponse)}", bavard=bavard, affiche=affiche)
    
    if len(ll) != len(réponse)-1:
        if len(réponse) < 10:
            pprint(réponse)
        else:
            pprint(réponse[:5])
            pprint(réponse[-5:])
        raise RuntimeError(f"Pas le bon nombre de résultats : {len(réponse)-1} au lieu de {len(ll)}")
    
    
    champs = réponse[0].strip()[1:].split(",")  # Il y a un caractère \ufeff au début de la première ligne...
    res = []
    for ligne in réponse[1:]:
        res.append({c: v for (c, v) in zip(champs, ligne.strip().split(","))})

    return res



######################
### Avec Nominatim ###
######################


def cherche_lieu(adresse, seulement_structurée=False, seulement_non_structurée=False, bavard=0):
    """
    Entrée : adresse (instance de Adresse)

    Sortie : liste d'objets geopy enregistrées dans osm pour la rue dont le nom est passé en argument. On peut préciser un numéro dans nom_rue.

    Premier essai : recherche structurée avec adresse.nom_rue et adresse.ville.avec_code
    Deuxième essai, seulement si seulement_structurée==False : non structurée avec essai adresse.pour_nominatim().
    """
    nom_rue = adresse.rue()
    ville = adresse.ville
    pays = adresse.pays
    
    if not seulement_non_structurée:
        #  Essai 1 : recherche structurée. Ne marche que si l'objet à chercher est effectivement une rue
        LOG(f'Essai 1: "street":{nom_rue}, "city":{ville.avec_code()}, "country":{pays}', bavard=bavard)
        lieu = localisateur.geocode(
            {"street": nom_rue, "city": ville.avec_code(), "country": pays, "dedup": 0},
            exactly_one=False, limit=None
        )  # Autoriser plusieurs résultats car souvent une rue est découpée en plusieurs tronçons
        if lieu is not None:
            return lieu
        else:
            LOG_PB(f"La recherche structurée a échouée pour {adresse}.")

    if not seulement_structurée:
        # Essai 2: non structuré. Risque de tomber sur un résultat pas dans la bonne ville.
        LOG(f'Essai 2 : "{adresse.pour_nominatim()}" ', bavard=bavard)
        lieu = localisateur.geocode(f"{adresse.pour_nominatim()}", exactly_one=False)
        if lieu is not None:
            return lieu
        else:
            raise LieuPasTrouvé(f"{adresse}")


        
#####################
### Avec overpass ###
#####################


def réessaie(n_max):
    """
    Renvoie un décorateur qui relance la fonction au maximum n_max fois en attendant 1mn entre deux essais jusqu’à ce quelle fonctionne.
    """
    def décorateur(f):
        def rés(*args, **kwargs):
            n_restant = n_max
            while n_restant > 0:
                try:
                    return f(*args, **kwargs)
                except overpy.exception.OverpassGatewayTimeout as e:
                    n_restant -= 1
                    print(f"Erreur dans {f.__name__} : {e}")
                    if n_restant == 0:
                        print("J’abandonne")
                    else:
                        print("Je réessaie dans 1mn")
                        time.sleep(60)
        return rés
    return décorateur


def réessaie_avec_arg_plus_petit(f, n_max):
    """
    Entrée : f (float -> 'a)
             n_max (int)
    Renvoie la fonction qui réessaie de lancer f au plus n_max fois, en divisant pas deux son arg à chaque fois.
    """
    def rés(x, n_restant=n_max):
        try:
            return f(x)
        except overpy.exception.OverpassGatewayTimeout as e:
            print(f"Erreur dans {f.__name__} : {e}")
            if n_restant == 0:
                print("J’abandonne")
            else:
                print("Je réessaie dans 20s")
                time.sleep(20)
                return rés(x/2, n_restant-1)
    return rés


def nœuds_of_rue(adresse, bavard=0):
    """
    Sortie : liste des nœuds osm correspondant aux ways correspondant à l'adresse.
    """

    lieu = cherche_lieu(adresse, seulement_non_structurée=True, bavard=bavard)
    LOG(f"rd.nœuds_of_rue : la recherche Nominatim pour {adresse} a donné {lieu}.", bavard=bavard)

    ids_way = [truc.raw["osm_id"] for truc in lieu if truc.raw["osm_type"]=="way"]
    ids_node = [truc.raw["osm_id"] for truc in lieu if truc.raw["osm_type"]=="node"]
    LOG(f"Voici les ids_way trouvés : {ids_way}", bavard=bavard)
    if len(ids_way) > 0:
        return nœuds_of_idsrue(ids_way, bavard=bavard-1)
    elif len(ids_node) > 0:
        return ids_node
    else:
        return []

    
def bb_enveloppante(nœuds, bavard=0):
    """
    Entrée : nœuds (int iterable), liste d’id_osm de nœuds
    Sortie : la plus petite bounding box contenant ces nœuds.
    """
    api = overpy.Overpass()
    req = f"""
    node(id:{",".join(map( str, nœuds))});
    out;
    """
    if bavard>0: print(req)
    rés = api.query(req).nodes
    lons = [n.lon for n in rés]
    lats = [n.lat for n in rés]
    # bb :sone
    return float(min(lats)), float(min(lons)), float(max(lats)), float(max(lons))


def nœuds_dans_bb(bb, tol=0):
    """
    Entrée : bb, bounding box (s,o,n,e)
             tol (float>=0)
             dtol (float >0)
    Sortie : liste des nœuds osm trouvés dans la bb.
    """
    print("(nœuds_dans_bb) J’attends 5s pour overpass.")
    time.sleep(5)
    api = overpy.Overpass()
    s, o, n, e = bb
    req = f"node({s-tol}, {o-tol}, {n+tol}, {e+tol});out;"
    return [n.id for n in api.query(req).nodes]
    
    

def ways_contenant_nodes(nœuds):
    """
    Entrée : nœuds (int itérable), id_osm de nœuds
    Sortie : liste des ways avec tag highwaycontenant au moins un élément de nœuds.
    """
    api = overpy.Overpass()
    requête = f"""
    node(id:{",".join(map( str, nœuds))});
    way[highway](bn);
    out;
    """
    return api.query(requête).ways


def nœuds_reliés(nœuds):
    """
    Entrée : itérable de nœuds osm
    Sortie : liste des nœuds sur un way contenant un des nœuds de nœuds.
    """
    ways = ways_contenant_nodes(nœuds)
    res = []
    for w in ways:
        res.extend(w._node_ids)
    return res

# nœuds de place saint louis de gonzague = [782224313, 782408135, 8428498156, 782155281, 343660472, 782224313]


def nœudsOfIdsway(ids_ways, api, bavard=0):
    """
    Entrée : ids_rue (int itérable), ids osm de ways.
    Sortie : liste des nœuds de celles-ci.
    """
    requête = f"""
            way(id:{",".join(map(str, ids_ways))});
            out;"""
    LOG(requête, bavard=bavard)
    print("J’attends 3s pour overpass.")
    time.sleep(3)
    rés_req = api.query(requête)
    return reduce(
        lambda x, y: x+y,
        [w._node_ids for w in rés_req.ways],
        []
    )


    
def zones_piétonnes(bbox, g, bavard=0) -> list:
    """
    Sortie :  les zones piétonnes (area=yes, highway=pedestrian ou footway) de la zone indiquée.
    liste de couples (nom, liste de nœuds).
    Seules les zones ayant au moins deux sommets sont renvoyées.
    """
    
    requête = f"""
    [out:json];
    (
    nwr[area='yes'][highway='pedestrian']{bbox};
    );
    out;
    """

    api = overpy.Overpass(url="https://lz4.overpass-api.de/api/interpreter", max_retry_count=5, retry_timeout=5)
    LOG(f"requête overpass : \n{requête}", bavard=bavard)
    rés_req = api.query(requête)

    places = []
    for w in rés_req.ways:
        nœuds = [s for s in w._node_ids if s in g]
        if len(nœuds) > 1:
            nom = w.tags.get("name", "")
            places.append((nom, nœuds))
    # return rés_req.relations

    for r in rés_req.relations:
        nom = r.tags.get("name", "")
        ways = [w.ref for w in r.members]
        nœuds = [n for n in nœudsOfIdsway(ways, api) if n in g]
        places.append((nom, nœuds))

    return places
    


def tousLesLieuxNommés(bbox, bavard=0):
    """
    Renvoie la requête overpass pour récupérer tous les lieux nommés dans la bbox indiquée.
    Les rues (highway) sont exclues.
    """
    
    return f"""
    [out:json];
    (
    nwr[name][!highway]{bbox};
    );
    out center;
    """
    


def récup_catégorie_lieu(catégorie_lieu: str, zone_overpass="area.searchArea", préfixe_requête="", bavard=0):
    """
    Renvoie la requête overpass pour obtenir les objets (Node, Way, Relation) ayant un tag de la catégorie indiquée, ainsi qu’un tag 'name'.
    Paramètres:
        zone_overpass : si pas défaut, doit être une bounding box.
        préfixe_requête : sera placé au début de la requête. Si zone_overpass est laissée à area.searchArea, ce préfixe doit définir le searchArea. Par exemple  area[name="{nom_de_la_ville}"]->.searchArea;
    """
    assert zone_overpass != "area.searchArea" or préfixe_requête != "", "Il faut remplir zone_overpass ou préfixe_requête."
    requête = f"""
    [out:json];
    {préfixe_requête}
    (
    nwr[{catégorie_lieu}][name]({zone_overpass});
    );
    out center; // Rajoute les coords des centres des objets. Disponible ensuite dans les objets de type overpy.Way et overpy.Relation dans les attributs center_lon et center_lat.
    """
    LOG(f"Requête overpass : {requête}", bavard=bavard)
    return requête


def coords_of_objet_overpy(o, type_objet_osm: str):
    """
    Entrée:
       o, un objet overpy (Node, Way, ou Rel)
       type_objet_osm: "nœud" dans le cas d’un Node, n’importe quoi d’autre sinon.

    Sortie ((float, float)):
       coordonnées de celui-ci. (lon, lat)

    Pour un nœud, les coords sont enregistrées dans l’objet dans des attributs lon et lat.
    Pour un way ou une rel, elles sont dans des attributs center_lon et center_lat, à condition d’avoir mis un « out center » à la fin de la requête overpass.
    """
    if type_objet_osm == "nœud":
        return float(o.lon), float(o.lat)
    else:
        return float(o.center_lon), float(o.center_lat)


def traitement_req_récup_lieux(requête: str, arbre_a: mo.ArbreArête, tous_les_id_osm=None, force=False, bavard=0):
    """
    Traite la requête overpass chargée de récupérer des lieux.

    Entrées:
        req : une requête overpass
        arbre_a : R-arbre d’arête dans lequel chercher l’arête la plus proche de chaque lieu.

    Sortie (Lieu list × Lieu list) : (nouveaux lieu (à bulk_creater), lieux à màj)

    Paramètres:
        force, si True on mets à jour même les lieux déjà présents dans la base et avec le même json_nettoyé
        tous_les_id_osm, si True les lieux dont l’id y figurent seront mis dans à_màj si des différences avec celui de la base sont détectér, et ignorés sinon. Si tous_les_id_osm est faux, tous les lieux seront mis dans les nouveaux lieux.
    """
    à_créer, à_màj = [], []
    dicos = dicos_of_requête(requête, bavard=bavard)
    for d in dicos:
        l, créé, utile = mo.Lieu.of_dico(d, arbre_a, tous_les_id_osm=tous_les_id_osm, créer_type=True, force=force)
        if créé:
            à_créer.append(l)
        elif utile:
            à_màj.append(l)
    return à_créer, à_màj



def dicos_of_requête(requête: str, bavard=0) -> list:
    """
    Entrée : requête overpass
    Sortie (liste de dicos sérialisables) : résultat d’icelle.
    Les dicos ont pour clefs lon, lat, type, catégorie, id_osm, ainsi que tous les tags présents sur osm.
    """
    
    ## Exécuter la requête
    api = overpy.Overpass(url="https://lz4.overpass-api.de/api/interpreter", max_retry_count=3, retry_timeout=5)
    LOG(f"requête overpass : \n{requête}", bavard=bavard)
    rés_req = api.query(requête)
    print(f"\nTraitement des {len(rés_req.nodes)} nœud, {len(rés_req.ways)} ways , et {len(rés_req.relations)} relations obtenues.\n")

    
    ## Créer les dicos
    champs_à_traduire = {"name": "nom",
                         "alt_name": "autre_nom",
                         "opening_hours": "horaires",
                         "phone": "tél",
                         }
    res = []
    for x, type_objet_osm in [(n, "nœud") for n in rés_req.nodes] + [(w, "way") for w in rés_req.ways] + [(r, "rel") for r in rés_req.relations]:
        if type_objet_osm != "rel" or "network" not in x.tags:  # J’élimine les lignes de bus
            lon, lat = coords_of_objet_overpy(x, type_objet_osm)
            d = {"id_osm": x.id,
                 "lon": lon, "lat": lat,
                 }
            d.update(x.tags)
        
            for c in champs_à_traduire:
                if c in d:
                    val = d.pop(c)
                    d[champs_à_traduire[c]] = val
                    
            res.append(d)
        
    return res


def lieux_of_ville(ville: mo.Ville, arbre_a: mo.ArbreArête, bavard=0, force=False):
    
    """
    Entrée :
        arbre_a, arbre d’arête utilisé pour associer l’arête la plus proche à chaque lieu.

    Sortie (Lieu list) : liste de Lieux (objets osm avec un tag «name») obtenus en cherchant la ville dans overpass.

    Effet : Les nouveaux lieux ont été créés, les anciens ont été mis à jour si une différence a été détectée par traitement_req_récup_lieux.

    Paramètres:
        force, si True on màj tous les lieux déjà présents, même si même dico obtenu par traitement_req_récup_lieux
    """
    
    res = []
    tous_les_id_osm = set([i for i, in mo.Lieu.objects.all().values_list("id_osm")])
    requête = tousLesLieuxNommés(ville.bbox())
    LOG(requête, bavard=bavard)
    à_c, à_m = traitement_req_récup_lieux(requête, arbre_a, tous_les_id_osm, force=force, bavard=bavard)
    
    print(f"(lieux_of_ville) Création de {len(à_c)} nouveaux lieux")
    mo.Lieu.objects.bulk_create(à_c, batch_size=2000)
    tous_les_id_osm.update((l.id_osm for l in à_c))
    print(f"(lieux_of_ville) Màj des {len(à_m)} lieux modifiés")
    mo.Lieu.objects.bulk_update(à_m, ["nom", "horaires", "tél", "type_lieu", "json_tout", "ville", "arête"], batch_size=2000)

    res.extend(à_c+à_m)
    return res


def lieux_of_bb(bb, bavard=0):
    """
    Entrée : bb (float×float×float×float)
    Sortie : liste de dico des lieux (amenity, shop, tourism, leisure) obtenus en cherchant la ville dans overpass.
    Les clefs de chaque dico sont :
        - id_osm
        - lon
        - lat
        - catégorie (qui vaut "amenity", "shop" ou "tourism")
        - type qui est la clef associée au tag amenity, shop ou tourism
        et tous les tags présents dans osm.
    """
    res = []
    for catégorie_lieu in ["amenity", "shop", "tourism"]:
        req = récup_catégorie_lieu(
            catégorie_lieu,
            zone_overpass=str(bb)[1:-1],
            bavard=bavard
        )
        res.extend(traitement_req_récup_lieux(req, catégorie_lieu)[0])
    return res


def lieux_of_types_lieux(bb, types, bavard=0):
    """
    Entrées:
        bb (float×float×float×float)
        types (TypeLieu iterable)

    Sortie (dico list) : les lieux des types indiqués dans la bbox indiquée.
    """
    print(f"types reçus : {types}")

    # Tri par catégories de lieux:
    dico_type = {}  # dico catégorie -> liste des types de lieu de cette catégorie
    for tl in types:
        if tl.catégorie not in dico_type:
            dico_type[tl.catégorie] = []
        dico_type[tl.catégorie].append(tl)

    res = []
    for cat, tl_cat in dico_type.items():
        milieu_requête = ""
        for tl in tl_cat:
            milieu_requête += f"nwr{tl.pour_overpass()}{bb};"
        requête = f"""
        ({milieu_requête});
        out center;
        """
        LOG(f"Requête overpass:\n {requête}", bavard=1)
        res.extend(dicos_of_requête(requête, bavard=bavard))
        
    LOG(f"Résultat :\n {res}", bavard=1)
    return res


def lieux_of_types_lieux_tenace(centre, rayon, types, bavard=0, n_max=5):
    return réessaie_avec_arg_plus_petit(lambda r: lieux_of_types_lieux(centre, r, types, bavard=bavard), n_max)(rayon)


########## Interpolation des adresses ##########
## Plus utilisé maintenant pour la France puisqu'il y a data.gouv

def charge_rue_num_coords():
    """ Renvoie le dictionnaire ville -> rue -> parité -> liste des (numéros, coords)"""
    entrée = open(CHEMIN_RUE_NUM_COORDS, encoding="utf-8")
    res = {}
    for ligne in entrée:
        villerue, tmp = ligne.strip().split(":")
        ville, rue = villerue.split(";")
        ville = normalise_ville(ville)
        rue = normalise_rue(rue, ville)
        données = tmp.split(";")
        ville_n = ville.nom_norm
        if ville_n not in res: res[ville_n] = {}
        res[ville_n][rue] = ([], [])  # numéros pairs, numéros impairs

        for k in range(2):
            if données[k] != "":
                for x in données[k].split("|"):
                    num, lat, lon = x.split(",")
                    res[ville_n][rue][k].append((int(num), (float(lat), float(lon))))
    return res

#print("Chargement du dictionnaire ville -> rue -> parité -> liste des (numéros, coords).")
#D_RUE_NUM_COORDS = charge_rue_num_coords()


def sauv_rue_nom_coords(d=None):
    """ Sauvegarde le dico ville -> rue -> parité -> liste des (numéros, coords) dans le fichier CHEMIN_JSON_NUM_COORDS.
    Format :
    Une ligne pour chaque couple (ville,rue).
    ville; rue : liste_pairs;liste_impairs
    Où liste_pairs et liste_impairs sont des (num, lat, lon) séparés par des |
    """
    if d is None:
        d=charge_rue_num_coords()
    sortie = open(CHEMIN_JSON_NUM_COORDS,"w", encoding="utf-8")
    for ville in d.keys():
        villen = normalise_ville(ville)
        for rue in d[ville].keys():
            ruen = normalise_rue(rue)
            pairs   = [ str((num,lat,lon))[1:-1] for (num,(lat,lon)) in d[ville][rue][0] ]
            impairs = [ str((num,lat,lon))[1:-1] for (num,(lat,lon)) in d[ville][rue][1] ]
            à_écrire = f"{villen};{ruen}:" + "|".join(pairs) + ";" + "|".join(impairs)
            sortie.write(à_écrire+"\n")
    

def barycentre(c1, c2, λ):
    """ Entrée : c1,  c2 des coords
                 λ ∈ [0,1]
        Sortie : λc1 + (1-λ)c2"""
    return (λ*c1[0]+(1-λ)*c2[0], λ*c1[1]+(1-λ)*c2[1])


class CoordsPasTrouvées(Exception):
    pass


def coords_of_adresse(adresse, bavard=0):
    """ Cherche les coordonnées de l’adresse fournie en interpolant parmi les adresses connues."""

    LOG_PB("J’ai eu besoin de recup_donnees.coords_of_adresse")
    D_RUE_NUM_COORDS = charge_rue_num_coords()
    num = adresse.num
    ville = adresse.ville
    rue = adresse.rue_norm
    
    k = num % 2  # parité du numéro
    if rue not in D_RUE_NUM_COORDS[str(ville)]:
        raise CoordsPasTrouvées(f"Rue inconnue : {adresse.rue} (normalisé en {rue}).")
    l = D_RUE_NUM_COORDS[str(ville)][rue][k]
    if len(l) < 2:
        raise CoordsPasTrouvées(f"J’ai {len(l)} numéro en mémoire pour {rue} ({ville}) du côté de parité {k}. Je ne peux pas interpoler.")

    else:
        deb, c1 = -1, (-1, -1)
        fin, c2 = -1, (-1, -1)
        for (n, c) in l:
            if n <= num:
                deb, c1 = n, c
            if n >= num:
                fin, c2 = n, c
                break
        if (deb, c1) == (-1, (-1, -1)):  # num est plus petit que tous les éléments de l
            ((deb, c1), (fin, c2)) = l[:2]
        elif (fin, c2) == (-1, (-1, -1)):  # num est plus grand que tous les éléments de l
            ((deb, c1), (fin, c2)) = l[-2:]
        if bavard>0: print(f"Je connais les coords des numéros {deb} et {fin} de la rue {rue}")
        if deb==fin:
            return c1
        else:
            λ  = (num-fin)/(deb-fin)
            return barycentre(c1, c2, λ)





    
### Rien à voir ### 


def kilométrage_piéton():
    """ Rien à voir : calcul du kilométrage de voies marquées « pedestrian » ou « footway »."""
    res = []
    for c in root:
        if c.tag == "way":
            for truc in c:
                if truc.tag == "tag" and truc.attrib["k"] == "highway" and truc.attrib["v"] in ["pedestrian", "footway"] :
                    res.append(c)
    for c in res:
        for truc in c:
            if truc.tag == "tag" and truc.attrib["k"] == "name": print(truc.attrib["v"])
# #Faire une classe Nœud_OSM pour extraire les tags, les nœuds d'une voie etc
