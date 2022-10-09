#!/usr/bin/python3
# -*- coding:utf-8 -*-

import os
import osmnx

from time import perf_counter
from pprint import pprint

from django.db import close_old_connections, transaction

from dijk.models import Ville, Zone, Cache_Adresse, Ville_Zone, Sommet, Rue, Arête

from dijk.progs_python.params import DONNÉES, RACINE_PROJET
from initialisation.noeuds_des_rues import extrait_nœuds_des_rues
from lecture_adresse.normalisation import arbre_rue_dune_ville, partie_commune, prétraitement_rue, normalise_rue
from graphe_par_networkx import Graphe_nx
from petites_fonctions import chrono, LOG

import initialisation.vers_django as vd
from quadrarbres import QuadrArbreSommet, QuadrArbreArête
from initialisation.amenities import charge_lieux_of_ville
from initialisation.communes import charge_villes

### Fonctions pour (ré)initialiser ou ajouter une nouvelle ville ou zone.



def quadArbreDeZone(z_d, bavard=0):
    l = list(Sommet.objects.filter(zone=z_d))
    tic = perf_counter()
    res = QuadrArbreSommet.of_list(l)
    chrono(tic, f"arbre quad de la zone {z_d}", bavard=bavard)
    return res


def quadArbreAretesDeZone(z_d, sauv=True, bavard=0):
    """
    Entrée : z_d (mo.Zone)
    Sortie : arbre des arêtes de cette zone
    Effet : si sauv, enregistre l’arbre à l’adresse "{DONNÉES}/{z_d.nom}/arbre_arêtes_{z_d}"
    """
    l = list(Arête.objects.filter(zone=z_d).prefetch_related("départ", "arrivée"))
    tic = perf_counter()
    res = QuadrArbreArête.of_list_darêtes_d(l)
    if sauv:
        rép = os.path.join(DONNÉES, z_d.nom)
        os.makedirs(rép, exist_ok=True)
        res.sauv(os.path.join(rép, f"arbre_arêtes_{z_d}"))
        print(f"Arbre sauvegardé dans {os.path.join(rép, f'arbre_arêtes_{z_d}')}")
    chrono(tic, f"création et sauvegarde de l’arbre quad de la zone {z_d}", bavard=bavard)
    return res


def charge_ville(nom, code, zone, recalculer_arbre_arêtes_de_la_zone=True,
                 rajouter_les_lieux=True,
                 ville_defaut=None, pays="France", bavard=2, rapide=0):
    """
    Entrées : nom (str), nom de la ville à charger.
              code (int)
              zone (str)
    Effet :
        Charge les données osm de la ville dans la base, à savoir:
           - Sommets
           - Arêtes
           - Rues
        Le tout associé à la zone indiquée, qui est créée si besoin.

    NB : actuellement, les places piétonnes sont récupérées via la fonction noeuds_des_rues, et la procédure place_en_clique est programmée, mais elle n’est pas lancée, car sur Pau en tout cas, cela ne semble pas pertinent (cf la place Clemenceau).

    Paramètres:
        - rapide (int) : indique la stratégie en cas de données déjà présentes.
             pour tout  (s,t) sommets voisins dans g,
                0 -> efface toutes les arêtes de s vers t et remplace par celles de g
                1 -> regarde si les arête entre s et t dans g correspondent à celles dans la base, et dans ce cas ne rien faire.
                        « correspondent » signifie : même nombre et mêmes noms.
                2 -> si il y a quelque chose dans la base pour (s,t), ne rien faire.
        - recalculer_arbre_arêtes_de_la_zone (bool) : si vrai le fichier contenant l’arbre quad des arêtes de la zone est recalculé (~4s pour Pau_agglo)
    """


    ## Création ou récupération de la zone
    if ville_defaut is not None:
        zone_d, créée = Zone.objects.get_or_create(nom=zone, ville_défaut=Ville.objects.get(nom_norm=partie_commune(ville_defaut)))
        if créée:
            zone_d.save()
    else:
        zone_d = Zone.objects.get(nom=zone)

        
    #ville_d = vd.ajoute_code_postal(nom, code)
    ville_d = Ville.objects.get(nom_norm=partie_commune(nom), code=code)
    rel, créée = Ville_Zone.objects.get_or_create(ville=ville_d, zone=zone_d)
    if créée: rel.save()

    
    ## Récup des graphe via osmnx
    print(f"\nRécupération du graphe pour « {ville_d.code} {ville_d.nom_complet}, {pays} » avec une marge :\n")
    gr_avec_marge = osmnx.graph_from_place(
        {"city": f"{ville_d.nom_complet}", "postcode": ville_d.code, "country":pays},
        network_type="all",  # Tout sauf private
        retain_all="False",  # Sinon il peut y avoir des enclaves déconnectées car accessibles seulement par chemin privé (ex: CSTJF)
        buffer_dist=500  # Marge de 500m
    )
    print("\n\nRécupération du graphe exact:\n")
    gr_strict = osmnx.graph_from_place({"city":f"{nom}", "postcode":code, "country":pays}, network_type="all", retain_all="True")

    g = Graphe_nx(gr_avec_marge)

    
    ## Noms des villes ajouté dans g (Graphe_nx)
    print("\n\nAjout du nom de ville.")
    for n in gr_strict:
        g.villes_of_nœud[n] = [nom]

        
    ## Nœuds des rues
    print("\n\nCalcul des nœuds de chaque rue")
    dico_rues, places_piétonnes = extrait_nœuds_des_rues(g, bavard=bavard-1)  # dico ville -> rue_n -> (rue, liste nœuds) # Seules les rues avec nom de ville, donc dans g_strict seront calculées.
    print("Écriture des nœuds des rues dans la base.")
    close_old_connections()
    vd.charge_dico_rues_nœuds(ville_d, dico_rues[nom])
    print(f"\nPlaces piétonnes trouvées : {places_piétonnes}\n")
    
    print("Création de l'arbre lexicographique")
    arbre_rue_dune_ville(
        ville_d,
        dico_rues[nom].keys()
    )

    ## Désorientation
    close_old_connections()
    print("\nDésorientation du graphe")
    vd.désoriente(g, bavard=bavard-1)
    
    ## Transfert du graphe
    close_old_connections()
    arêtes_créées, arêtes_màj = vd.transfert_graphe(g, zone_d, bavard=bavard-1, juste_arêtes=False, rapide=rapide)


    ## Arbre q des arêtes
    if recalculer_arbre_arêtes_de_la_zone:
        quadArbreAretesDeZone(zone_d, sauv=True)
        
    ## Lieux
    if rajouter_les_lieux:
        charge_lieux_of_ville(ville_d)
    
    
    ville_d.données_présentes = True
    ville_d.save()
    return ville_d


def crée_tous_les_arbres_des_rues():
    """
    Effet : crée tous les arbres lexicographiques des rues des villes qui appartiennent à au moins une zone, en repartant du nom complet présent dans la base.
    """

    dico_arbres = {}  # dico id_ville -> liste des rues
    for id_v, in Ville_Zone.objects.values_list("ville_id").distinct():
        dico_arbres[id_v] = []

    for nom_rue, id_v in Rue.objects.values_list("nom_complet", "ville_id"):
        dico_arbres[id_v].append(nom_rue)
    for id_v, l in dico_arbres.items():
        ville_d = Ville.objects.get(pk=id_v)
        arbre_rue_dune_ville(
            ville_d,
            map(prétraitement_rue, l)
        )


À_RAJOUTER_PAU = {
    "Gelos": 64110,
    "Lée": 64320,
    "Pau": 64000,
    "Lescar": 64230,
    "Billère": 64140,
    "Jurançon": 64110,
    "Ousse": 64320,
    "Idron": 64320,
    "Lons": 64140,
    "Bizanos": 64320,
    "Artigueloutan": 64420,
    "Mazères-Lezons": 64110
}.items()
VDS_PAU = [Ville.objects.get(nom_norm=partie_commune(v)) for v,_ in À_RAJOUTER_PAU]

ZONE_VOIRON = {
    "saint étienne de crossey": 38960,
    "coublevie": 38500,
    "la buisse": 38500,
    "saint aupre": 38960,
    "voiron": 38500
}.items()

ZONE_GRENOBLE = [
    ("Grenoble", 38000),
    ("Saint Martin d’Hères", 38400),
    ("Eybens", 38320),
    ("Poisat", 38309),
    ("Voreppe", 38340),
    ("Échirolles", 38130),
]
VDS_GRE = [Ville.objects.get(nom_norm=partie_commune(v)) for v,_ in ZONE_GRENOBLE]


def charge_zone(liste_villes, zone: str, ville_defaut: str, réinit=False, effacer_cache=False, bavard=2, rapide=0):
    """
    Entrée : liste_villes, itérable de (nom de ville, code postal)
             zone (str), nom de la zone
             ville_defaut (str), nom de la ville par défaut de la zone. Utilisé uniquement si la zone est créée.

    Effet : charge toutes ces ville dans la base, associées à la zone indiquée.
            Si la zone n’existe pas, elle sera créée, en y associant ville_défaut.

    Paramètres:
       Si réinit, tous les éléments associés à la zone (villes, rues, sommets, arêtes) ainsi que le cache sont au préalable supprimés.
       À FAIRE : Si effacer_cache, tous les fichiers .json du dossier cache du répertoire courant seront effacés.

    Sortie (Ville list) : liste des villes pour lesquels on n’a pas pu récupérer les lieux.
    """

    # Récupération ou création de la zone :
    zs_d = Zone.objects.filter(nom=zone)
    if zs_d.exists():
        z_d = zs_d.first()
    else:
        try:
            ville_défaut_d = Ville.objects.get(nom_complet=ville_defaut)
            z_d = Zone(nom=zone, ville_défaut=ville_défaut_d)
            z_d.save()
        except dijk.models.Ville.DoesNotExists:
            raise RuntimeError("Ville pas trouvée. Avez-vous chargé la liste des villes avec communes.charge_villes() ?")

    # Réinitialisation de la zone :
    if réinit:
        for v in z_d.villes():
            v.delete()
        Sommet.objects.filter(zone=z_d).delete()
        Cache_Adresse.objects.all().delete()

    # Vidage du cache d’osmnx ?
    
    # Chargement des villes :
    LOG("\nChargement des villes", bavard=bavard)
    villes_d = []
    for nom, code in liste_villes:
        villes_d.append(charge_ville(nom, code, zone, bavard=bavard, rapide=rapide, recalculer_arbre_arêtes_de_la_zone=False, rajouter_les_lieux=False))

    # Arbre quad des arêtes
    LOG("\nCréation du R-arbre des arêtes", bavard=bavard)
    arbre_a = quadArbreAretesDeZone(z_d, sauv=True)

    # Lieux (besoin de l’arbre des arêtes)
    LOG("\nChargement des lieux")
    échec_lieux = charge_lieux_of_liste_ville(villes_d, arbre_a)

    if échec_lieux:
        print("Problème sur les villes :")
        pprint(échec_lieux)
    else:
        print("\nFini!")
    return pb


def charge_lieux_of_liste_ville(villes, arbre_a: QuadrArbreArête) -> list:
    """
    Charge les lieux des villes de la liste éponyme.
    Sortie : villes pour lesquelles charge_lieux_of_ville a échoué.
    """
    pb = []
    for v_d in villes:
        try:
            charge_lieux_of_ville(v_d, arbre_a=arbre_a)
        except Exception as e:
            print(f"Problème pour {v_d}")
            pprint(e)
            pb.append(v_d)
    return pb


# def charge_multidigraph():
#     """
#     Renvoie le multidigraph de la zone défaut, supposé enregistré sur le disque. Plutôt pour tests.
#     """
#     s,o,n,e = BBOX_DÉFAUT
#     nom_fichier = f'{DONNÉES}/{s}{o}{n}{e}.graphml'
#     g = osmnx.load_graphml(nom_fichier)
#     return g


def charge_fichier_cycla_défaut(g, chemin=os.path.join(RACINE_PROJET, "progs_python/initialisation/données_à_charger/rues et cyclabilité.txt"), zone="Pau_agglo"):
    """
    Entrées : g (graphe)
              chemin (str)
    Effet : remplit la cycla_défaut des rues indiquées dans le fichier.
    
    """
    z_d = Zone.objects.get(nom=zone)
    with transaction.atomic():
        with open(chemin) as entrée:
            for ligne in entrée:
                if ligne[:6]=="cycla ":
                    cycla = 1.1**int(ligne[6:].strip())
                    print(f"\n\nRues de cyclabilité {cycla}")
                elif ligne.strip()=="":
                    None
                elif ligne[:2]=="à ":
                    v_d = Ville.objects.get(nom_norm=partie_commune(ligne[2:].strip().replace(":","")))
                    print(f"\n  Ville {v_d}")
                else:
                    nom_n, nom_osm,_ = normalise_rue(g, z_d, ligne.strip(), v_d)
                    print(f"    {nom_osm}")
                    rue = Rue.objects.get(nom_norm=nom_n, ville=v_d)
                    sommets = frozenset(g.dico_Sommet[s] for s in rue.nœuds())
                    for s in sommets:
                        for a in Arête.objects.filter(départ=s).select_related("arrivée"):
                            if a.arrivée in sommets:
                                if abs(a.cycla_défaut) < abs(cycla):
                                    print(f"À mettre à jour : ancienne cycla_défaut {a.cycla_défaut}")
                                    a.cycla_défaut=cycla
                                    a.save()
