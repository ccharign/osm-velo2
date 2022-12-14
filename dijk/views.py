# -*- coding:utf-8 -*-

import time
import re
import os
import traceback
import json
from pprint import pprint

from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Subquery, Q

from dijk import forms

from .progs_python.params import LOG
from .progs_python.petites_fonctions import chrono

from .progs_python.chemins import Chemin, ÉtapeArête

from .progs_python.lecture_adresse.recup_noeuds import PasTrouvé
from .progs_python.lecture_adresse.normalisation0 import prétraitement_rue
from .progs_python import recup_donnees
from .progs_python.apprentissage import n_lectures
from .progs_python.bib_vues import bool_of_checkbox, énumération_texte, récup_données, z_é_i_d, chaîne_avec_points_virgule_renversée

from .progs_python.utils import dessine_cycla, itinéraire_of_étapes

from .progs_python.graphe_par_django import Graphe_django
from .progs_python.lecture_adresse.normalisation0 import découpe_adresse

from .models import Chemin_d, Zone, Rue, Ville_Zone, Cache_Adresse, CacheNomRue, Lieu, Ville, GroupeTypeLieu







g = Graphe_django()




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







### Formulaires de recherche d’itinéraire


def recherche(requête, zone_t, bavard=1):
    """
    Vue pour une recherche de base.
    """
    
    données = récup_données(requête.GET, forms.ChoixZone, validation_obligatoire=False)
    if "zone" in données and données["zone"]:
        z_d = g.charge_zone(données["zone"].nom)  # Charge la zone si besoin
        requête.session["zone"] = z_d.nom
        requête.session["zone_id"] = z_d.pk
    elif "zone" in requête.session:
        z_d = g.charge_zone(requête.session["zone"])  # Charge la zone si besoin
        données["zone"] = z_d
    else:
        # Si pas de zone dispo, renvoie à la page de choix de la zone.
        return choix_zone(requête)
    
    if requête.GET and "arrivée" in requête.GET:
        form_recherche = forms.Recherche(données)
        if form_recherche.is_valid():
            # Formulaire rempli et valide
            données.update(form_recherche.cleaned_data)
            LOG(f"(views.recherche) départ (données) : {données['départ']}", bavard=bavard)
            
            z_d, étapes, étapes_interdites, étapes_sommets, ps_détour = z_é_i_d(g, données)
            # données a éventuellement été complété avec des coords de l’adresse
            

            return calcul_itinéraires(requête, ps_détour, z_d,
                                      étapes,
                                      étapes_sommets,
                                      étapes_interdites=étapes_interdites,
                                      données=données,
                                      bavard=1
                                      )
        else:
            # Form pas valide
            print(form_recherche.errors)
    else:
        # Form pas rempli
        form_recherche = forms.Recherche(initial=données)
    return render(requête, "dijk/recherche.html",
                  {"ville": z_d.ville_défaut, "zone_t": zone_t, "recherche": form_recherche}
                  )



def relance_rapide(requête):
    """
    Relance un calcul à partir du résultat du formulaire de relance rapide.
    Les étapes sont dans des champs dont le nom contient 'étape_coord', sous la forme 'lon;lat'
    Les arêtes interdites sont dans des champs dont le nom contient 'interdite_coord', sous la même forme.
    Le champ « étapes » du formulaire n’est pas utilisé ! Seulement les étapes venant d’un clic sur la carte.
    """

    données = récup_données(requête.GET, forms.RelanceRapide)
    z_d, étapes, étapes_interdites, étapes_sommets, ps_détour = z_é_i_d(g, données)
    
    return calcul_itinéraires(requête, ps_détour, z_d,
                              étapes, étapes_sommets, étapes_interdites=étapes_interdites,
                              données=données,
                              bavard=3)




def trajet_retour(requête):
    """
    Renvoie le résultat pour le trajet retour de celui reçu dans la requête.
    """

    données = récup_données(requête.GET, forms.ToutCaché)
    z_d, étapes, étapes_interdites, étapes_sommets, ps_détour = z_é_i_d(g, données)
    
    #  Échange départ-arrivée dans le dico de données
    données["départ"], données["arrivée"] = données["arrivée"], données["départ"]
    données["données_cachées_départ"], données["données_cachées_arrivée"] = données["données_cachées_arrivée"], données["données_cachées_départ"]

    #  Étapes à l’envers
    étapes.reverse()
    données["marqueurs_é"] = chaîne_avec_points_virgule_renversée(données["marqueurs_é"])

    return calcul_itinéraires(requête, ps_détour, z_d,
                              étapes,
                              étapes_sommets,
                              étapes_interdites=étapes_interdites,
                              données=données
                              )




### Fonction principale


def calcul_itinéraires(requête, ps_détour, z_d, étapes, étapes_sommets, étapes_interdites=[], données={}, bavard=0):
    """
    Entrées : ps_détour (float list ou str)
              z_d (models.Zone)
              étapes (chemin.Étape list or None), si présent sera utilisé au lieu de noms_étapes. Doit contenir aussi départ et arrivée. Et dans ce cas, interdites sera utilisé au lieu de rues_interdites.
              étapes_interdites (chemin.Étape list or None), ne passer par aucune arête inclue dans une de ces étapes.
              données : données du formulaire précédent. Sera utilisé pour préremplir les formulaires de relance de recherche et d’enregistrement.
    """

    assert isinstance(étapes_sommets, list)
    
    if isinstance(ps_détour, str):
        ps_détour = list(map(
            lambda x: float(x)/100,
            requête.GET["pourcentage_détour"].split(";")
        ))
        
    try:

        données.update(itinéraire_of_étapes(
            étapes, étapes_sommets, ps_détour, g, z_d,
            rajouter_iti_direct=len(étapes) > 2,
            étapes_interdites=étapes_interdites,
            bavard=bavard
        ))
        noms_étapes = données["noms_étapes"]
        rues_interdites = données["rues_interdites"]
        


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
                        "départ": str(étapes[0]),
                        "arrivée": str(étapes[-1]),
                        "zone_t": z_d.nom,
                        "marqueurs_i": texte_marqueurs(étapes_interdites),  # Sera mis en hidden dans le formulaire relance_rapide
                        "marqueurs_é": texte_marqueurs(étapes, supprime_début_et_fin=True),  # idem
                        })

        texte_étapes_inter = énumération_texte(noms_étapes[1:-1])

        # données à sérialiser pour envoyer à js
        pour_js = {
            "bbox": données["bbox"],
            "itis": [iti.vers_js() for iti in données["itinéraires"]]
        }
        
        return render(requête,
                      "dijk/résultat_itinéraire_sans_carte.html",
                      {**données,
                       **{
                           "texte_étapes_inter": texte_étapes_inter,
                           "rues_interdites": énumération_texte(rues_interdites),
                           "post_préc": données,
                           "relance_rapide": forms.ToutCaché(initial=données),
                           "enregistrer_contrib": forms.EnregistrerContrib(initial=données),
                           "trajet_retour": forms.ToutCaché(initial=données),
                           "fouine": requête.session.get("fouine", None),
                           # "js_itinéraires": [iti.vers_leaflet() for iti in données["itinéraires"]],
                           "données": json.dumps(pour_js)
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
    nb_lectures = 30

    try:
        données = récup_données(requête.POST, forms.EnregistrerContrib)
        z_d, étapes, étapes_interdites, étapes_sommets, _ = z_é_i_d(g, données)
        if étapes_sommets:
            raise RuntimeError("Ne pas enregistrer avec des étapes « passer par »")
        AR = bool_of_checkbox(requête.POST, "AR")
        
        def traite_un_chemin(pourcentage_détour: int):
            c = Chemin.of_étapes(z_d, étapes, pourcentage_détour, AR, g, étapes_interdites=étapes_interdites, nv_cache=2, bavard=2)
            chemins.append(c)
            c_d = c.vers_django(bavard=1)
            prop_modif = n_lectures(nb_lectures, g, [c], bavard=1)
            c_d.dernier_p_modif = prop_modif
            c_d.save()

        chemins = []
        for id_chemin in requête.POST.keys():
            if id_chemin[:2] == "ps" and requête.POST[id_chemin] == "on":
                pourcentage_détour = int(id_chemin[2:])
                traite_un_chemin(pourcentage_détour)

        if données["autre_p_détour"]:
            traite_un_chemin(données["autre_p_détour"])

        LOG("Calcul des nouveaux cycla_min et cycla_max", bavard=1)
        g.calcule_cycla_min_max(z_d)
        
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
            données = form.cleaned_data
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
        g.charge_zone(z_d.nom)
    
        dessine_cycla(g, z_d, où_enregistrer="dijk/templates/"+nom, bavard=1)
    return render(requête, nom)



### Gestion des chemins (admin) ###


def sauv_chemins(requête):
    """
    Renvoie en téléchargement le csv de tous les chemins.
    """
    return HttpResponse(
        Chemin_d.sauv_csv(),
        headers={
            'Content-Type': "text/csv",
            'Content-Disposition': 'attachment; filename="chemins.csv"'
        }
    )
    

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
        Un nouvel élément d n’est ajouté que si son label n’est pas déjà présent et si le nb de résultats est < self.n_max
        """
        def __init__(self, n_max):
            self.res = []
            self.n_max = n_max
            self.déjà_présent = set()
            self.nb = 0
            self.trop_de_rés = False

        def __len__(self):
            return self.nb

        def ajoute(self, réponse: dict):
            """
            Entrées:
            réponse doit avoir au moins une clef « label » et optionnellement une clef « àCacher » à laquelle est associé un json.
            """
            if self.nb < self.n_max:
                àAfficher = réponse["label"]
                if àAfficher not in self.déjà_présent:
                    self.déjà_présent.add(àAfficher)
                    self.res.append(réponse)
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
        
        début = " ".join(x for x in [num, bis_ter] if x)
        if début: début += " "

        print(f"Recherche de {rue}")
        
        def chaîne_à_renvoyer(adresse, ville=None, parenthèse=None):
            res = ";".join(tout[:-1] + [début+adresse])
            if parenthèse:
                res += f" ({parenthèse})"
            if ville: res += ", " + ville
            return res

        # Villes de la zone z_id
        villes = Ville_Zone.objects.filter(zone=z_id, ville__nom_norm__icontains=déb_ville)
        req_villes = Subquery(villes.values("ville"))

        
        res = Résultat(nbMax)

        # Complétion dans l’arbre lexicographique (pour les fautes de frappe...)
        # Fonctionne sauf qu’on ne récupère pas la ville pour l’instant
        # dans_l_arbre = g.arbre_lex_zone[z_d].complétion(à_chercher, tol=2, n_max_rés=nbMax)
        # print(dans_l_arbre)

        # Recherche dans les gtls:
        essais = re.findall("(une?) (.*)", rue)
        if len(essais) == 1:
            déterminant, texte = essais[0]
            gtls = GroupeTypeLieu.objects.filter(nom__istartswith=texte, féminin=déterminant=="une")
            for gtl in gtls:
                res.ajoute(gtl.pour_autocomplète())
        
        # Recherche dans les lieux
        lieux = Lieu.objects.filter(nom__icontains=rue, ville__in=req_villes).prefetch_related("ville", "type_lieu")
        print(f"{len(lieux)} lieux trouvées")
        for l in lieux:
            res.ajoute(l.pour_autocomplète())
        
        
        # Recherche dans les rues de la base
        dans_la_base = Rue.objects.filter(nom_norm__icontains=rue, ville__in=req_villes).prefetch_related("ville")
        for rue_trouvée in dans_la_base:
            res.ajoute({"label": chaîne_à_renvoyer(rue_trouvée.nom_complet, rue_trouvée.ville.nom_complet),
                        "àCacher": json.dumps({"type": "rue", "pk": rue_trouvée.pk, "num": num, "bis_ter": bis_ter, "coords": ""})}
                       )

        
        
        # Recherche dans les caches
        # for truc in Cache_Adresse.objects.filter(adresse__icontains=rue, ville__in=req_villes).prefetch_related("ville"):
        #     print(f"Trouvé dans Cache_Adresse : {truc}")
        #     chaîne = chaîne_à_renvoyer(truc.adresse, truc.ville.nom_complet)
        #     res.ajoute(chaîne)
            
        # for chose in CacheNomRue.objects.filter(
        #         Q(nom__icontains=rue) | Q(nom_osm__icontains=rue), ville__in=req_villes
        # ).prefetch_related("ville"):
        #     print(f"Trouvé dans CacheNomRue : {chose}")
        #     chaîne = chaîne_à_renvoyer(chose.nom_osm, chose.ville.nom_complet)
        #     res.ajoute(chaîne_à_renvoyer(chose.nom_osm, chose.ville.nom_complet))

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
        bbox = tuple(map(float, données["bbox"].split(",")))
            
        lieux = recup_donnees.lieux_of_types_lieux(bbox, données["type_lieu"].all(), bavard=3)
        
        LOG(f"{len(lieux)} lieux trouvés", bavard=1)
        données["marqueurs"] = [l.marqueur_leaflet("laCarte") for l in lieux]
        return render(requête, "dijk/autourDeMoi.html", données)
    else:
        form = forms.AutourDeMoi()
        return render(requête, "dijk/autourDeMoi.html", {"form": form})
