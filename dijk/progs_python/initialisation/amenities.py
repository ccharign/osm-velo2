# -*- coding:utf-8 -*-
import time
import datetime
from pprint import pformat

from django.db import close_old_connections

from dijk.progs_python.params import DONNÉES
#from dijk.progs_python.recup_donnees import lieux_of_ville
import dijk.progs_python.recup_donnees as rd
from dijk.progs_python.quadrarbres import QuadrArbreArête
from dijk.models import TypeLieu, Zone
import dijk.models as mo


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
                    except TypeLieu.DoesNotExist:
                        print(f"Type de lieu non trouvé: {tl}")
            gtl.save()




def charge_lieux_of_ville(v_d, arbre_a, bavard=0, force=False):
    """
    Effet :
        Récupère sur osm les amenities, shops, leisure et tourism de la ville, et remplit les tables TypeLieu et Lieu avec.
    Params:
        - force : si True, remplace les lieux déjà présentes.
    """

    LOG(f"Lieux de {v_d}", bavard=1)
    LOG("Récupération des lieux via overpass", bavard=1)
    ll = rd.lieux_of_ville(v_d, arbre_a, bavard=bavard, force=force)
    v_d.lieux_calculés = datetime.date.today()
    v_d.save()
    LOG(f"charge_lieux_of_ville({v_d}) fini !")



def charge_lieux_of_zone(z_d: Zone, force=False):
    """
    Params:
        force, si Vrai force la mise à jour des lieux déjà présents, et des lieux des villes pour lesquelles lieux_calculés est aujourd’hui.
        L’option force=False est pratique pour relancer le calcul sur les villes qui ont échoué à un premier essai.
    """
    close_old_connections()
    #z_d = Zone.objects.get(nom=z_t)

    #arbre_a = QuadrArbreArête.of_list_darêtes_d(z_d.arêtes())
    for ville in z_d.villes():
        if force or ville.lieux_calculés < datetime.date.today():
            charge_lieux_of_ville(ville, z_d.arbre_arêtes, force=force)
            print("Pause de 10s pour overpass")
            time.sleep(10)
    TypeLieu.supprimerLesInutiles()
