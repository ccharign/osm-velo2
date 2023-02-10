# -*- coding:utf-8 -*-

### Fonctions diverses pour utiliser le logiciel

from time import perf_counter
from django.db import transaction, close_old_connections
import gpxpy
from branca.element import Element


from folium.plugins import Fullscreen, LocateControl

from dijk.progs_python.petites_fonctions import chrono, deuxConséc, LOG

import dijk.models as mo
from dijk.models import Chemin_d, Arête


tic = perf_counter()
from mon_folium import folium_of_chemin, ajoute_marqueur, folium_of_arêtes, couleur_of_cycla, color_dict, NB_COUL
chrono(tic, "mon_folium", bavard=2)

import dijkstra

tic = perf_counter()
import chemins
chrono(tic, "chemins", bavard=2)

import apprentissage as ap



def liste_Arête_of_iti(g, iti, p_détour):
    """
    Entrée : iti (int list), liste d'id osm
    Sortie : liste d'Arêtes
    """
    tic = perf_counter()
    res = [g.meilleure_arête(s, t, p_détour) for (s, t) in deuxConséc(iti)]
    chrono(tic, "conversion de l'itinéraire en liste d'Arêtes.")
    return res


DICO_PROFIl = {
    0: ("Le plus court",
        "Le trajet le plus court tenant compte des contraintes indiquées."
        ),
    15: ("Intermédiaire",
         "Un cycliste de profil « intermédiaire » rallonge en moyenne ses trajets de 10% pour éviter les rues désagréables. Il rallongera son trajet de 15% pour remplacer un itinéraire entièrement non aménagé par un itinéraire entièrement sur piste cyclable."
         ),
    30: ("Priorité confort",
         "Un cycliste de profil « priorité confort » rallonge en moyenne ses trajets de 15% pour passer par les zones plus agréables. Il pourra faire un détour de 30% pour remplacer un itinéraire entièrement non aménagé par un itinéraire entièrement sur piste cyclable."
         )
}


def légende_et_aide(p_détour):
    pourcent = int(100*p_détour)
    if pourcent in DICO_PROFIl:
        return DICO_PROFIl[pourcent]
    else:
        return f"Profil détour {pourcent}%", ""


def itinéraire_of_étapes(étapes,
                         étapes_sommets,
                         ps_détour,
                         g,
                         z_d,
                         rajouter_iti_direct=True,
                         étapes_interdites={},
                         bavard=0):
    """
    Entrées:
        ps_détour (float list)
        étapes (listes d’étapes), départ et arrivée inclus.
        étapes_interdites (Étape list)

    Sortie : dico avec les clefs suivantes :
       (stats : liste de dicos (légende, aide, id, p_détour, longueur, longueur ressentie, couleur, gpx) pour les itinéraires obtenus,
        c : chemin avec le plus grand p_détour,
        nom_étapes,
        nom_rues_interdites,
        bbox,
        itinéraires: liste d’Itinéraire
       )
    """
    
    np = len(ps_détour)
    ps_détour.sort()  # Pour être sûr que l’éventuel 0 est en premier.
    stats = []
    itinéraires = []
    
    interdites = chemins.arêtes_interdites(g, z_d, étapes_interdites, bavard=bavard)
    
    def traite_un_chemin(c, légende, aide):
        iti = g.itinéraire(c, bavard=bavard-2)
        itinéraires.append(iti)
        longueur = int(iti.longueur_vraie())
        
        stats.append({"légende": légende,
                      "aide": aide,
                      "p_détour": int(100*c.p_détour),
                      "id": f"ps{int(100*c.p_détour)}",
                      "longueur": longueur,
                      "temps": int(longueur/15000*60),  # Moyenne de 15km/h disons
                      "longueur_ressentie": int(iti.longueur),
                      "couleur": c.couleur,
                      "gpx": gpx_of_iti(iti, bavard=bavard-1)}
                     )

    tic = perf_counter()
    for i, p in enumerate(ps_détour):
        coul = color_dict[(i*NB_COUL)//np]
        c = chemins.Chemin(z_d, étapes, étapes_sommets, p, coul, False, interdites=interdites)
        
        traite_un_chemin(c, *légende_et_aide(p))
        tic = chrono(tic, f"dijkstra {c} et sa longueur")

    if ps_détour[0] == 0.:
        longueur_ch_direct = stats[0]["longueur"]
        
    d, a = étapes[0], étapes[-1]
    if rajouter_iti_direct:
        cd = chemins.Chemin(z_d, [d, a], [], 0, "#000000", False)
        traite_un_chemin(cd, "Trajet direct", "Le trajet le plus court, sans prendre en compte les étapes imposées.")
        tic = chrono(tic, "Calcul de l'itinéraire direct.")
        longueur_ch_direct = stats[-1]["longueur"]

    # Calculer les pourcentages de détour effectifs
    if (rajouter_iti_direct or ps_détour[0] == 0.) and longueur_ch_direct > 0:
        for s in stats:
            s["p_détour_effectif"] = int((s["longueur"]/longueur_ch_direct - 1.) * 100.)

    # Ajout de marqueurs pour le début et la fin de l’itinéraire avec le plus grand p_détour
    # -> délégué au client maintenant
    # coords_départ = g.coords_of_id_osm(itinéraires[-1].liste_sommets[0])  # coords du début de l’iti avec le plus grand p_détour
    # coords_arrivée = g.coords_of_id_osm(itinéraires[-1].liste_sommets[-1])
    # itinéraires[-1].marqueurs = [
    #     étapes[0].marqueur_leaflet(coords_départ),
    #     étapes[-1].marqueur_leaflet(coords_arrivée)
    # ]
    
    return {"stats": stats,
            "chemin": c,
            "noms_étapes": [str(é) for é in étapes],
            "rues_interdites": [str(é) for é in étapes_interdites],
            "bbox": list(itinéraires[0].bbox(g)),  # En list pour être envoyé à js
            "itinéraires": itinéraires
            }



### création du gpx ###
# https://pypi.org/project/gpxpy/


def gpx_of_iti(iti_d, bavard=0):
    """
    Entrée : iti_d (Arête list)
             session (dic), le dictionnaire de la session Django

    Sortie : le gpx où les \n sont remplacés par des ν
    """
    
    res = gpxpy.gpx.GPX()
    tronçon = gpxpy.gpx.GPXTrack()
    res.tracks.append(tronçon)
    segment = gpxpy.gpx.GPXTrackSegment()
    tronçon.segments.append(segment)
    
    for a in iti_d.liste_arêtes:
        for lon, lat in a.géométrie():
            segment.points.append( gpxpy.gpx.GPXTrackPoint(lat, lon) )

    res_str = res.to_xml()#.replace(" ", "%20").replace("\n", "ν")
    return res_str


#################### Affichage ####################

# Pour utiliser folium sans passer par osmnx regarder :
# https://stackoverflow.com/questions/57903223/how-to-have-colors-based-polyline-on-folium


# Affichage folium avec couleur
# voir https://stackoverflow.com/questions/56234047/osmnx-plot-a-network-on-an-interactive-web-map-with-different-colours-per-infra

def dessine(listes_chemins, g, z_d, ad_départ, ad_arrivée, où_enregistrer, bavard=0, fouine=False):
    """
    Entrées :
      - listes_chemins : liste de couples (liste d'Arêtes, couleur)
      - g (instance de Graphe)
      - ad_départ, ad_arrivée (instances d’Adresse). Pour la première et la dernière partie de l’itinéraire et les marqueurs de départ et arrivée.
      - où_enregistrer : adresse du fichier html à créer
    Sortie:
       la carte
       la bounding box
    Effet:
      Crée le fichier html de la carte superposant tous les itinéraires fournis.
    """

    # Initialisation de la carte avec le premier chemin.
    l, _, _ = listes_chemins[0]
    
    # Je mets les coords de début et fin du premier itinéraire si les champs coords des adresses n’était pas remplis.
    cd = l[0].départ.coords()
    cf = l[0].arrivée.coords()
    o, e = sorted([cd[0], cf[0]])  # lon
    s, n = sorted([cd[1], cf[1]])  # lat
    if not ad_départ.coords:
        ad_départ.coords = cd
    if not ad_arrivée.coords:
        ad_arrivée.coords = cf

    

    carte = None
    for l, coul, p in listes_chemins:
        carte = folium_of_chemin(g, z_d, l, p, carte=carte, color=coul)

    ajoute_marqueur(ad_départ, carte, fouine=fouine)
    ajoute_marqueur(ad_arrivée, carte, fouine=fouine)

    # Bonus
    Fullscreen(title="Plein écran", title_cancel="Quitter le plein écran").add_to(carte)
    LocateControl(locateOptions={"enableHighAccuracy":True}).add_to(carte)

    # modif de la carte
    nom_carte = carte.get_name()
    carte.get_root().script.add_child(
        Element(f"""
        $(document).ready(function() {{
            gèreLesClics({nom_carte});
            marqueurs_of_form(document.getElementById("relance_rapide"), {nom_carte});
            L.tileLayer.provider('CyclOSM').addTo({nom_carte});
        ;}});
""")
    )
    carte.save(où_enregistrer)
    return carte, (s,o,n,e)




# def dessine_chemin(c, g, où_enregistrer=os.path.join(TMP, "chemin.html"), ouvrir=False, bavard=0):
#     """
#     Entrées :
#        - c (instance de Chemin)
#        - g (instance de Graphe)
#        - p_détour (float ou float list) : liste des autres p_détour pour lesquels lancer et afficher le calcul.
#        - où_enregistrer : adresse où enregistrer le html produit.
#        - ouvrir (bool) : Si True, lance le navigateur sur la page créée.

#     Effet : Crée une carte html avec le chemin direct en rouge, et le chemin compte tenu de la cyclabilité en bleu.
#     Sortie : Longueur du chemin, du chemin direct.
#     """

#     # Calcul des chemins
#     c_complet, _ = dijkstra.chemin_étapes_ensembles(g, c)
#     longueur = g.longueur_itinéraire(c_complet, c.p_détour)
    
#     départ, arrivée = c_complet[0], c_complet[-1]
#     c_direct, _ = dijkstra.chemin(g, départ, arrivée, 0)
#     longueur_direct = g.longueur_itinéraire(c_direct, 0)

#     dessine([(c_complet, "blue", c.p_détour), (c_direct,"red", 0)], g, où_enregistrer, ouvrir=ouvrir)
#     return longueur, longueur_direct


def moyenne(t):
    return sum(t) / len(t)


def dessine_cycla(g, z_d, où_enregistrer, bavard=0):
    """
    Entrée : où_enregistrer (str) adresse et nom du fichier à créer.
    Effet : Crée la carte de la cyclabilité.
    """
    #g.calcule_cycla_min_max(z_d)

    arêtes = []

    for a in z_d.arêtes().exclude(cycla__isnull=True).prefetch_related("départ", "arrivée"):
        arêtes.append((a, {"color": couleur_of_cycla(a, g, z_d), "popup": a.cycla}))

    carte = folium_of_arêtes(g, arêtes)

    carte.save(où_enregistrer)
    print(f"Carte enregistrée à {où_enregistrer}")

    
    
### Apprentissage ###

def lecture_tous_les_chemins(g, z_t=None, n_lectures_max=20, bavard=1):
    """
    Lance l’apprentissage sur chaque chemin de la zone. Si None, parcourt toutes les zones de g.
    On lit n_lectures_max fois la liste de tous les chemins, ceux qui n’ont pas été modifiés étant retirés de la liste.
    """
    close_old_connections()
    if z_t is None:
        à_parcourir = g.zones
    else:
        z = g.charge_zone(z_t)
        à_parcourir = [z]

    # Liste des chemins à lire
    à_lire = []
    for z in à_parcourir:
        print(f"\nEntrainement sur la zone {z}")
        for c_d in Chemin_d.objects.filter(zone=z):
            c = chemins.Chemin.of_django(c_d, g, bavard=bavard-1)
            c.c_d = c_d
            à_lire.append(c)

    # lecture des chemins
    for _ in range(n_lectures_max):
        LOG(f"\n{len(à_lire)} chemins restant à lire.")
        à_lire_après = []
        for c in à_lire:
            try:
                n_modif, l = ap.lecture_meilleur_chemin(g, c, bavard=bavard-1)
                c.c_d.dernier_p_modif = n_modif / l
                LOG(f"\nLecture de {c}.\n {n_modif} arêtes modifiées, distance = {l}.\n\n", bavard=bavard)
                if n_modif > 0:
                    à_lire_après.append(c)
                else:
                    c.c_d.save()
            except Exception as e:
                print(f"Problème pour le chemin {c}\n {e}.\n Voulez-vous le supprimer de la base (o/n)?")
                if input("") == "o":
                    c.c_d.delete()
        à_lire = à_lire_après

    # sauvegarde des dernier_p_modif pour les chemins où ce n’est pas arrivé à 0.
    for c in à_lire:
        LOG(f"Apprentissage pas fini pour {c}, p_modif = {c.c_d.dernier_p_modif}")
        c.c_d.save()
        


def réinit_cycla(g, z_t=None, nb_lectures=6, bavard=0):
    """
    Vide la la cyclabilité des arêtes puis lance nb_lectures lectures des chemins.
    Pour la zone z_t si indiquée, sinon pour toutes les zones chargée dans g.
    """
    if z_t is None:
        à_parcourir = g.zones
    else:
        z=g.charge_zone(z_t)
        à_parcourir = [z]
    for z in à_parcourir:
        print(f"Effaçage de la cyclabilité des arêtes de la zone {z}")
        with transaction.atomic():
            arêtes = Arête.objects.filter(zone=z)
            for a in arêtes:
                a.cycla=None
        for _ in range(nb_lectures):
            lecture_tous_les_chemins(g, z.nom, bavard=bavard-1)
