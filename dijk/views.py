# -*- coding:utf-8 -*-

import time
tic0 = time.perf_counter()
from glob import glob
import os
import traceback
import json
import re
from pprint import pprint

from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Subquery, Q

from dijk import forms

from .progs_python.params import LOG
from .progs_python.petites_fonctions import chrono, bbox_autour

from .progs_python.chemins import Chemin, ÉtapeArête

from .progs_python.lecture_adresse.recup_noeuds import PasTrouvé
from .progs_python.lecture_adresse.normalisation0 import prétraitement_rue
from .progs_python import recup_donnees
from .progs_python.apprentissage import n_lectures
from .progs_python.bib_vues import bool_of_checkbox, énumération_texte, récup_head_body_script, récup_données, z_é_i_d

from .progs_python.utils import dessine_cycla, itinéraire_of_étapes

from .progs_python.graphe_par_django import Graphe_django
from .progs_python.lecture_adresse.normalisation0 import découpe_adresse

from .models import Chemin_d, Zone, Rue, Ville_Zone, Cache_Adresse, CacheNomRue, Lieu, Ville

chrono(tic0, "Chargement total\n\n", bavard=3)


g = Graphe_django()





# https://stackoverflow.com/questions/18176602/how-to-get-the-name-of-an-exception-that-was-caught-in-python
def get_full_class_name(obj):
    module = obj.__class__.__module__
    if module is None or module == str.__class__.__module__:
        return obj.__class__.__name__
    return module + '.' + obj.__class__.__name__




def choix_zone(requête):
    """
    Page d’entrée du site. Formulaire de choix de zone.
    """
    if requête.method == "GET" and requête.GET:
        form = forms.ChoixZone(requête.GET)
        if form.is_valid():
            z_d = form.cleaned_data["zone"]
            return recherche(requête, z_d.nom)
    form = forms.ChoixZone()
    return render(requête, "dijk/index.html", {"form": form})


def fouine(requête):
    requête.session["fouine"] = True
    return choix_zone(requête)


def limitations(requête):
    return render(requête, "dijk/limitations.html", {})


def mode_demploi(requête):
    return render(requête, "dijk/mode_demploi.html", {})


def contribution(requête):
    return render(requête, "dijk/contribution.html", {})


def sous_le_capot(requête):
    return render(requête, "dijk/sous_le_capot.html", {})


# def visualisation_nv_chemin(requête):
#     return render(requête, "dijk/iti_folium.html", {})






### Formulaires de recherche d’itinéraire


def recherche(requête, zone_t):
    """
    Vue pour une recherche de base.
    """
    # données = dict_of_get(requête.GET)
    # form_zone = forms.ChoixZone(requête.GET)
    # if not form_zone.is_valid():
    #     print(form_zone.errors)
    # données.update(form_zone.cleaned_data)
    données = récup_données(requête.GET, forms.ChoixZone, validation_obligatoire=False)
    if "zone" in données and données["zone"]:
        z_d = g.charge_zone(données["zone"].nom)
        requête.session["zone"] = z_d.nom
        requête.session["zone_id"] = z_d.pk
    elif "zone" in requête.session:
        z_d = g.charge_zone(requête.session["zone"])
        données["zone"] = z_d
    else:
        return choix_zone(requête)
    
    if requête.GET and "arrivée" in requête.GET:
        form_recherche = forms.Recherche(données)
        if form_recherche.is_valid():
            données.update(form_recherche.cleaned_data)
            z_d, étapes, étapes_interdites, ps_détour = z_é_i_d(g, données)

            return calcul_itinéraires(requête, ps_détour, z_d,
                                      étapes,
                                      étapes_interdites=étapes_interdites,
                                      données=données,
                                      bavard=1
                                      )
        else:
            # form pas valide
            print(form_recherche.errors)
    else:
        form_recherche = forms.Recherche(initial=données)
    return render(requête, "dijk/recherche.html",
                  {"ville": z_d.ville_défaut, "zone_t": zone_t, "recherche": form_recherche}
                  )



def relance_rapide(requête):
    """
    Relance un calcul à partir du résultat du formulaire de relance rapide.
    Les étapes sont dans des champs dont le nom contient 'étape_coord', sous la forme 'lon;lat'
    Les arêtes interdites sont dans des champs dont le nom contient 'interdite_coord', sous la même forme.
    """

    données = récup_données(requête.GET, forms.RelanceRapide)
    z_d, étapes, étapes_interdites, ps_détour = z_é_i_d(g, données)
    
    
    départ = étapes[0]
    arrivée = étapes[-1]

    é_inter = []
    é_interdites = []
    
    for c, v in requête.GET.items():
        if "étape_coord" in c:
            num = int(re.match("étape_coord([0-9]*)", c).groups()[0])
            print(num)
            coords = tuple(map(float, v.split(",")))
            a, _ = g.arête_la_plus_proche(coords, z_d)
            é_inter.append((num, ÉtapeArête.of_arête(a, coords)))
            
        elif "interdite_coord" in c:
            coords = tuple(map(float, v.split(",")))
            a, _ = g.arête_la_plus_proche(coords, z_d)
            é_interdites.append(ÉtapeArête.of_arête(a, coords))
    LOG(f"(views.relance_rapide) étapes_interdites : {étapes_interdites}")
    é_inter.sort()
    étapes = [départ] + [é for _, é in é_inter] + [arrivée]
    return calcul_itinéraires(requête, ps_détour, z_d,
                              étapes, étapes_interdites=é_interdites,
                              données=données,
                              bavard=3)




def chaîne_avec_points_virgule_renversée(c: str):
    """
    c contient des point-virgules
    Sortie : la même en inversant l’ordre des morceaux séparés par les points-virgules.
    """
    return ";".join(
        reversed(
            c.split(";")
        )
    )

def trajet_retour(requête):
    """
    Renvoie le résultat pour le trajet retour de celui reçu dans la requête.
    """

    données = récup_données(requête.GET, forms.ToutCaché)
    z_d, étapes, étapes_interdites, ps_détour = z_é_i_d(g, données)
    
    #  Échange départ-arrivée dans le dico de données
    données["départ"], données["arrivée"] = données["arrivée"], données["départ"]
    données["coords_départ"], données["coords_arrivée"] = données["coords_arrivée"], données["coords_départ"]

    #  Étapes à l’envers
    étapes.reverse()
    données["marqueurs_é"] = chaîne_avec_points_virgule_renversée(données["marqueurs_é"])

    return calcul_itinéraires(requête, ps_détour, z_d,
                              étapes,
                              étapes_interdites=étapes_interdites,
                              données=données
                              )




### Fonction principale


def calcul_itinéraires(requête, ps_détour, z_d, étapes, étapes_interdites=[], données={}, bavard=0):
    """
    Entrées : ps_détour (float list ou str)
              z_d (models.Zone)
              noms_étapes (str list)
              rues_interdites (str list), noms des rues interdites.
              étapes (chemin.Étape list or None), si présent sera utilisé au lieu de noms_étapes. Doit contenir aussi départ et arrivée. Et dans ce cas, interdites sera utilisé au lieu de rues_interdites.
              interdites (chemin.Étape list or None), ne passer par aucune arête inclue dans une de ces étapes.
              données : données du formulaire précédent : sera utilisé pour préremplir les formulaires de relance de recherche et d’enregistrement.
    """
    
    if isinstance(ps_détour, str):
        ps_détour = list(map( lambda x: float(x)/100, requête.GET["pourcentage_détour"].split(";")) )
        
    try:
        #stats, chemin, noms_étapes, rues_interdites, carte = itinéraire_of_étapes(
        données.update(itinéraire_of_étapes(
            étapes, ps_détour, g, z_d, requête.session,
            rajouter_iti_direct=len(étapes) > 2,
            étapes_interdites=étapes_interdites,
            bavard=1,
            où_enregistrer="dijk/templates/dijk/iti_folium.html"
        ))
        noms_étapes = données["noms_étapes"]
        rues_interdites = données["rues_interdites"]
        
        
        ## Création du gabarit

        # suffixe = "".join(noms_étapes) + "texte_étapes" + "".join(rues_interdites)

        # vieux_fichier = glob("dijk/templates/dijk/résultat_itinéraire_complet**")
        # for f in vieux_fichier:
        #     os.remove(f)
        # head, body, script = récup_head_body_script("dijk/templates/dijk/iti_folium.html")

        # nom_fichier_html = f"dijk/résultat_itinéraire_complet{suffixe}"
        # if len(nom_fichier_html) > 230:
        #     nom_fichier_html = nom_fichier_html[:230]
        # nom_fichier_html += ".html"

        # with open(os.path.join("dijk/templates", nom_fichier_html), "w") as sortie:
        #     sortie.write(f"""
        #     {{% extends "dijk/résultat_itinéraire_sans_carte.html" %}}
        #     {{% block head_début %}}
        #     {head}
        #     {{% load static %}}
        #     <script src="{{% static 'dijk/leaflet-providers.js' %}}" type="text/javascript" > </script>
        #     {{% endblock %}}
        #     {{% block carte %}} {body} {{% endblock %}}
        #     {{% block script %}} <script> {script} </script> {{% endblock %}}
        #     """)

            
        ## Chargement du gabarit

        def texte_marqueurs(l_é, supprime_début_et_fin=False):
            """
            Entrée : liste d’étapes
            Sortie (str) : coords des étapes de type ÉtapeArête séparées par des ;. La première et la dernière étape sont supprimées (départ et arrivée).
            """
            if supprime_début_et_fin:
                à_voir = l_é[1:-1]
            else:
                à_voir = l_é
            return ";".join(map(
                lambda c: f"{c[0]},{c[1]}",
                [é.coords_ini for é in à_voir if isinstance(é, ÉtapeArête)]
            ))

        # Ce dico sera envoyé au gabarit sous le nom de 'post_préc'
        données.update({"étapes": ";".join(noms_étapes[1:-1]),
                        "rues_interdites": ";".join(rues_interdites),
                        "pourcentage_détour": ";".join(map(lambda p: str(int(p*100)), ps_détour)),
                        "départ": étapes[0].adresse,
                        "arrivée": étapes[-1].adresse,
                        "zone_t": z_d.nom,
                        "marqueurs_i": texte_marqueurs(étapes_interdites),  # Sera mis en hidden dans le formulaire relance_rapide
                        "marqueurs_é": texte_marqueurs(étapes, supprime_début_et_fin=True),  # idem
                        })
        LOG(f"(views.calcul_itinéraires) marqueurs_i : {données['marqueurs_i']}")
        texte_étapes_inter = énumération_texte(noms_étapes[1:-1])

        coords_départ = g.coords_of_id_osm(données["itinéraires"][-1].liste_sommets[0])  # coords du début de l’iti avec le plus grand p_détour 
        coords_arrivée = g.coords_of_id_osm(données["itinéraires"][-1].liste_sommets[-1])
        marqueurs_à_rajouter = [
            étapes[0].marqueur_leaflet(coords_départ),
            étapes[-1].marqueur_leaflet(coords_arrivée)
        ]
        
        return render(requête,
                      #nom_fichier_html,
                      "dijk/résultat_itinéraire_sans_carte.html",
                      {**données,
                       **{
                           "texte_étapes_inter": texte_étapes_inter,
                           "rues_interdites": énumération_texte(rues_interdites),
                           #"chemin": chemin.str_joli(),
                           "post_préc": données,
                           "relance_rapide": forms.RelanceRapide(initial=données),
                           "enregistrer_contrib": forms.EnregistrerContrib(initial=données),
                           "trajet_retour": forms.ToutCaché(initial=données),
                           "fouine": requête.session.get("fouine", None),
                           "js_itinéraires": [iti.vers_leaflet() for iti in données["itinéraires"]] + marqueurs_à_rajouter
                           #"la_carte": carte.get_name()
                         }
                       }
                      )

    # Renvoi sur la page d’erreur
    except (PasTrouvé, recup_donnees.LieuPasTrouvé) as e:
        return vueLieuPasTrouvé(requête, e)
    except Exception as e:
        traceback.print_exc()
        return autreErreur(requête, e)







### Ajout d’un nouvel itinéraire ###


def confirme_nv_chemin(requête):
    """
    Traitement du formulaire d’enregistrement d’un nouveau chemin.
    """
    try:

        données = récup_données(requête.POST, forms.ToutCaché)
        z_d, étapes, étapes_interdites, _ = z_é_i_d(g, données)

        nb_lectures = 50

        #noms_étapes = [é for é in requête.POST["étapes"].strip().split(";") if len(é)>0]
        AR = bool_of_checkbox(requête.POST, "AR")
        #rues_interdites = [r for r in requête.POST["rues_interdites"].strip().split(";") if len(r)>0]

        chemins = []
        for id_chemin in requête.POST.keys():
            if id_chemin[:2] == "ps" and requête.POST[id_chemin] == "on":
                pourcentage_détour = int(id_chemin[2:])
                c = Chemin.of_étapes(z_d, étapes, pourcentage_détour, AR, g, étapes_interdites=étapes_interdites, nv_cache=2, bavard=2)
                chemins.append(c)
                for é in c.étapes:
                    print(é.nœuds)
                c_d = c.vers_django(bavard=1)
                
                prop_modif = n_lectures(nb_lectures, g, [c], bavard=1)
                c_d.dernier_p_modif = prop_modif
                c_d.save()

        return render(requête, "dijk/merci.html", {"chemin": chemins, "zone_t": z_d.nom})
    
    except Exception as e:
        traceback.print_exc()
        return autreErreur(requête, e)


### traces gpx ###

def téléchargement(requête):
    """
    Fournit le .gpx, contenu dans requête.POST["gpx"]
    """
    try:
        return HttpResponse(
            requête.POST["gpx"].replace("%20", " ").replace("ν", "\n"),
            headers={
                'Content-Type': "application/gpx+xml",
                'Content-Disposition': 'attachment; filename="trajet.gpx"'
            }
        )
    except Exception as e:
        return autreErreur(requête, e)


### Carte cycla ###


def choix_cycla(requête):
    if requête.method == "GET" and requête.GET:
        # On est arrivé ici après remplissage du formulaire
        form = forms.CarteCycla(requête.GET)
        if form.is_valid():
            données=form.cleaned_data
            return carte_cycla(requête, données)
    else:
        # Formulaire pas encore rempli (premier appel)
        form = forms.CarteCycla()
    return render(requête, "dijk/cycla_choix.html", {"form": form})


def carte_cycla(requête, données):
    """
    Renvoie la carte de la cyclabilité de la zone indiquée.
    """
    z_d = données["zone"]
    nom = f"dijk/cycla{z_d}.html"
    print(nom)
    if not os.path.exists("dijk/templates/"+nom) or données["force_calcul"]:
        if z_d.nom not in g.zones: g.charge_zone(z_d.nom)
    
        dessine_cycla(g, z_d, où_enregistrer="dijk/templates/"+nom, bavard=1)
    return render(requête, nom)



### Gestion des chemins (admin) ###

def affiche_chemins(requête):
    cs = Chemin_d.objects.all()
    n_cs = len(cs)
    print(f"Nombre de chemins : {len(cs)}")
    return render(requête, "dijk/affiche_chemins.html", {"chemins": cs, "nb_chemins": n_cs})


def action_chemin(requête):
    
    if requête.POST["action"] == "voir":
        c = Chemin_d.objects.get(id=requête.POST["id_chemin"])
        g.charge_zone(c.zone.nom)
        étapes = c.étapes()
        d = étapes[0]
        a = étapes[-1]
        return calcul_itinéraires(
            requête, d, a,
            [c.p_détour],
            c.zone,
            étapes[1:-1],
            c.rues_interdites()
        )

    elif requête.POST["action"] == "effacer":
        c = Chemin_d.objects.get(id=requête.POST["id_chemin"])
        c.delete()
        return affiche_chemins(requête)


### Erreurs ###

def vueLieuPasTrouvé(requête, e):
    """
    Renvoie une page d’erreur de type « Lieu pas trouvé»
    """
    return render(requête, "dijk/LieuPasTrouvé.html", {"msg": f"{e}"})


def autreErreur(requête, e):
    """
    Renvoie une page d’erreur générique.
    """
    return render(requête, "dijk/autreErreur.html", {"msg": f"{e.__class__.__name__} : {e}"})




### Auto complétion ###


def pour_complétion(requête, nbMax=15):
    """
    Renvoie la réponse nécessitée par autocomplete.
    Laisse tel quel la partie avant le dernier ;
    Découpe l’adresse en (num? bis_ter? rue(, ville)?), et cherche des complétions pour rue et ville.
    nbMax : nb max de résultat. S’il y en a plus, aucun n’est renvoyé.
    """

    class Résultat():
        """
        Pour enregistrer le résultat à renvoyer.
        Un nouvel élément d n’est ajouté que si self.f_hach(d) n’est pas déjà présent et si le nb de résultats est < self.n_max
        """
        def __init__(self, f_hach, n_max):
            self.res = []
            self.f_hach = f_hach
            self.n_max = n_max
            self.déjà_présent = set()
            self.nb = 0
            self.trop_de_rés = False

        def __len__(self):
            return self.nb

        def ajoute(self, d):
            if self.nb < self.n_max:
                if self.f_hach(d) not in self.déjà_présent:
                    self.déjà_présent.add(self.f_hach(d))
                    self.res.append(d)
                    self.nb += 1
            else:
                self.trop_de_rés = True

        def vers_json(self):
            if self.trop_de_rés:
                return "fail"
            else:
                return json.dumps(self.res)
            

    
    mimeType = "application/json"
    if "term" in requête.GET:

        # id de la zone
        if "zone_id" not in requête.session:
            z_d = Zone.objects.get(nom=requête.session["zone"])
            requête.session["zone_id"] = z_d.pk
            z_id = z_d.pk
        else:
            z_id = requête.session["zone_id"]
            z_d = Zone.objects.get(pk=z_id)
        

        # Découpage de la chaîne à chercher
        tout = requête.GET["term"].split(";")
        à_chercher = prétraitement_rue(tout[-1])
        num, bis_ter, rue, déb_ville = découpe_adresse(à_chercher)
        print(f"Recherche de {rue}")
        début = " ".join(x for x in [num, bis_ter] if x)
        if début: début += " "
        
        def chaîne_à_renvoyer(adresse, ville=None, parenthèse=None):
            res = ";".join(tout[:-1] + [début+adresse])
            if parenthèse:
                res += f" ({parenthèse})"
            if ville: res += ", " + ville
            return res

        # Villes de la zone z_id
        villes = Ville_Zone.objects.filter(zone=z_id, ville__nom_norm__icontains=déb_ville)
        print(f"villes : {[Ville.objects.get(pk=v) for v, in villes.values_list('ville')]}. Zone : {z_d}.")
        req_villes = Subquery(villes.values("ville"))

        
        res = Résultat(lambda d: d["label"], nbMax)

        # Complétion dans l’arbre lexicographique (pour les fautes de frappe...)
        # Fonctionne sauf qu’on ne récupère pas la ville pour l’instant
        # dans_l_arbre = g.arbre_lex_zone[z_d].complétion(à_chercher, tol=2, n_max_rés=nbMax)
        # print(dans_l_arbre)

        
        # Recherche dans les lieux
        lieux = Lieu.objects.filter(nom__icontains=rue, ville__in=req_villes).prefetch_related("ville", "type_lieu")
        print(f"{len(lieux)} lieux trouvées")
        for l in lieux:
            res.ajoute({"label": l.str_pour_formulaire(), "lon": l.lon, "lat": l.lat})
        
        
        # Recherche dans les rues de la base
        dans_la_base = Rue.objects.filter(nom_norm__icontains=rue, ville__in=req_villes).prefetch_related("ville")
        for rue_trouvée in dans_la_base:
            res.ajoute({"label": chaîne_à_renvoyer(rue_trouvée.nom_complet, rue_trouvée.ville.nom_complet)})

        
        
        # Recherche dans les caches
        for truc in Cache_Adresse.objects.filter(adresse__icontains=rue, ville__in=req_villes).prefetch_related("ville"):
            print(f"Trouvé dans Cache_Adresse : {truc}")
            chaîne = chaîne_à_renvoyer(truc.adresse, truc.ville.nom_complet)
            res.ajoute({"label": chaîne})
            
        for chose in CacheNomRue.objects.filter(Q(nom__icontains=rue) | Q(nom_osm__icontains=rue), ville__in=req_villes).prefetch_related("ville"):
            print(f"Trouvé dans CacheNomRue : {chose}")
            chaîne = chaîne_à_renvoyer(chose.nom_osm, chose.ville.nom_complet)
            res.ajoute({"label": chaîne_à_renvoyer(chose.nom_osm, chose.ville.nom_complet)})

        return HttpResponse(res.vers_json(), mimeType)
        
    else:
        return HttpResponse("fail", mimeType)

        
    


### Stats ###

def recherche_pourcentages(requête):
    return render(requête, "dijk/recherche_pourcentages.html")

def vue_pourcentages_piétons_pistes_cyclables(requête, ville=None):
    """
    Renvoie un tableau avec les pourcentages de voies piétonnes et de pistes cyclables pour les villes dans requête.POSTE["villes"]. Lequel est un str contenant les villes séparées par des virgules.
    """
    from dijk.progs_python.stats import pourcentage_piéton_et_pistes_cyclables
    if ville:
        villes = [ville]
    else:
        villes = requête.POST["villes"].split(";")
    res = []
    for v in villes:
        res.append((v,) + pourcentage_piéton_et_pistes_cyclables(v))
    return render(requête, "dijk/pourcentages.html", {"stats": res})



### Rapport de bug ###

def rapport_de_bug(requête):
    """
    Pour rentrer un rapport de bug.
    """
    if requête.POST:
        form = forms.RapportDeBug(requête.POST)
        form.save()
        return render(requête, "dijk/message.html", {"message": "C’est enregistré, merci !"})
    else:
        form = forms.RapportDeBug()
        return render(requête, "dijk/rapport_de_bug.html", {"form": form})


### Autour de moi ###

def autourDeMoi(requête):
    """
    Affiche la carte autour de l’utilisateur, ainsi qu’un formulaire pour recherche de lieux.
    """
    if requête.GET:
        données = récup_données(requête.GET, forms.AutourDeMoi, validation_obligatoire=False)
        lon, lat = map(float, données["localisation"].split(","))
        bbox = tuple(map(float, données["bbox"].split(",")))
        print(f"bbox : {bbox}")

        print("Types de lieux à chercher :")
        for tl in données["type_lieu"]:
            print(f"    {tl}")
            
        lieux = recup_donnees.lieux_of_types_lieux(bbox, données["type_lieu"].all(), bavard=3)
        
        LOG(f"{len(lieux)} lieux trouvés", bavard=1)
        données["marqueurs"] = [l.marqueur_leaflet("laCarte") for l in lieux]
        pprint(données["marqueurs"])
        return render(requête, "dijk/autourDeMoi.html", données)
    else:
        form = forms.AutourDeMoi()
        return render(requête, "dijk/autourDeMoi.html", {"form": form})
