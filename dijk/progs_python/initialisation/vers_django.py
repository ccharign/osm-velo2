
# -*- coding:utf-8 -*-


##################################################
### Transférer les données dans la base Django ###
##################################################

import re
import json
from pprint import pformat, pprint

from django.db import transaction, close_old_connections
from django.db.models import Q

from dijk.models import Ville, Rue, Sommet, Arête, Chemin_d, Ville_Zone, Zone
from dijk.progs_python.lecture_adresse.normalisation import prétraitement_rue, partie_commune
from params import LOG
from petites_fonctions import union, intersection, distance_euc, sauv_objets_par_lots
from lecture_adresse.arbresLex import ArbreLex

# L’arbre contient les f"{nom_norm}|{code}"
def à_mettre_dans_arbre(nom_n, code):
    return f"{nom_n}|{code}"



def arbre_des_villes(zone_d=None):
    """
    Renvoie l’arbre lexicographique des villes de la base.
    Si zone_d est précisé, seulement les villes de cette zone.
    """
    print("Création de l’arbre des villes")
    res = ArbreLex()
    if zone_d is None:
        villes = Ville.objects.all()
    else:
        villes = zone_d.villes()
    for v_d in villes:
        res.insère(à_mettre_dans_arbre(v_d.nom_norm, v_d.code))
    print("--- fini")
    return res


def ajoute_code_postal(nom, code):
    """
    Ajoute ou corrige le code postal de la ville.
    Sortie (models.Ville)
    """
    essai = Ville.objects.filter(nom_norm=partie_commune(nom)).first()
    if essai:
        essai.code=code
        essai.save()
        return essai
    else:
        raise RuntimeError(f"Ville pas trouvée dans la base INSEE : {nom}, {(code)}")

        
def nv_ville(nom, code, zone_d, tol=3):
    """
    Effet : si pas déjà présente, rajoute la ville dans la base django et dans l'arbre lex ARBRE_VILLES.
    Sortie : l'objet Ville créé ou récupéré dans la base.
    """
    nom_norm = partie_commune(nom)
    arbre = arbre_des_villes(zone_d=zone_d)
    dans_arbre, d = arbre.mots_les_plus_proches(à_mettre_dans_arbre(nom_norm, code), d_max=tol)
    
    if len(dans_arbre) > 0:
        print(f"Ville(s) trouvée(s) dans l'arbre : {tuple(dans_arbre)}")
        nom_n_corrigé, code_corrigé = tuple(dans_arbre)[0].split("|")
        if d>0:
            LOG(f"Avertissement : la ville {nom_norm, code} a été corrigée en {nom_n_corrigé, code_corrigé}")
        v_d = Ville.objects.get(nom_norm=nom_n_corrigé, code=code_corrigé)
        return v_d
    
    else:
        v_d = Ville(nom_complet=nom, code=code, nom_norm=nom_norm)
        v_d.save()
        rel = Ville_Zone(ville=v_d, zone=zone_d)
        rel.save()
        return v_d

    
def liste_attributs(g):
    """
    Entrée : g (multidigraph)
    Sortie : dico (attribut -> liste des valeurs) des arêtes qui apparaissent dans g
    Fonction utile pour régler les paramètres de cycla_défaut.
    """

    res = {}
    for s in g.nodes:
        for t in g[s].keys():
            for a in g[s][t].values():
                for att, val in a.items():
                    if att not in ["name", "length", "geometry", "osmid"]:
                        if att not in res:res[att]=set()
                        res[att].add(str(val))
    return res


def tuple_valeurs(a, att):
    """
    Renvoie le tuple des valeurs de l’attribut att dans l’arête a.
    """
    if att in a:
        if isinstance(a[att], list):
            return tuple(a[att])
        else:
            return (a[att],)
    else:
        return ()

def désoriente(g, bavard=0):
    """
    Entrée : g (Graphe_nx)
    Effet : rajoute les arêtes inverses si elles ne sont pas présentes, avec un attribut 'sens_interdit' en plus.
    """
    
    gx = g.multidigraphe

    def géom_of_arête_nx(a):
        """
        Sortie : sorted(a["geometry"].coords) si existe, None sinon.
        """
        if "geometry" in a:
            return sorted(a["geometry"].coords)
        else:
            return None
    
    def existe_inverse(s, t, a):
        """
        Indique si l’arête inverse de (s, t, a) est présente dans gx.
        """
        if s not in gx[t]:
            return False
        else:
            inverses_de_a = tuple(a_i for a_i in gx[t][s].values() if a.get("name", None)==a_i.get("name", None))
            if len(inverses_de_a) == 1:
                return True
            elif len(inverses_de_a) == 0:
                return False
            else:
                inverses_de_a = tuple(
                    a_i for a_i in inverses_de_a
                    if géom_of_arête_nx(a_i) == géom_of_arête_nx(a)
                )
                if len(inverses_de_a) == 1:
                    return True
                elif len(inverses_de_a) == 0:
                    return False
                else:
                    print(f"Avertissement : Arête en double : {s}, {t}, {inverses_de_a}")
                    return True

    
    def ajoute_inverse(s, t, a):
        LOG(f"ajout de l’arête inverse de {s}, {t}, {a}", bavard=bavard)
        a_i = {att: val for att, val in a.items()}
        if "maxspeed" in a and a["maxspeed"] in ["10", "20", "30"]:
            a_i["contresens cyclable"] = True
        else:
            a_i["sens_interdit"] = True
        gx.add_edge(t, s, **a_i)

        
    for s in gx.nodes:
        for t in gx[s].keys():
            if t != s:  # Il semble qu’il y ait des doublons dans les boucles dans les graphes venant de osmnx
                for a in gx[s][t].values():
                    if a["highway"] != "cycleway" and not any("rond point" in c for c in map(partie_commune, tuple_valeurs(a, "name"))) and not existe_inverse(s, t, a):
                        ajoute_inverse(s, t, a)


# @transaction.atomic
# def sauv_données(à_sauver):
#     """
#     Sauvegarde les objets en une seule transaction.
#     Pour remplacer bulk_create si besoin du champ id nouvellement créé.
#     """
#     for o in à_sauver:
#         o.save()
#     LOG("fin de sauv_données")



# def a_la_valeur(a, att, val):
#     """
#     Entrée : a (arête nx)
#              att
#              val
#     Indique si l’arête a à la valeur val pour l’attribut att
#     """
#     if att in a:
#         if isinstance(a[att], str):
#             return a[att]==val
#         elif isinstance(a[att], list):
#             return val in a[att]
#         else:
#             print(f"Avertissement : l’attribut {att} pour l’arête {a} n’était ni un str ni un list.")
#             return False
#     else:
#         return False

    



@transaction.atomic
def supprime_tout(à_supprimer):
    """
    Entrée : à_supprimer (iterable d’objets ayant une méthode delete)
    Effet : supprime de la base tous ces objets en une seule requête.
    """
    for x in à_supprimer:
        x.delete()
    
    
def transfert_graphe(g, ville_d,
                     bavard=0, rapide=1, juste_arêtes=False,
                     champs_arêtes_à_màj=[]
                     ):
    """
    Entrée : g (Graphe_nx)
             ville_d (instance de Zone)

    Effet : transfert le graphe dans la base Django.
    La longueur des arêtes est mise à min(champ "length", d_euc de ses sommets).
    
    Sortie : arêtes créées, arêtes mises à jour ou conservées
    
    Paramètres:
        rapide (int) : pour tout  (s,t) sommets voisins dans g,
                            0 -> efface toutes les arêtes de s vers t et remplace par celles de g
                            1 -> regarder si les arête entre s et t dans g correspondent à celles dans la base, et dans ce cas ne rien faire.
                        « correspondent » signifie : même nombre et mêmes noms.
                            2 -> si il y a quelque chose dans la base pour (s,t), ne rien faire.
        juste_arêtes (bool) : si vrai, ne recharge pas les sommets.
        champs_arêtes_à_màj : la valeur de ces champs sera mise à jour pour les arêtes déjà présentes.
    """
    assert isinstance(ville_d, Ville), f"transfert_graphe attend une ville et a reçu {ville_d}"
    gx = g.multidigraphe

    tous_les_sommets = Sommet.objects.all()
    print(f"{len(tous_les_sommets)} sommets dans la base")

    ### Sommets ###
    if not juste_arêtes:
        LOG("Chargement des sommets")
        à_créer = []
        à_màj = []
        nb = 0
        for s in g.multidigraphe.nodes:
            if nb%500==0: print(f"    {nb} sommets vus")
            nb += 1
            lon, lat = g.coords_of_nœud(s)
            essai = Sommet.objects.filter(id_osm=s).first()
            if essai is None:
                s_d = Sommet(id_osm=s, lon=lon, lat=lat)
                à_créer.append(s_d)
            else:
                s_d = essai
                # màj des coords au cas où...
                s_d.lon = lon
                s_d.lat = lat
                à_màj.append(s_d)

        ## Création/màj des sommets
        LOG(f"Ajout des {len(à_créer)} nouveaux sommets dans la base")
        sauv_données(à_créer)
        LOG(f"Mise à jour des {len(à_màj)} sommets modifiés")
        Sommet.objects.bulk_update(à_màj, ["lon", "lat"])

        ## ville des sommets
        LOG("Ajout de la ville à chaque sommet...")
        # Ne serait-il pas plus simple de tout supprimer puis tout recréer ?
        LOG("Sommets créés", bavard=bavard)
        rel_àcréer = []
        for s_d in à_créer:
            rel = Sommet.villes.through(sommet_id=s_d.id, ville_id=ville_d.id)
            rel_àcréer.append(rel)
        LOG("Sommets mis à jour", bavard=bavard)
        for s_d in à_màj:
            if ville_d not in s_d.villes.all():  # c’est ce test qui est lent a priori
                rel = Sommet.villes.through(sommet_id=s_d.id, ville_id=ville_d.id)
                rel_àcréer.append(rel)
        Sommet.villes.through.objects.bulk_create(rel_àcréer)


    ### Arêtes ###

    # pour profiling
    # temps = {"correspondance":0., "remplace_arêtes":0., "màj_arêtes":0., "récup_nom":0.}
    # nb_appels = {"correspondance":0, "remplace_arêtes":0, "màj_arêtes":0, "récup_nom":0}

    # Création du dico sommet -> liste de (voisin, arête) pour les arêtes déjà existantes dans la base.
    dico_voisins = {}
    toutes_les_arêtes = Arête.objects.all().select_related("départ", "arrivée")
    for a in toutes_les_arêtes:
        s = a.départ#.id_osm
        t = a.arrivée#e.id_osm
        if s not in dico_voisins:
            dico_voisins[s] = []
        dico_voisins[s].append((t, a))

    #@mesure_temps("récup_nom", temps, nb_appels)
    # def récup_noms(arêtes_d, nom):
    #     """ Renvoie le tuple des a∈arêtes_d qui ont pour nom 'nom'"""
    #     return [a_d for a_d in arêtes_d if nom == a_d.nom]

    
    #@mesure_temps("correspondance", temps, nb_appels)
    def correspondance(s_d, t_d, gx):
        """
        Entrées:
            - s_d, t_d (Sommet)
            - gx (multidigraph)

        Sortie (Arête list × Arête list × Arête list × Arête list) :
            (à_supprimer, à_créer, à_màj, à_garder)

        Ne prend en compte que les arêtes de s_d vers t_d.
        Deux arêtes sont considérées égales quand elles ont même géom.
        """
        
        s, t = s_d.id_osm, t_d.id_osm
        vieilles_arêtes = [a_d for (v, a_d) in dico_voisins.get(s_d, []) if v==t_d]
                    
        if t not in gx[s]:
            return vieilles_arêtes, [], [], []
        
        else:
            nouvelles_arêtes = [Arête.of_arête_nx(s_d, t_d, ax) for ax in gx[s][t].values()]
            à_màj = []
            à_supprimer = []

            def récup_arête(va):
                """
                Entrée : une vieille arête
                Effet :
                    Si elle est dans les nouvelles, elle est mise dans à_màj avec sa binôme, qui est supprimée de nouvelles_arêtes.
                    Sinon elle est mise dans à_supprimer
                """
                
                if va.départ.id_osm == 3206065247 and va.arrivée.id_osm == 7972899167:
                    print(f"récup_arête lancé sur l’arête {va}.\n nouvelles arêtes: {pformat(nouvelles_arêtes)}.\n Géométrie : {va.geom}, {[a.geom for a in nouvelles_arêtes]}")
                    
                    
                for (i, na) in enumerate(nouvelles_arêtes):
                    if na == va:  # NB: le __eq__ se base sur la géom.
                        à_màj.append((va, na))
                        nouvelles_arêtes.pop(i)
                        if va.départ.id_osm == 3206065247 and va.arrivée.id_osm == 7972899167:
                            print(f"Arête reconnue. nouvelles_arêtes={pformat(nouvelles_arêtes)}")

                        return None
                à_supprimer.append(va)

                
            for va in vieilles_arêtes:
                récup_arête(va)
                
            à_créer = nouvelles_arêtes
            à_màj, à_garder = màj_arêtes(à_màj)

            return (à_supprimer, à_créer, à_màj, à_garder)

    
    #@mesure_temps("màj_arêtes", temps, nb_appels)
    def màj_arêtes(arêtes_vn):
        """
        Entrées:
            - arêtes_vn (Arête×Arête list) : liste de couples (arête de la base, nouvelle arête)
        Effet:
            Met à jour les champs indiquées dans champs_arêtes_à_màj de l’arête de la base.
        Sortie : (les arêtes modifiées, arêtes pas modifiées). Il faudra encore un Arête.bulk_update sur la première liste.
        """
        à_màj, à_garder = [], []
        for va, na in arêtes_vn:
            modif = False
            for champ in champs_arêtes_à_màj:
                if va.__getattribute__(champ) != na.__getattribute__(champ):
                    modif = True
                    va.__setattribute__(champ, na.__getattribute__(champ))
            if modif:
                à_màj.append(va)
            else:
                à_garder.append(va)
        return à_màj, à_garder
    

    #@mesure_temps("remplace_arêtes", temps, nb_appels)
    # def nelles_arêtes(s_d, t_d, arêtes_x, bavard=0):
    #     """
    #     Sortie (Arête list): Arêtes django correspondant aux arêtes nx passées en arg.
    #     Effet : les arêtes à créer sont ajoutées dans à_créer.
    #     """
    #     à_créer = []
    #     for a_nx in arêtes_x:
    #         a_d = Arête.of_arête_nx(s_d, t_d, a_nx)
    #         à_créer.append(a_d)
    #     return à_créer

    LOG("Chargement des arêtes depuis le graphe osmnx", bavard)
    nb = 0
    à_créer = []
    à_màj = []
    à_supprimer = []
    à_garder = []
    #with transaction.atomic():  # Utile pour les suppressions d’anciennes arêtes.
    for s in gx.nodes:
            s_d = tous_les_sommets.get(id_osm=s)
            for t, _ in gx[s].items():
                if t != s:  # Suppression des boucles
                    nb += 1
                    if nb%500==0: print(f"    {nb} arêtes traitées\n ")  #{temps}\n{nb_appels}\n")
                    t_d = tous_les_sommets.get(id_osm=t)
                    if rapide < 2:
                        à_s, à_c, à_m, à_g = correspondance(s_d, t_d, gx)
                        if s_d.id_osm == 3206065247 and t_d.id_osm == 7972899167:
                            print(f"Arête problématique ! {à_s, à_c, à_m, à_g}")
                            input("")
                        à_supprimer.extend(à_s)
                        à_créer.extend(à_c)
                        à_màj.extend(à_m)
                        à_garder.extend(à_g)

    LOG(f"Suppression de {len(à_supprimer)} arêtes.", bavard=bavard)
    supprime_tout(à_supprimer)
    LOG(f"Ajout des {len(à_créer)} nouvelles arêtes dans la base", bavard=bavard)

    # debug
    # las = Arête.objects.filter(départ__id_osm=3206065247, arrivée__id_osm=7972899167)
    # print(f"Avant sauv_données : {pformat(tuple(las))}")
    # input("")
    
    sauv_objets_par_lots(à_créer)  # bulk_create pas possible

    # debug
    # las = Arête.objects.filter(départ__id_osm=3206065247, arrivée__id_osm=7972899167)
    # print(f"Après sauv_données : {pformat(tuple(las))}")
    # input("")
    
    if à_màj:
        LOG(f"Mise à jour des {len(à_màj)} anciennes arêtes", bavard=bavard)
        Arête.objects.bulk_update(à_màj, champs_arêtes_à_màj)
    else:
        LOG("Pas d’arête à mettre à jour", bavard=bavard)
    LOG(f"{len(à_garder)} arêtes conservées")

    #    print(f"{}")
    # ex d’arête sans sa ville : (3206065247, 7972899167) (id_osm des sommets)

    
    return à_créer, à_màj+à_garder
    

# def ajoute_zone_des_arêtes(zone_d, créées, màj):
#     ### Zone des arête
#     assert False, "Cette fonction est dépréciée. Passer par ajoute_arêtes_de_ville"
#     LOG("Ajout de la zone à chaque arête")
#     nb = 0
#     ## nouvelles arêtes -> rajouter zone_d mais aussi les éventuelles anciennes zones.
#     rel_àcréer = []
#     for a_d in créées:
#         for z in union([zone_d], intersection(a_d.départ.zone.all(), a_d.arrivée.zone.all())):
#             rel = Arête.zone.through(arête_id=a_d.id, zone_id=z.id)
#             rel_àcréer.append(rel)
#     Arête.zone.through.objects.bulk_create(rel_àcréer)
#     ## anciennes arêtes mises à jour -> rajouter zone_d et ville_d si pas présente.
#     rel_àcréer = []
#     for a_d in màj:
#         if zone_d not in a_d.zone.all():
#             rel = Arête.zone.through(arête_id=a_d.id, zone_id=zone_d.id)
#             rel_àcréer.append(rel)
#         nb += 1
#         if nb%1000==0: print(f"    {nb} arêtes traités")
#     Arête.zone.through.objects.bulk_create(rel_àcréer)

    
def ajoute_arêtes_de_ville(ville_d, créées, màj, bavard=0):
    """
    Ajoute les arêtes indiquées à la ville.
    """
    
    assert isinstance(ville_d, Ville)
    LOG(f"Ajout des arêtes à la ville {ville_d}")
    
    ## nouvelles arêtes -> rajouter ville_d mais aussi les éventuelles anciennes villes.
    rel_àcréer = []
    couples = set()  # juste pour débug
    n = 1
    for a_d in créées:
        villes_de_a = tuple(intersection(a_d.départ.get_villes(), a_d.arrivée.get_villes()))
        for v in villes_de_a:
            rel = Arête.villes.through(arête_id=a_d.id, ville_id=v.id)
            if (a_d, v) not in couples:
                couples.add((a_d, v))
            else:
                raise RuntimeError(f"Rel déjà créée : {a_d, v}. Ville de l’arête : {villes_de_a}. L’arête était la {n}ième traitée")
            rel_àcréer.append(rel)
            n += 1
        assert (a_d, ville_d) in couples
        # if a_d.départ.id_osm == 3206065247 and a_d.arrivée.id_osm == 7972899167:
        #     print(f"Arête problématique {a_d} !\n villes : {tuple(villes_de_a)}")
        #     input("")
    LOG(f"Enregistrement des {len(rel_àcréer)} relations pour les nouvelles arêtes.")
    assert len(rel_àcréer) == len(set(couples)), "Des relations ont été créées en double"
    # pprint(tuple(couples[:10])); input("")
    Arête.villes.through.objects.bulk_create(rel_àcréer, batch_size=2000)
    
    ## anciennes arêtes mises à jour -> rajouter ville_d si pas présente.
    arêtes_avec_la_ville = set(ville_d.arête_set.all())
    nb = 0
    rel_àcréer = []
    for a_d in màj:
        if a_d not in arêtes_avec_la_ville:
            rel = Arête.villes.through(arête_id=a_d.id, ville_id=ville_d.id)
            rel_àcréer.append(rel)
        nb += 1
        if nb%1000==0: print(f"    {nb} arêtes traités")
    LOG(f"Enregistrement des {len(rel_àcréer)} relations pour les anciennes arêtes.")
    Arête.villes.through.objects.bulk_create(rel_àcréer, batch_size=2000)



@transaction.atomic()
def charge_dico_rues_nœuds(ville_d, dico):
    """
    Entrée :
        - ville_d (instance de ville)
        - dico : un dico nom_de_rue -> liste de nœuds
    Effet :
        remplit la table dijk_rue. Si une rue était déjà présente, elle sera supprimée.
    """
    rues_à_créer=[]
    for rue_n, (rue, nœuds) in dico.items():
        #rue_n = prétraitement_rue(rue)
        assert rue_n == prétraitement_rue(rue_n), f"La rue suivante n’était pas normalisée : {rue_n}"
        nœuds_texte = ",".join(map(str, nœuds))
        vieilles_rues = Rue.objects.filter(nom_norm=rue_n, ville=ville_d)
        vieilles_rues.delete()
        rue_d = Rue(nom_complet=rue, nom_norm=rue_n, ville=ville_d, nœuds_à_découper=nœuds_texte)
        rues_à_créer.append(rue_d)
    Rue.objects.bulk_create(rues_à_créer)
        


def cycla_défaut_of_csv(chemin, bavard=0):
    """
    Entrée : adresse d’un csv contenant des nom de rue et des valeurs de cycla défaut
    Effet : change la cycla défaut des rues concernées.
    """

    @transaction.atomic()
    def change_cycla(rue_d, valeur):
        """
        Effet : met à valeur la cycla_défaut de toutes les arêtes de la rue.
        """
        for a in rue_d.arêtes.all():
            a.cycla_défaut=valeur
            a.save()

    


@transaction.atomic()
def met_en_clique(g, nœuds, nom, cycla_défaut=1.1, bavard=0):
    """
    Entrée : g (graphe)
             nœuds (liste d’id osm)
             nom (str)
    Effet : rajoute toutes les arêtes nécessaires pour que l’ensemble des sommets dans nœuds devienne une clique. Les longueurs sont prises comme la distance euclidienne entre les deux sommets. Le nom qui sera rentré est celui passé en arg.
    Paramètres:
        cycla_défaut (float) : cycla défaut à mettre aux arêtes créées.
    """
    cpt = 0
    for s in nœuds:
        s_d = Sommet.objects.get(id_osm=s)
        for t in nœuds:
            t_d = Sommet.objects.get(id_osm=t)
            if t!=s:
                if not Arête.objects.filter(départ__id_osm=s, arrivée__id_osm=t).exists():
                    a = Arête(
                        départ = s_d,
                        arrivée = t_d,
                        longueur = g.d_euc(s,t),
                        geom = f"{s_d.lon},{s_d.lat};{t_d.lon},{t_d.lat}",
                        cycla_défaut= cycla_défaut
                    )
                    a.save()
                    cpt+=1
    print(f"{cpt} nouvelles arêtes créées.")
    
    
def place_en_clique(g, v_d):
    """
    Effet : Transforme en clique toutes les places.
    """
    for r in Rue.objects.filter( Q(nom_complet__icontains="place") | Q(nom_complet__icontains="square"), ville=v_d):
        print(f"Mise en clique : {r}")
        met_en_clique(g, r.nœuds(), r.nom_complet)
    








    

### vieux trucs ###



# def nv(g, nom_ville):
#     return normalise_ville(g, nom_ville).nom_norm

# #code_postal_norm = {nv(v):code for v,code in TOUTES_LES_VILLES.items()}

# #Utiliser bulk_create
# #https://pmbaumgartner.github.io/blog/the-fastest-way-to-load-data-django-postgresql/

# def villes_vers_django(g):
#     """
#     Effet : réinitialise la table dijk_ville
#     """
#     Ville.objects.all().delete()
#     villes_à_créer=[]
#     for nom, code in TOUTES_LES_VILLES.items():
#         villes_à_créer.append( Ville(nom_complet=nom, nom_norm=nv(g, nom), code=code))
#     Ville.objects.bulk_create(villes_à_créer)

        
# def charge_rues(bavard=0):
#     """ 
#     Transfert le contenu du csv CHEMIN_NŒUDS_RUES dans la base.
#     Réinitialise la table Rue (dijk_rue)
#     """

#     # Vidage des tables
#     Rue.objects.all().delete()
#     #Sommet.objects.all().delete() # À cause du on_delete=models.CASCADE, ceci devrait vider les autres en même temps
    
#     rues_à_créer=[]
#     with open(CHEMIN_NŒUDS_RUES, "r") as entrée:
#         compte=0
#         nb_lignes_lues=0
#         for ligne in entrée:
#             nb_lignes_lues+=1
#             if nb_lignes_lues%100==0:
#                 print(f"ligne {nb_lignes_lues}")
#             if bavard>1:print(ligne)
#             ville_t, rue, nœuds_à_découper = ligne.strip().split(";")

#             ville=normalise_ville(ville_t)
#             ville_n = ville.nom_norm
#             ville_d = Ville.objects.get(nom_norm=ville_n) # l’objet Django. # get renvoie un seul objet, et filter plusieurs (à confirmer...)
            
#             rue_n = prétraitement_rue(rue)
#             rue_d = Rue(nom_complet=rue, nom_norm=rue_n, ville=ville_d, nœuds_à_découper=nœuds_à_découper)
#             rues_à_créer.append(rue_d)
            
#         Rue.objects.bulk_create(rues_à_créer)
            
#     print("Chargement des rues vers django fini.")



@transaction.atomic
def charge_csv_chemins(zone_t, réinit=False):
    """
    Effet : charge le csv de CHEMIN_CHEMINS dans la base. Dans celui-ci, les villes sont supposées être entre parenthèses.
    Si réinit, vide au prélable la table.
    """
    z_d = Zone.objects.get(nom=zone_t)
    if réinit:
        Chemin_d.objects.all().delete()
    with open(CHEMIN_CHEMINS) as entrée:
        à_créer=[]
        for ligne in entrée:
            print(ligne)
            AR_t, pourcentage_détour_t, étapes_t,rues_interdites_t = ligne.strip().split("|")
            p_détour = int(pourcentage_détour_t)/100.
            if AR_t=="True": AR=True
            else: AR=False
            if étapes_t: étapes_t = conversion_ligne(étapes_t)
            if rues_interdites_t: rues_interdites_t = conversion_ligne(rues_interdites_t)
            début, fin = étapes_t[:255], étapes_t[-255:]
            interdites_début, interdites_fin = rues_interdites_t[:255], rues_interdites_t[-255:]
            c_d = Chemin_d(zone=z_d, ar=AR, p_détour=p_détour, étapes_texte=étapes_t, interdites_texte=rues_interdites_t, début=début, fin = fin, interdites_début=interdites_début, interdites_fin=interdites_fin)
            c_d.sauv()


def conversion_étape(texte, bavard=0):
    """
    Entrée : texte d’une étape où la ville est entre parenthèses
    Sortie : texte d’une étape avec la ville séparée par une virgule.
    """
    # Lecture de la regexp
    e = re.compile("(^[0-9]*) *([^()]+)(\((.*)\))?")
    essai = re.findall(e, texte)
    if bavard > 1: print(f"Résultat de la regexp : {essai}")
    if len(essai) == 1:
        num, rue, _, ville = essai[0]
    elif len(essai) == 0:
        raise SyntaxError(f"adresse mal formée : {texte}")
    else:
        print(f"Avertissement : plusieurs interprétations de {texte} : {essai}.")
    num, rue, _, ville = essai[0]
    rue=rue.strip()
    ville=ville.strip()

    if not num:
        res=""
    else:
        res= f"{int(num)} "
    return res + f"{rue}, {ville}"


def conversion_ligne(ligne):
    """
    Entrée : ligne (str) étapes séparées par des ; où les villes sont entre parenthèses
    Sortie (str) : idem mais où les villes sont séparées par des virgules.
    """
    étapes = ligne.split(";")
    return ";".join(conversion_étape(é) for é in étapes)
