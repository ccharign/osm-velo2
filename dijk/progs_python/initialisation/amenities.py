# -*- coding:utf-8 -*-
import time
import datetime
from pprint import pformat

from django.db import close_old_connections

from dijk.progs_python.params import DONNÉES
from dijk.progs_python.recup_donnees import lieux_of_ville
from dijk.progs_python.quadrarbres import QuadrArbreArête
from dijk.models import TypeLieu, Lieu, Zone
import dijk.models as mo
from dijk.progs_python.petites_fonctions import morceaux_tableaux


from dijk.progs_python.params import LOG



def initGroupesTypesLieux(chemin="dijk/progs_python/initialisation/données_à_charger/groupesTypesLieux.csv", réinit=True):
    """
    Créer les groupe de types de lieux et les enregistrer dans la base.
    """
    if réinit:
        print("Suppression des anciens groupes de types de lieux")
        print(mo.GroupeTypeLieu.objects.all().delete())
        
    with open(chemin) as entrée:
        for ligne in entrée:
            nom, trucs, féminin = ligne.strip().split("|")
            gtl = mo.GroupeTypeLieu(nom=nom, féminin=féminin)
            gtl.save()
            print(gtl)
            for categorie in trucs.split(";"):
                nom_categorie, types_à_découper = categorie.split(":")
                for tl in types_à_découper.split(","):
                    try:
                        tld = mo.TypeLieu.objects.get(catégorie=nom_categorie, nom_osm=tl)
                        gtl.type_lieu.add(tld)
                    except TypeLieu.DoesNotExists:
                        print(f"Type de lieu non trouvé: {tl}")
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


                
# def ajoute_ville_et_rue(ll, taille_paquets=1000, force=False, bavard=0):
#     """
#     Entrée : ll (Lieu iterable)
#     Effet : ajoute les adresses et les villes trouvées sur data.gouv.
#     Paramètres :
#         force, si True, écrase les données déjà présentes.
#         taille_paquets : nb de lieux à envoyer à la fois à data.gouv.
#     """

#     nb_traités = 0
#     nb_problèmes = 0
#     for paquet in morceaux_tableaux(ll, taille_paquets):
#         print(f"{nb_traités} lieux traités")
#         nb_traités += taille_paquets
#         Lieu.objects.bulk_update(à_maj, ["ville", "adresse"])


    
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
