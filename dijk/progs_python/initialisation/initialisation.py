#!/usr/bin/python3
# -*- coding:utf-8 -*-

import os
from pprint import pprint
from time import perf_counter
from typing import Iterable
import logging

import osmnx
from geopandas import GeoSeries, GeoDataFrame

import dijk.models as mo
import dijk.progs_python.initialisation.vers_django as vd
import dijk.progs_python.recup_donnees as rd

from dijk.models import (ArbreArête, Arête, Cache_Adresse, Lieu, Rue,
                         SegmentArête, Sommet, Ville, Ville_Zone, Zone)
from dijk.progs_python.initialisation.amenities import charge_lieux_of_ville
from dijk.progs_python.params import RACINE_PROJET
from dijk.progs_python.quadrarbres import QuadrArbreArête
from django.db import close_old_connections, transaction
from django.db.models import Count
from graphe_par_networkx import Graphe_nx
from lecture_adresse.normalisation import (arbre_rue_dune_ville, normalise_rue,
                                           partie_commune, prétraitement_rue)
from petites_fonctions import LOG, chrono, paires, supprime_objets_par_lots

from initialisation.noeuds_des_rues import extrait_nœuds_des_rues
from dijk.progs_python.initialisation.geom_utils import union_de_géoms


#############################################################################
### Fonctions pour (ré)initialiser ou ajouter une nouvelle ville ou zone. ###
#############################################################################




def supprimeTousArbresArêtesDeLaBase():
    """Efface tous les arbres arêtes de la base."""
    if mo.ArbreArête.objects.all().count() > 0:
        a = mo.ArbreArête.uneRacine()
        print(f"Suppression de l’arbre de {a.getZones().all()}")
        a.supprime()
        supprimeTousArbresArêtesDeLaBase()
    # mo.ArbreArête.effaceTout()
    

def quadArbresArêtesDeLaBase():
    """Crée les arbres de toutes les zones non inclues dans une autre et les enregistre dans la base."""
    print("Suppression des anciens arbres")
    supprimeTousArbresArêtesDeLaBase()

    # Création des arbres
    for z in mo.Zone.objects.all():
        if not z.inclue_dans:
            print(f"Création de l’arbre de {z}")
            créeQuadArbreArêtesDeZone(z)

    # Association des arbres aux sous-zones
    for z in mo.Zone.objects.all():
        if z.inclue_dans:
            ancêtre = z.plusGrandeZoneContenant()
            print(f"J’associe à la zone {z} l’arbre de {ancêtre}")
            z.arbre_arêtes = ancêtre.arbre_arêtes
            z.save()

    
def créeQuadArbreArêtesDeZone(z_d: mo.Zone, bavard=0) -> ArbreArête:
    """
    Effet : Crée le quadArbre de la plus grande zone contenant z_d, l’enregistre dans la base, et l’associe à z_d ainsi qu’à toutes les zones contenant z_d.

    Sortie : l’arbre créé.
    """
    print(f"(Arbre des arêtes de la zone {z_d})")
    
    # Cas récursif
    if z_d.inclue_dans:
        res = créeQuadArbreArêtesDeZone(z_d.inclue_dans, bavard=bavard)
        z_d.arbre_arêtes = res
        z_d.save()
        return res

    # Cas de base
    else:
        qaa = QuadrArbreArête.of_list_darêtes_d(z_d.arêtes())
        res = qaa.sauv_dans_base(ArbreArête, SegmentArête)
        z_d.arbre_arêtes = res
        z_d.save()
        return res

    
    
def quadarbre_of_arêtes(arêtes: Iterable[Arête]) -> ArbreArête:
    """
    Entrée : itérable d’Arêtes
    Sortie (mo.ArbreArête) : le plus petit sous-arbre contenant les arêtes passées en arg.
    """
    print(f"{len(arêtes)} arêtes. Récupération des feuilles, càd des segmets d’arêtes.")
    feuilles = mo.ArbreArête.objects.filter(
        related_manager_segment__arête__in=arêtes  # Django est quand même balèze
    )
    print(f"Fini. {len(feuilles)} feuilles.\nCalcul de l’arbre:")
    return mo.ArbreArête.racine().sous_arbre_contenant(feuilles)


def quadArbreArêtesDeVille(v_d: mo.Ville):
    """Renvoie le plus petit sous-arbre de la base contenant les arêtes de v_d."""
    return QuadrArbreArête.of_list_darêtes_d(v_d.arêtes())



# def quadArbreArêtesDeToutesLesZones():
#     """
#     Enregistre dans la base la racine de l’arbre de chaque zone.
#     """
#     for z_d in mo.Zone.all():
#         a = quadArbreArêtesDeZone(z_d)
#         z_d.arbre_arêtes = a
#         z_d.save()



def supprime_arêtes_en_double():
    """Inutile normalement. Supprime les arêtes ayant même géom qu’une autre."""
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


def graphe_de_villes(villes: list[Ville], marge=500, pays="France"):
    """
    Renvoie le graphe de l’enveloppe convexe de l’union des villes passées an arg, avec la marge indiquée.

    Args:
       - villes: liste des villes à inclure
       - marge: en mètres
    """
    logging.info("Calcul de la géométrie de l’enveloppe convexe de %s", [v.nom_complet for v in villes])
    géoms = osmnx.geocode_to_gdf([ville.avec_code() for ville in villes])

    enveloppe = géoms.unary_union.convex_hull  # Ceci est une geometry
    # Il faut en refaire un gpd
    enveloppe_gdf = GeoDataFrame(geometry=[enveloppe], crs=géoms.crs)
    # On projette dans la projection classique de la France EPSG:2154
    # Afin d’avoir le buffer en mètres qui fonctionne
    # Puis remettre en lon lat (EPSG:4326) pour graph_of_polygon
    enveloppe_avec_marge = enveloppe_gdf.to_crs("EPSG:2154").buffer(marge).to_crs("EPSG:4326")

    logging.info("Récupération du graphe")
    g = osmnx.graph_from_polygon(
        enveloppe_avec_marge[0],
        simplify=False,
        network_type="bike",
        truncate_by_edge=True,
    )

    logging.info("Transformation des places piétonnes en clique")
    # On transforme les place piétonnes en cliques
    o, s, e, n = enveloppe_gdf.bounds.values[0]
    places_en_cliques(g, (s,o,n,e))

    logging.info("Simplification du graphe")
    osmnx.simplify_graph(g)

    logging.info("Ajout du nom des villes sur les sommets")
    # GeoDataFrame des sommets
    nœuds = osmnx.graph_to_gdfs(g, edges=False)

    # On indique la ou les villes de chaque nœud
    for ville, géom in zip(villes, géoms["geometry"]):
        nœuds_de_la_ville = nœuds[nœuds.within(géom)]
        for s in nœuds_de_la_ville.index:
            if "ville" not in g.nodes[s]:
                g.nodes[s]["ville"] = [ville.nom_complet]
            else:
                g.nodes[s]["ville"].append(ville.nom_complet)

    return g
    
#ei1c1722589
def charge_graphe_de_ville(ville_d: Ville, pays="France", bavard=0, rapide=0) -> None:
    """
    Récupère le graphe grâce à osmnx et le charge dans la base.

    Une marge de 500m est prise. En particulier les sommets et arêtes à moins de 500m d’une frontière entre deux villes seront au final associés à ces deux villes.
    """
    ## Récup des graphe via osmnx
    print(f"\nRécupération du graphe pour « {ville_d.code} {ville_d.nom_complet}, {pays} » avec une marge :\n")
    gr_avec_marge = osmnx.graph_from_place(
        {"city": f"{ville_d.nom_complet}", "postcode": ville_d.code, "country": pays},
        network_type="all",  # Tout sauf private
        retain_all=False,  # Sinon il peut y avoir des enclaves déconnectées car accessibles seulement par chemin privé (ex: CSTJF)
        buffer_dist=500,  # Marge de 500m
        truncate_by_edge=True,   # garde les arêtes dont une extrémité est dans la zone.
        simplify=False,          # On simplifiera après places_en_cliques
    )
    print("\n\nRécupération du graphe exact:\n")
    gr_strict = osmnx.graph_from_place(
        {"city": f"{ville_d.nom_complet}", "postcode": ville_d.code, "country": pays},
        network_type="all",
        retain_all=True,
        simplify=False,
    )

    g = Graphe_nx(gr_avec_marge)
    places_en_cliques(g, ville_d.bbox())
    osmnx.simplify_graph(g.multidigraphe)

    ## Noms des villes ajouté dans g
    for n in gr_strict:
        g.villes_of_nœud[n] = [ville_d.nom_complet]

    ## Nœuds des rues
    print("\n\nCalcul des nœuds de chaque rue")
    dico_rues, places_piétonnes = extrait_nœuds_des_rues(g, bavard=bavard-1)  # dico ville -> rue_n -> (rue, liste nœuds) # Seules les rues avec nom de ville, donc dans g_strict seront calculées.
    print(f"\nPlaces piétonnes trouvées : {places_piétonnes}\n")

    close_old_connections()
    print("Suppression des anciennes rues")
    print(Rue.objects.filter(ville=ville_d).delete())
    print("Ajout des nouvelles rues.")
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
    vd.transfert_graphe(g, ville_d, bavard=bavard-1, rapide=rapide)
    



def remplaceArête(g: Graphe_nx, s, t, nom: str):
    """
    Supprime toutes les arêtes entre s et t et entre t et s et les remplace par une ligne droite dans chaque sens, avec le tag « highway: pedestrian »
    """
    d = g.d_euc(s, t)
    gn = g.multidigraphe
    if t in gn[s]:
        for _ in range(len(gn[s][t])):
            gn.remove_edge(s, t)
    if s in gn[t]:
        for _ in range(len(gn[t][s])):
            gn.remove_edge(t, s)
    gn.add_edge(s, t, length=d, name=nom, highway="pedestrian")
    gn.add_edge(t, s, length=d, name=nom, highway="pedestrian")
    


def places_en_cliques(g: Graphe_nx, bbox: tuple[float, float, float, float]):
    """
    Récupère les zones piétonnes de la ville et ajoute les cliques correspondantes au graphe g.
    """

    places = rd.zones_piétonnes(bbox, g)
    
    # Création des nouvelles arêtes
    nb = 0
    for nom, place in places:
        print(f"Mise en clique de {nom}")
        for (s, t) in paires(place):
            nb += 1
            remplaceArête(g, s, t, nom)
    print(f"{nb} arêtes ajoutées")
        
    
    

def ajoute_ville(nom: str, code: int, nom_zone: str, force=False, pays="France", bavard=0):
    """
    Ajoute la ville dans la zone indiquée.
    Paramètres:
        force : si True les données seront rechargées même si données_présentes est vrai.
    """

    zone_d = Zone.objects.get(nom=nom_zone)
    ville_d = ville_of_nom_et_code_postal(nom, code)
    charge_ville(ville_d, zone_d, force=force, pays=pays, bavard=bavard)
    print("Recréation de l’arbre des arêtes")
    quadArbresArêtesDeLaBase()


def charge_ville(ville_d, zone_d,
                 force=False,
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
        - force : si vrai, recharge les données même si le champ données_présentes de ville_d valait True.
        - rapide (int) : indique la stratégie en cas de données déjà présentes.
             pour tout  (s,t) sommets voisins dans g,
                0 -> efface toutes les arêtes de s vers t et remplace par celles de g
                1 -> regarde si les arête entre s et t dans g correspondent à celles dans la base, et dans ce cas ne rien faire.
                        « correspondent » signifie : même nombre et mêmes noms.
                2 -> si il y a quelque chose dans la base pour (s,t), ne rien faire.
        - rajouter_les_lieux : si Vrai,récupère les lieux sur overpass et crée les objets associés.
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
        charge_graphe_de_ville(ville_d, pays=pays, bavard=bavard-1, rapide=rapide)
        modif = True

    ## Lieux
    if rajouter_les_lieux:
        # Si rajouter_les_lieux est faux, c’est que c’est crée_zone qui s’en charge (pour éviter de recalculer l’arbre des arêtes à chaque ville.)
        arbre_a = quadArbreArêtesDeVille(ville_d)
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


ZONE_PAU = {
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
    "Mazères-Lezons": 64110,
}.items()


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
    ("Fontaine", 38600),
    ("Gières", 38610),
]


def ville_of_nom_et_code_postal(nom: str, code: int):
    """
    Renvoie la ville de la base ayant le nom indiqué (après normalisation par partie_commune)
    En cas de non unicité, utilise le code postal pour départager.
    """

    essai1 = Ville.objects.filter(nom_norm=partie_commune(nom))
    if len(essai1) == 1:
        return essai1.first()
    elif len(essai1) == 0:
        raise RuntimeError(f"Ville pas trouvée : {nom}. Avez-vous chargé la liste des villes avec communes.charge_villes() ?")
    else:
        return Ville.objects.get(nom_norm=partie_commune(nom), code=code)



def crée_zone(liste_villes_str, zone: str,
              réinit_données=False,
              réinit_zone=False,
              effacer_cache=False, bavard=2, rapide=0,
              force_lieux=False,
              inclue_dans: str|None = None,
              contient: str|None = None
              ):
    """
    Entrée : liste_villes, itérable de (nom de ville, code postal). La ville par défaut sera la première de cette liste.
             zone (str), nom de la zone

    Effet : charge toutes ces ville dans la base, associées à la zone indiquée.
            Si la zone n’existe pas, elle sera créée.
            ## Si la zone existe, l’ancienne est supprimée. -> Plus le cas !

    Paramètres:
       Si réinit_données, tous les éléments associés à la zone (villes, rues, sommets, arêtes) ainsi que le cache sont au préalable supprimés.
       Si force_lieux, on charge les lieux même pour les villes qui avaient données_présentes à True.
       Si réinit_zone, la zone est effacée puis recréée, ce qui réinitialise les villes contenues et les relation inclue_dans.
       À FAIRE : Si effacer_cache, tous les fichiers .json du dossier cache du répertoire courant seront effacés.
       inclue_dans : nom d’une autre zone, qui sera marquée comme contenant la zone créée.
       contient : nom d’une autre zone, qui sera marquée comme contenue dans la zone crée.


    Sortie (Ville list) : liste des villes pour lesquelles on n’a pas pu récupérer les lieux.
    """
    
    close_old_connections()

    ## Récup des villes :
    liste_villes_d = [ville_of_nom_et_code_postal(*c) for c in liste_villes_str]
    
    ## Récupération ou création de la zone :
    z_d, créée = Zone.objects.get_or_create(nom=zone, ville_défaut=liste_villes_d[0])
    if not créée and réinit_zone:
        z_d.sauv_csv()
        z_d.delete()
        z_d = Zone(nom=zone, ville_défaut=liste_villes_d[0])
        z_d.save()
        z_d.charge_csv()
    # Associer les villes à la zone
    for v in liste_villes_d:
        z_d.ajoute_ville(v)
    # Les relations d’inclusion dans une autre zone
    if inclue_dans:
        z_d.inclue_dans = Zone.objects.get(nom=inclue_dans)
        z_d.save()
    if contient:
        grande_zone = Zone.objects.get(nom=contient)
        grande_zone.inclue_dans = z_d
        grande_zone.save()
        
        
    ## Réinitialisation de la zone :
    if réinit_données:
        for v in liste_villes_d:
            v.données_présentes = False
            v.save()
            print(f"J’ai mis données présentes à False pour {v}.")

            print("Suppression des relations sommet-ville et arête-ville :")
            #supprime_objets_par_lots(list(Sommet.villes.through.objects.filter(ville_id=v.id)))
            rels = Sommet.villes.through.objects.filter(ville_id=v.id)
            print(rels._raw_delete(rels.db))
            #supprime_objets_par_lots(list(Arête.villes.through.objects.filter(ville_id=v.id)))
            rels = Arête.villes.through.objects.filter(ville_id=v.id)
            print(rels._raw_delete(rels.db))
            
            
            sansVille = Sommet.objects.all().alias(nbvilles=Count("villes")).filter(nbvilles=0)
            print(f"Suppression des {len(sansVille)}sommets orphelins :")
            #supprimeQuerySetParLots(sansVille)
            sansVille.delete()
            # Ceci supprime au passage les arêtes liées aux sommets supprimés
            
        Cache_Adresse.objects.all().delete()

    # Vidage du cache d’osmnx ?

    # Graphe total
    graphe_total = graphe_de_villes(liste_villes_d)
    
    ## Chargement des villes :
    villes_modifiées = []
    for v_d in liste_villes_d:
        LOG(f"\nChargement de {v_d}", bavard=bavard)
        _, données_ajoutées = charge_ville(
            v_d, z_d,
            bavard=bavard, rapide=rapide, rajouter_les_lieux=False
        )
        if données_ajoutées or force_lieux:
            villes_modifiées.append(v_d)

    ## Arbre quad des arêtes de la plus grande zone contenant z_d
    arbre_a = créeQuadArbreArêtesDeZone(z_d, bavard=bavard)
    

    ## Lieux (besoin de l’arbre des arêtes)
    LOG("\nChargement des lieux")
    échec_lieux = charge_lieux_of_liste_ville(villes_modifiées, arbre_a, réinit=True)
    if échec_lieux:
        print("Problème sur les villes :")
        pprint(échec_lieux)


    ## Entrainement sur les trajets sauvegardés
    if réinit_données:
        print(f"Entrainement (Pas encore implémenté! Utiliser pour_shell.entraine_tout)")
        

    print("(crée_zone) fini!")


def charge_lieux_of_liste_ville(villes, arbre_a: QuadrArbreArête, réinit=False) -> list:
    """
    Charge les lieux des villes de la liste éponyme.
    Sortie : villes pour lesquelles charge_lieux_of_ville a échoué.
    """
    pb = []
    for v_d in villes:
        try:
            charge_lieux_of_ville(v_d, arbre_a=arbre_a, réinit=réinit)
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

    charge_lieux_of_liste_ville(villes, QuadrArbreArête.of_list_darêtes_d(zone.arêtes(), sauv=False))
    

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
                elif ligne.strip() == "":
                    None
                elif ligne[:2] == "à ":
                    v_d = Ville.objects.get(nom_norm=partie_commune(ligne[2:].strip().replace(":","")))
                    print(f"\n  Ville {v_d}")
                else:
                    nom_n, nom_osm, _ = normalise_rue(g, z_d, ligne.strip(), v_d)
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
