# -*- coding:utf-8 -*-
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

from .progs_python import recup_donnees
from .progs_python.apprentissage import n_lectures
from .progs_python.bib_vues import bool_of_checkbox, énumération_texte, récup_données, z_é_i_d

from .progs_python.utils import dessine_cycla, itinéraire_of_étapes

from .progs_python.graphe_par_django import Graphe_django

from .models import Chemin_d, Zone

import dijk.progs_python.autoComplétion as ac





g = Graphe_django()


def renvoieSurPageDErreur(vue):
    """
    Décorateur sur une vue pour renvoyer sur la page d’erreur en cas d’erreur non rattrapée avant.
    """
    def nv_vue(requête, *args, **kwargs):
        try:
            return vue(requête, *args, **kwargs)
        except (PasTrouvé, recup_donnees.LieuPasTrouvé) as e:
            return vueLieuPasTrouvé(requête, e)
        except Exception as e:
            traceback.print_exc()
            return autreErreur(requête, e)
    return nv_vue




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

@renvoieSurPageDErreur
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
    étapes_dicos = json.loads(données["toutes_les_étapes"])
    z_d, étapes, étapes_interdites, étapes_sommets, ps_détour = z_é_i_d(g, données)
    
    #  Échange départ-arrivée dans le dico de données
    # données["départ"], données["arrivée"] = données["arrivée"], données["départ"]
    # données["données_cachées_départ"], données["données_cachées_arrivée"] = données["données_cachées_arrivée"], données["données_cachées_départ"]

    #  Étapes à l’envers
    étapes.reverse()
    données["toutes_les_étapes"] = json.dumps(étapes_dicos)
    #  données["marqueurs_é"] = chaîne_avec_points_virgule_renversée(données["marqueurs_é"])

    return calcul_itinéraires(requête, ps_détour, z_d,
                              étapes,
                              étapes_sommets,
                              étapes_interdites=étapes_interdites,
                              données=données
                              )



###########################
### Fonction principale ###
###########################


@renvoieSurPageDErreur
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
        

    données.update(itinéraire_of_étapes(
        étapes, étapes_sommets, ps_détour, g, z_d,
        rajouter_iti_direct=len(étapes) > 2,
        étapes_interdites=étapes_interdites,
        bavard=bavard
    ))
    noms_étapes = données["noms_étapes"]
    rues_interdites = données["rues_interdites"]
    
    # Mettre les traces gpx dans le dico de session, et les sortir de données
    for stat in données["stats"]:
        if "gpx" not in requête.session:
            requête.session["gpx"] = {}
        requête.session["gpx"][stat["p_détour"]] = stat.pop("gpx")


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
    données.update({#"étapes": ";".join(noms_étapes[1:-1]),
                    #"rues_interdites": ";".join(rues_interdites),
                    "pourcentage_détour": ";".join(map(lambda p: str(int(p*100)), ps_détour)),
                    "départ": str(étapes[0]),
                    "arrivée": str(étapes[-1]),
                    "zone_t": z_d.nom,
                    #"marqueurs_i": texte_marqueurs(étapes_interdites),  # Sera mis en hidden dans le formulaire relance_rapide
                    #"marqueurs_é": texte_marqueurs(étapes, supprime_début_et_fin=True),  # idem
    })


    #texte_étapes_inter = énumération_texte(noms_étapes[1:-1])

    # données sérialisées pour envoyer à js
    pour_js = {
        "bbox": données["bbox"],
        "itis": [iti.vers_js() for iti in données["itinéraires"]],
        "mettre_form_enregistrer": len(étapes) > 2 and len(étapes_sommets)==0,
    }

    return render(requête,
                  "dijk/résultat_itinéraire_sans_carte.html",
                  {**données,
                   **{
                       #  "texte_étapes_inter": texte_étapes_inter,
                       # "rues_interdites": énumération_texte(rues_interdites),
                       "post_préc": données,
                       "relance_rapide": forms.ToutCaché(initial=données),
                       "enregistrer_contrib": forms.EnregistrerContrib(initial=données),  # À enlever à terme
                       "fouine": requête.session.get("fouine", None),
                       "données": json.dumps(pour_js)
                   }
                   }
                  )







####################################
### Ajout d’un nouvel itinéraire ###
####################################


def confirme_nv_chemin(requête):
    """
    Traitement du formulaire d’enregistrement d’un nouveau chemin.
    """
    nb_lectures = 30

    données = récup_données(requête.POST, forms.EnregistrerContrib)
    z_d, étapes, étapes_interdites, étapes_sommets, _ = z_é_i_d(g, données)
    if étapes_sommets:
        raise RuntimeError("Ne pas enregistrer avec des étapes « passer par »")
    AR = bool_of_checkbox(requête.POST, "AR")

    def traite_un_chemin(pourcentage_détour: int):
        c = Chemin.of_étapes(z_d, étapes, pourcentage_détour, AR, g, étapes_interdites=étapes_interdites, nv_cache=2, bavard=2)
        chemins.append(c)
        prop_modif = n_lectures(nb_lectures, g, [c], bavard=1)
        c_d = c.vers_django(bavard=1)
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
    z_d.calculeCyclaMinEtMax()

    return render(requête, "dijk/merci.html", {"chemin": chemins, "zone_t": z_d.nom})


### traces gpx ###

@renvoieSurPageDErreur
def téléchargement(requête):
    """
    Fournit le .gpx, contenu dans requête.POST["gpx"]
    """

    return HttpResponse(
        requête.POST["gpx"].replace("%20", " ").replace("ν", "\n"),
        headers={
            'Content-Type': "application/gpx+xml",
            'Content-Disposition': 'attachment; filename="trajet.gpx"'
        }
    )

@renvoieSurPageDErreur
def envoieGpx(requête, p_détour):
    """
    Fournit le .gpx contenu dans requête.session["gpx"][p_détour]
    """
    return HttpResponse(
        # Il semble que les clefs soient transformées en str dans requête.session
        requête.session["gpx"][str(p_détour)].replace("%20", " ").replace("ν", "\n"),
        headers={
            'Content-Type': "application/gpx+xml",
            'Content-Disposition': 'attachment; filename="trajet.gpx"'
        }
    )


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



### Autocomplétion ###

def pour_complétion(requête, nbMax=15):
    """
    Renvoie la réponse nécessitée par autocomplete.
    Laisse tel quel la partie avant le dernier ;
    Découpe l’adresse en (num? bis_ter? rue(, ville)?), et cherche des complétions pour rue et ville.
    nbMax : nb max de résultat. S’il y en a plus, aucun n’est renvoyé.
    """
    mimeType = "application/json"
    # Une requête d’autocomplétion à une clef « term »
    if "term" in requête.GET:

        # id de la zone
        if "zone_id" not in requête.session:
            z_d = Zone.objects.get(nom=requête.session["zone"])
            requête.session["zone_id"] = z_d.pk
            z_id = z_d.pk
        else:
            z_id = requête.session["zone_id"]
            z_d = Zone.objects.get(pk=z_id)

        res = ac.complétion(requête.GET["term"], nbMax, z_d)
        
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
        # Traitement du formulaire
        données = récup_données(requête.GET, forms.AutourDeMoi, validation_obligatoire=False)
        bbox = tuple(map(float, données["bbox"].split(",")))

        gtls = données["gtls"].all()
        tls = []
        for gtl in gtls:
            tls.extend(gtl.type_lieu.all())
        lieux = recup_donnees.lieux_of_types_lieux(
            bbox,
            tls,
            bavard=3
        )
        LOG(f"{len(lieux)} lieux trouvés", bavard=1)
        
        données["marqueurs"] = json.dumps(lieux)
        return render(requête, "dijk/autourDeMoi.html", données)
    
    else:
        # Initialisation du formulaire
        form = forms.AutourDeMoi()
        return render(requête, "dijk/autourDeMoi.html", {"form": form})
