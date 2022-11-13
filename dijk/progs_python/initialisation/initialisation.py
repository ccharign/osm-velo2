#!/usr/bin/python3
# -*- coding:utf-8 -*-

import os
import osmnx

from time import perf_counter
from pprint import pprint, pformat

from django.db import close_old_connections, transaction
from dijk.models import Ville, Zone, Cache_Adresse, Ville_Zone, Sommet, Rue, Arête, Lieu
from django.db.models import Count

from dijk.progs_python.params import DONNÉES, RACINE_PROJET
from initialisation.noeuds_des_rues import extrait_nœuds_des_rues
from lecture_adresse.normalisation import arbre_rue_dune_ville, partie_commune, prétraitement_rue, normalise_rue
from graphe_par_networkx import Graphe_nx
from petites_fonctions import chrono, LOG, supprime_objets_par_lots

import initialisation.vers_django as vd
from quadrarbres import QuadrArbreSommet, QuadrArbreArête
from initialisation.amenities import charge_lieux_of_ville, ajoute_ville_et_rue_manquantes
from initialisation.communes import charge_villes

### Fonctions pour (ré)initialiser ou ajouter une nouvelle ville ou zone.



# def quadArbreDeZone(z_d, bavard=0):
#     l = list(Sommet.objects.filter(villes__zone=z_d))
#     tic = perf_counter()
#     res = QuadrArbreSommet.of_list(l)
#     chrono(tic, f"arbre quad de la zone {z_d}", bavard=bavard)
#     return res


def quadArbreAretesDeZone(z_d, sauv=True, bavard=0):
    """
    Entrée : z_d (mo.Zone)
    Sortie : arbre des arêtes de cette zone.
    Effet : si sauv, recalcule et enregistre l’arbre à l’adresse "{DONNÉES}/{z_d.nom}/arbre_arêtes_{z_d}"
            sinon, l’arbre est chargé depuis le disque.
    """
    
    
    if sauv:
        l = list(z_d.arêtes())
        LOG(f"Villes de la zone {z_d} : {tuple(z_d.villes())}\n {len(l)} arêtes.")
        tic = perf_counter()
        res = QuadrArbreArête.of_list_darêtes_d(l)
        rép = os.path.join(DONNÉES, z_d.nom)
        os.makedirs(rép, exist_ok=True)
        res.sauv(os.path.join(rép, f"arbre_arêtes_{z_d}"))
        print(f"Arbre sauvegardé dans {os.path.join(rép, f'arbre_arêtes_{z_d}')}")
        chrono(tic, f"création et sauvegarde de l’arbre quad de la zone {z_d}", bavard=bavard)
    else:
        dossier_données = os.path.join(DONNÉES, str(z_d))
        chemin = os.path.join(dossier_données, f"arbre_arêtes_{z_d}")
        tic = perf_counter()
        LOG(f"Chargement de l’arbre quad des arêtes depuis {chemin}", bavard=bavard)
        res = QuadrArbreArête.of_fichier(chemin)
        tic = chrono(tic, "Chargement de l’arbre quad des arêtes", force=True)
                
    return res




def supprime_arêtes_en_double():
    """
    Inutile normalement. Supprime les arêtes ayant même géom qu’une autre.
    """
    déjà_vue = set()  # geom des arêtes déjà vues
    à_supprimer = []
    n = 0
    for a in Arête.objects.all():
        if a.geom in déjà_vue:
            à_supprimer.append(a)
        else:
            déjà_vue.add(a.geom)
        n += 1
        if not n%1000: print(f"{n} arêtes vues")
    print(f"Suppression de {len(à_supprimer)} arêtes")
    supprime_objets_par_lots(à_supprimer)

    

def charge_graphe_de_ville(ville_d, pays="France", bavard=0, rapide=0):
    """
    Récupère le graphe grâce à osmnx et le charge dans la base.
    Une marge de 500m est prise. De sorte que les sommets et arêtes à moins de 500m d’une frontière entre deux villes seront au final associés à ces deux villes.
    """

    ## Récup des graphe via osmnx
    print(f"\nRécupération du graphe pour « {ville_d.code} {ville_d.nom_complet}, {pays} » avec une marge :\n")
    gr_avec_marge = osmnx.graph_from_place(
        {"city": f"{ville_d.nom_complet}", "postcode": ville_d.code, "country": pays},
        network_type="all",  # Tout sauf private
        retain_all="False",  # Sinon il peut y avoir des enclaves déconnectées car accessibles seulement par chemin privé (ex: CSTJF)
        buffer_dist=500  # Marge de 500m
    )
    print("\n\nRécupération du graphe exact:\n")
    gr_strict = osmnx.graph_from_place(
        {"city": f"{ville_d.nom_complet}", "postcode": ville_d.code, "country": pays},
        network_type="all", retain_all="True"
    )
    g = Graphe_nx(gr_avec_marge)

    ## Noms des villes ajouté dans g
    for n in gr_strict:
        g.villes_of_nœud[n] = [ville_d.nom_complet]

    ## Nœuds des rues
    print("\n\nCalcul des nœuds de chaque rue")
    dico_rues, places_piétonnes = extrait_nœuds_des_rues(g, bavard=bavard-1)  # dico ville -> rue_n -> (rue, liste nœuds) # Seules les rues avec nom de ville, donc dans g_strict seront calculées.
    print(f"\nPlaces piétonnes trouvées : {places_piétonnes}\n")
    print("Écriture des nœuds des rues dans la base.")
    close_old_connections()
    vd.charge_dico_rues_nœuds(ville_d, dico_rues[ville_d.nom_complet])

    ## Arbrex lex des rues
    print("Création de l'arbre lexicographique")
    arbre_rue_dune_ville(
        ville_d,
        dico_rues[ville_d.nom_complet].keys()
    )

    ## Désorientation
    close_old_connections()
    print("\nDésorientation du graphe")
    vd.désoriente(g, bavard=bavard-1)
    
    ## Transfert du graphe
    close_old_connections()
    sommets, crées, màj = vd.transfert_graphe(g, ville_d, bavard=bavard-1, rapide=rapide)
    
    vd.ajoute_ville_à_sommets_et_arêtes(
        ville_d,
        sommets,
        crées+màj,
        bavard=bavard-1
    )
    return crées, màj


def ajoute_ville(nom: str, code: int, nom_zone: str, force=False, pays="France", bavard=0):
    """
    Ajoute la ville dans la zone indiquée.
    Paramètres:
        force : si True les données seront rechargées même si données_présentes est vrai.
    """

    zone_d = Zone.objects.get(nom=nom_zone)
    ville_d = ville_of_nom_et_code_postal(nom, code)
    charge_ville(ville_d, zone_d, force=force, pays=pays, bavard=bavard)


def charge_ville(ville_d, zone_d,
                 force=False,
                 recalculer_arbre_arêtes_de_la_zone=True,
                 rajouter_les_lieux=True,
                 pays="France", bavard=2, rapide=0
                 ):
    """
    Entrées :
    Effet :
       Rajoute la ville indiquée (après avoir chargé si besoin son graphe et ses lieux) à la zone indiquée.

    Sortie (Ville×bool): (l’objet Ville, données ajoutées)

    NB : actuellement, les places piétonnes sont récupérées via la fonction noeuds_des_rues, et la procédure place_en_clique est programmée, mais elle n’est pas lancée, car sur Pau en tout cas, cela ne semble pas pertinent (cf la place Clemenceau).

    Paramètres:
        - force : si vrai, recharge les données même si le champ données_présentes valait True.
        - rapide (int) : indique la stratégie en cas de données déjà présentes.
             pour tout  (s,t) sommets voisins dans g,
                0 -> efface toutes les arêtes de s vers t et remplace par celles de g
                1 -> regarde si les arête entre s et t dans g correspondent à celles dans la base, et dans ce cas ne rien faire.
                        « correspondent » signifie : même nombre et mêmes noms.
                2 -> si il y a quelque chose dans la base pour (s,t), ne rien faire.
        - recalculer_arbre_arêtes_de_la_zone (bool) : si vrai le fichier contenant l’arbre quad des arêtes de la zone est recalculé (~4s pour Pau_agglo sur ma vieille machine)
    """

    assert isinstance(ville_d, Ville) and isinstance(zone_d, Zone)
    
    LOG(f"chargement de {ville_d}.\n")
    close_old_connections()
    
    rel, créée = Ville_Zone.objects.get_or_create(ville=ville_d, zone=zone_d)
    if créée:
        rel.save()

    modif = False
    
    if not ville_d.données_présentes or force:
        # création et enregistrement du graphe de la ville
        arêtes_créées, arêtes_màj = charge_graphe_de_ville(ville_d, pays=pays, bavard=bavard-1, rapide=rapide)
        #vd.ajoute_arêtes_de_ville(ville_d, arêtes_créées, arêtes_màj)
        modif = True

        
    ## Arbre q des arêtes
    if modif or recalculer_arbre_arêtes_de_la_zone or rajouter_les_lieux:  # Pour rajouter les lieux il faut être sûr que l’arbre des arêtes est à jour
        # Si recalculer_arbre_arêtes_de_la_zone est Faux, c’est que le calcul de l’arbre des arêtes sera lancé par crée_zone.
        arbre_a = crée_les_arbres_darêtes([ville_d], bavard=bavard-1)[zone_d]
        modif = True
        
    ## Lieux
    if rajouter_les_lieux:
        # De même, si rajouter_les_lieux est faux, c’est que c’est crée_zone qui s’en charge (pour éviter de recalculer l’arbre des arêtes à chaque ville.)
        charge_lieux_of_ville(ville_d, arbre_a=arbre_a)
        modif = True
    
    ville_d.données_présentes = True
    ville_d.save()
    return ville_d, modif


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
    "Pau": 64000,
    "Gelos": 64110,
    "Lée": 64320,
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

#VDS_PAU = [Ville.objects.get(nom_norm=partie_commune(v)) for v, _ in À_RAJOUTER_PAU]

ZONE_VOIRON = {
    "voiron": 38500,
    "saint étienne de crossey": 38960,
    "coublevie": 38500,
    "la buisse": 38500,
    "saint aupre": 38960,
}.items()

ZONE_GRENOBLE = [
    ("Grenoble", 38000),
    ("Saint Martin d’Hères", 38400),
    ("Eybens", 38320),
    ("Poisat", 38309),
    ("Voreppe", 38340),
    ("Échirolles", 38130),
]

#VDS_GRE = [Ville.objects.get(nom_norm=partie_commune(v)) for v, _ in ZONE_GRENOBLE]

def ville_of_nom_et_code_postal(nom: str, code: int):
    """
    Renvoie la ville de la base ayant le nom indiqué (après normalisation par partie_commune)
    En cas de non unicité, utilise le code postal pour départager.
    """

    essai1 = Ville.objects.filter(nom_norm=partie_commune(nom))
    if len(essai1) == 1:
        return essai1.first()
    elif len(essai1) == 0:
        raise RuntimeError("Ville pas trouvée. Avez-vous chargé la liste des villes avec communes.charge_villes() ?")
    else:
        return Ville.objects.get(nom_norm=partie_commune(nom), code=code)

    
def crée_les_arbres_darêtes(villes_modifiées, bavard=0):
    """
    Crée et sauvegarde les arbres d’arêtes des zones contenant au moins une des ville de villes_modifiées.
    Sortie : dictionnaire zone->arbre
    """
    LOG("\nCréation des R-arbres des arêtes", bavard=bavard)
    zones_modifiées = set()
    res = {}
    for v in villes_modifiées:
        zones_modifiées.update(v.zones())
    for z in zones_modifiées:
        print(f"Je recalcule l’arbre des arêtes de {z}")
        res[z] = quadArbreAretesDeZone(z, sauv=True)
    return res
 


def crée_zone(liste_villes_str, zone: str,
              réinit=False, effacer_cache=False, bavard=2, rapide=0,
              force_lieux=False
              ):
    """
    Entrée : liste_villes, itérable de (nom de ville, code postal). La ville par défaut sera la première de cette liste.
             zone (str), nom de la zone

    Effet : charge toutes ces ville dans la base, associées à la zone indiquée.
            Si la zone n’existe pas, elle sera créée, en y associant ville_défaut.
            Si la zone existe, l’ancienne est supprimée.

    Paramètres:
       Si réinit, tous les éléments associés à la zone (villes, rues, sommets, arêtes) ainsi que le cache sont au préalable supprimés.
       Si force_lieux, on charge les lieux même pour les villes qui avaient données_présentes à True.
       À FAIRE : Si effacer_cache, tous les fichiers .json du dossier cache du répertoire courant seront effacés.

    Sortie (Ville list) : liste des villes pour lesquelles on n’a pas pu récupérer les lieux.
    """
    
    close_old_connections()

    # Récup des villes :
    liste_villes_d = [ville_of_nom_et_code_postal(*c) for c in liste_villes_str]
    
    # Récupération ou création de la zone :
    z_d, créée = Zone.objects.get_or_create(nom=zone, ville_défaut=liste_villes_d[0])
    if not créée:
        z_d.sauv_csv()
        z_d.delete()
        z_d = Zone(nom=zone, ville_défaut=liste_villes_d[0])
        z_d.save()
        z_d.charge_csv()
    for v in liste_villes_d:
        z_d.ajoute_ville(v)
        
    # Réinitialisation de la zone :
    if réinit:
        for v in liste_villes_d:
            v.données_présentes = False
            v.save()
            print(f"J’ai mis données présentes à False pour {v}.")

            print("Suppression des relation sommet-ville et arête-ville :")
            supprime_objets_par_lots(list(Sommet.villes.through.objects.filter(ville_id=v.id)))
            supprime_objets_par_lots(list(Arête.villes.through.objects.filter(ville_id=v.id)))
            print("Suppression des sommets orphelins :")
            sansVille = Sommet.objects.all().alias(nbvilles=Count("villes")).filter(nbvilles=0)
            supprime_objets_par_lots(list(sansVille))
            # Ceci supprime au passage les arêtes liées aux sommets supprimés
            
        Cache_Adresse.objects.all().delete()

    # Vidage du cache d’osmnx ?
    
    # Chargement des villes :
    LOG(f"\nChargement des villes {liste_villes_d}", bavard=bavard)
    villes_modifiées = []
    for v_d in liste_villes_d:
        _, données_ajoutées = charge_ville(
            v_d, z_d,
            bavard=bavard, rapide=rapide, recalculer_arbre_arêtes_de_la_zone=False, rajouter_les_lieux=False
        )
        if données_ajoutées or force_lieux:
            villes_modifiées.append(v_d)

    # Arbre quad des arêtes
    if villes_modifiées:
        arbre_a = crée_les_arbres_darêtes(villes_modifiées, bavard=bavard)[z_d]
    else:
        arbre_a = quadArbreAretesDeZone(z_d, sauv=False)
    

    # Lieux (besoin de l’arbre des arêtes)
    LOG("\nChargement des lieux")
    échec_lieux = charge_lieux_of_liste_ville(villes_modifiées, arbre_a)
    if échec_lieux:
        print("Problème sur les villes :")
        pprint(échec_lieux)
    else:
        print("\nFini!")
    #print("Je lance ajoute_ville_et_rue_manquantes pour faire un deuxième essai de recherche des adresses des lieux sur toute la base..")
    #ajoute_ville_et_rue_manquantes(bavard=bavard-1)


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


def recharge_lieux_of_zone(zone, bavard=0):
    """
    Efface et recharge les lieux de la zone indiquée
    """
    villes = zone.villes()
    lieux = Lieu.objects.filter(ville__in=villes)
    lieux.delete()

    charge_lieux_of_liste_ville(villes, quadArbreAretesDeZone(zone, sauv=False))
    

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
