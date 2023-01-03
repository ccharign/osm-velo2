# -*- coding:utf-8 -*-
import time
import datetime
import os
from pprint import pformat

from django.db.transaction import atomic
from django.db import close_old_connections

from dijk.progs_python.params import DONNÉES
from dijk.progs_python.recup_donnees import lieux_of_ville, adresses_of_liste_lieux
from dijk.progs_python.quadrarbres import QuadrArbreArête
from dijk.models import TypeLieu, Lieu, Zone, Ville, Ville_Zone
import dijk.models as mo
from dijk.progs_python.petites_fonctions import morceaux_tableaux
from dijk.progs_python.lecture_adresse.normalisation0 import int_of_code_insee, partie_commune

from params import LOG



def initGroupesTypesLieux(chemin="dijk/données/données_à_charger/groupesTypesLieux.csv"):
    """
    Créer les groupe de types de lieux et les enregistrer dans la base.
    """
    with open(chemin) as entrée:
        for ligne in entrée:
            nom, trucs = ligne.strip().split("|")
            gtl = mo.GroupeTypeLieu(nom=nom)
            gtl.save()
            for categorie in trucs.split(";"):
                nom_categorie, types_à_découper = categorie.split(":")
                for tl in types_à_découper.split(","):
                    tld = mo.TypeLieu.objects.get(catégorie=nom_categorie, nom_osm=tl)
                    gtl.type_lieu.add(tld)
            gtl.save()


def charge_type_lieux(ld):
    """
    ld (liste de dico), contient le résultat d’un récup_amenities
    Effet : remplit la table TypeAmenity avec les nouveaux. Demande interactivement la traduction en français.
    """

    déjà_présente = set(TypeLieu.objects.values_list("nom_osm", "catégorie"))

    for r in ld:
        if (r["type"], r["catégorie"]) in déjà_présente:
            # mise à jour ?
            None
        else:
            tl = TypeLieu(nom_osm=r["type"], catégorie=r["catégorie"])
            nom_traduit = input(f"Traduction de {r['type']} ? C’est pour {r['name']} ({r['catégorie']}). ")
            close_old_connections()
            tl.nom_français = nom_traduit
            déjà_présente.add((r["type"], r["catégorie"]))
            tl.save()
            if not nom_traduit:
                print(f"J’ignorerai à l’avenir le type {r['type']}")

# @atomic
# def charge_lieux(ll, v_d, force=False):
#     """
#     ll (liste de Lieux)
#     v_d (instance de Ville)
#     Effet : charge les lieux de ll qui n’y étaient pas dans la base.
#     params:
#         force: si vrai, remplace celles déjà présentes dans la base.
#     """
#     print("Récupération des lieux déjà présents dans la base\n")
#     déjà_présentes = set(Lieu.objects.all())
#     types_ignorés = set(TypeLieu.objects.filter(nom_français=""))

#     print(f"Traitement des {len(ll)} lieux")

#     for l in ll:
#         if l not in déjà_présentes and l.type_lieu not in types_ignorés:
#             déjà_présentes.add(l)
#             try:
#                 l.save()
#             except Exception as e:
#                 print(l, l.id_osm)
#                 raise(e)

#         elif force and l in déjà_présentes:
#             # Remplacer l’ancienne
#             vieille = Lieu.objects.get(id_osm=l.id_osm)
#             vieille.delete()
#             l.save()


def ajoute_ville_et_rue(ll, taille_paquets=1000, force=False, bavard=0):
    """
    Entrée : ll (Lieu iterable)
    Effet : ajoute les adresses et les villes trouvées sur data.gouv.
    Paramètres :
        force, si True, écrase les données déjà présentes.
        taille_paquets : nb de lieux à envoyer à la fois à data.gouv.
    """

    nb_traités = 0
    nb_problèmes = 0
    for paquet in morceaux_tableaux(ll, taille_paquets):
        print(f"{nb_traités} lieux traités")
        nb_traités += taille_paquets

        
        
        # try:
        #     données = adresses_of_liste_lieux(paquet, bavard=bavard)
        # except:
        #     print(f"Échec pour la récupération du dernier paquet de {len(paquet)} lieux.")
        # à_maj = []
        # for l, d in zip(paquet, données):
        #     if l.adresse and not force:
        #         print(f"Données déjà présentes, je laisse les vieilles.\nAdresse osm :{l.adresse}\n Adresse data.gouv : {d}\n")
        #     else:
        #         try:
        #             l.adresse = (d["result_housenumber"]+" "+d["result_name"]).strip()
        #             l.ville = Ville.objects.get(code_insee=int_of_code_insee(d["result_citycode"]))
        #             à_maj.append(l)
        #         except ValueError:
        #             #print(f"Problème pour {l} : {e}.\n Voici le résultat reçu : \n{pformat(d)}")
        #             try:
        #                 l.adresse = (d["result_housenumber"]+" "+d["result_name"]).strip()
        #                 l.ville = Ville.objects.get(nom_norm=partie_commune(d["result_city"]), code=d["result_postcode"])
        #                 à_maj.append(l)
        #             except Exception as e:
        #                 nb_problèmes += 1
        #                 LOG(f"Problème pour {l}\n  Données reçues : {pformat(d)}\n Erreur : {e}", type_de_log="pb", bavard=2)
        # print(f"La récupération de l’adresse a échoué pour {nb_problèmes} lieux.")
        # print(f"Enregistrement des modifs ({len(à_maj)} lieux).\n)")
        Lieu.objects.bulk_update(à_maj, ["ville", "adresse"])


# def ajoute_ville_et_rue_manquantes(bavard=1):
#     """
#     Essaie de rajouter ville et adresse des lieux dans la base qui n’en ont pas.
#     """
#     close_old_connections()
#     à_traiter = Lieu.objects.filter(ville__isnull=True)
#     LOG(f"{len(à_traiter)} lieux n’ont pas de Ville.")
#     ajoute_ville_et_rue(à_traiter, bavard=bavard-1)
#     à_traiter = Lieu.objects.filter(ville__isnull=True)
#     LOG(f"Maintenant {len(à_traiter)} lieux n’ont pas de Ville.")

    
def charge_lieux_of_ville(v_d, arbre_a=None, bavard=0, force=False):
    """
    Effet :
        Récupère sur osm les amenities, shops, leisure et tourism de la ville, et remplit les tables TypeLieu et Lieu avec.
    Params:
        - force : si True, remplace les lieux déjà présentes.
    """

    LOG(f"Lieux de {v_d}", bavard=1)

    if not arbre_a:
        arbre_a = mo.ArbreArête.racine()
        
    LOG("Récupération des lieux via overpass", bavard=1)
    ll = lieux_of_ville(v_d, arbre_a, bavard=bavard, force=force)

    v_d.lieux_calculés = datetime.date.today()
    v_d.save()

    LOG(f"charge_lieux_of_ville({v_d}) fini !")
    
    

def charge_lieux_of_zone(z_t, force=False):
    """
    Params:
        force, si Vrai force la mise à jour des lieux déjà présents, et des lieux des villes pour lesquelles lieux_calculés est aujourd’hui.
        L’option force=False est pratique pour relancer le calcul sur les villes qui ont échoué à un premier essai.
    """
    close_old_connections()
    z_d = Zone.objects.get(nom=z_t)
    arbre_a = QuadrArbreArête.of_list_darêtes_d(z_d.arêtes())
    for rel in z_d.ville_zone_set.all():
        if force or rel.ville.lieux_calculés < datetime.date.today():
            charge_lieux_of_ville(rel.ville, force=force, arbre_a=arbre_a)
            print("Pause de 10s pour overpass")
            time.sleep(10)
