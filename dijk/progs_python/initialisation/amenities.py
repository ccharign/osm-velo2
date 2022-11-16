# -*- coding:utf-8 -*-
import time
import os
from pprint import pformat

from django.db.transaction import atomic
from django.db import close_old_connections

from dijk.progs_python.params import DONNÉES
from dijk.progs_python.recup_donnees import lieux_of_ville, adresses_of_liste_lieux
from dijk.progs_python.quadrarbres import QuadrArbreArête
from dijk.models import TypeLieu, Lieu, Zone, Ville, Ville_Zone
from dijk.progs_python.petites_fonctions import morceaux_tableaux
from dijk.progs_python.lecture_adresse.normalisation0 import int_of_code_insee, partie_commune

from params import LOG


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
    for i, l in enumerate(ll):
        try:
            l.pk
        except Exception as e:
            print(f"{l} n’a pas de pk.\n{e}. C’était le lieu d’indice {i}.\n")
            raise e
    nb_traités = 0
    nb_problèmes = 0
    for paquet in morceaux_tableaux(ll, taille_paquets):
        print(f"{nb_traités} lieux traités")
        nb_traités += taille_paquets
        try:
            données = adresses_of_liste_lieux(paquet, bavard=bavard)
        except:
            print(f"Échec pour la récupération du dernier paquet de {len(paquet)} lieux.")
        à_maj = []
        for l, d in zip(paquet, données):
            if l.adresse and not force:
                print(f"Données déjà présentes, je laisse les vieilles.\nAdresse osm :{l.adresse}\n Adresse data.gouv : {d}\n")
            else:
                try:
                    l.adresse = (d["result_housenumber"]+" "+d["result_name"]).strip()
                    l.ville = Ville.objects.get(code_insee=int_of_code_insee(d["result_citycode"]))
                    à_maj.append(l)
                except ValueError:
                    #print(f"Problème pour {l} : {e}.\n Voici le résultat reçu : \n{pformat(d)}")
                    try:
                        l.adresse = (d["result_housenumber"]+" "+d["result_name"]).strip()
                        l.ville = Ville.objects.get(nom_norm=partie_commune(d["result_city"]), code=d["result_postcode"])
                        à_maj.append(l)
                    except Exception as e:
                        nb_problèmes += 1
                        LOG(f"Problème pour {l}\n  Données reçues : {pformat(d)}\n Erreur : {e}", type_de_log="pb", bavard=2)
        print(f"La récupération de l’adresse a échoué pour {nb_problèmes} lieux.")
        print(f"Enregistrement des modifs ({len(à_maj)} lieux).\n)")
        Lieu.objects.bulk_update(à_maj, ["ville", "adresse"])


def ajoute_ville_et_rue_manquantes(bavard=1):
    """
    Essaie de rajouter ville et adresse des lieux dans la base qui n’en ont pas.
    """
    close_old_connections()
    à_traiter = Lieu.objects.filter(ville__isnull=True)
    LOG(f"{len(à_traiter)} lieux n’ont pas de Ville.")
    ajoute_ville_et_rue(à_traiter, bavard=bavard-1)
    à_traiter = Lieu.objects.filter(ville__isnull=True)
    LOG(f"Maintenant {len(à_traiter)} lieux n’ont pas de Ville.")

    
def charge_lieux_of_ville(v_d, arbre_a=None, bavard=0, force=False):
    """
    Effet :
        Récupère sur osm les amenities, shops, leisure et tourism de la ville, et remplit les tables TypeLieu et Lieu avec.
    Params:
        - force : si True, remplace les lieux déjà présentes.
    """

    LOG(f"Lieux de {v_d}", bavard=1)

    # 1) Récup ou création des Lieux
    LOG("Récupération des lieux via overpass", bavard=1)
    ll = lieux_of_ville(v_d, bavard=bavard, force=force)

    # POur débug
    #Lieu.objects.bulk_update(ll, ["nom"])
    
    # 2) Ajout de villes
    LOG(f"Récupération des noms de ville et des adresses via data.gouv pour les {len(ll)} lieux obtenus", bavard=1)
    ajoute_ville_et_rue(ll, bavard=bavard-1)

    
    # 3) Ajout de l’arête la plus proche
    lieux_de_la_bonne_ville = Lieu.objects.filter(ville=v_d)
    
    LOG("Calcul des arêtes les plus proches de chaque Lieu.", bavard=bavard)
    if not arbre_a:
        try:
            z_d = Ville_Zone.objects.filter(ville=v_d).first().zone
            dossier_données = os.path.join(DONNÉES, str(z_d))
            chemin = os.path.join(dossier_données, f"arbre_arêtes_{z_d}")
            arbre_a = QuadrArbreArête.of_fichier(chemin)
        except Exception as e:
            print(f"Erreur dans la récupération de l’arbre des arêtes : {e}")
            arbre_a = QuadrArbreArête.of_ville(v_d)
        
    for l in lieux_de_la_bonne_ville:
        l.ajoute_arête_la_plus_proche(arbre_a)
    LOG("Enregistrement des arêtes les plus proches", bavard=1)
    Lieu.objects.bulk_update(lieux_de_la_bonne_ville, ["arête"])

    LOG(f"charge_lieux_of_ville({v_d}) fini !")
    
    

def charge_lieux_of_zone(z_t, force=False):
    z_d = Zone.objects.get(nom=z_t)
    for rel in z_d.ville_zone_set.all():
        charge_lieux_of_ville(rel.ville, force=force)
        print("Pause de 10s pour overpass")
        time.sleep(10)
