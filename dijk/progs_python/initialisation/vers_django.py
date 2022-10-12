
# -*- coding:utf-8 -*-


##################################################
### Transférer les données dans la base Django ###
##################################################

import re
import json

from django.db import transaction, close_old_connections
from django.db.models import Q

from dijk.models import Ville, Rue, Sommet, Arête, Chemin_d, Ville_Zone, Zone
from dijk.progs_python.lecture_adresse.normalisation import prétraitement_rue, partie_commune
from params import LOG
from petites_fonctions import union, intersection, distance_euc
from lecture_adresse.arbresLex import ArbreLex

# L’arbre contient les f"{nom_norm}|{code}"
def à_mettre_dans_arbre(nom_n, code):
    return f"{nom_n}|{code}"



def arbre_des_villes(zone_d=None):
    """
    Renvoie l’arbre lexicographique des villes de la base.
    Si zone_d est précisé, seulement les villes de cette zone.
    """
    print("Création de l’arbre des villes")
    res = ArbreLex()
    if zone_d is None:
        villes = Ville.objects.all()
    else:
        villes = zone_d.villes()
    for v_d in villes:
        res.insère(à_mettre_dans_arbre(v_d.nom_norm, v_d.code))
    print("--- fini")
    return res


def ajoute_code_postal(nom, code):
    """
    Ajoute ou corrige le code postal de la ville.
    Sortie (models.Ville)
    """
    essai = Ville.objects.filter(nom_norm = partie_commune(nom)).first()
    if essai:
        essai.code=code
        essai.save()
        return essai
    else:
        raise RuntimeError(f"Ville pas trouvée dans la base INSEE : {nom}, {(code)}")

        
def nv_ville(nom, code, zone_d, tol=3):
    """
    Effet : si pas déjà présente, rajoute la ville dans la base django et dans l'arbre lex ARBRE_VILLES.
    Sortie : l'objet Ville créé ou récupéré dans la base.
    """
    nom_norm = partie_commune(nom)
    arbre = arbre_des_villes(zone_d=zone_d)
    dans_arbre, d = arbre.mots_les_plus_proches(à_mettre_dans_arbre(nom_norm, code), d_max=tol)
    
    if len(dans_arbre) > 0:
        print(f"Ville(s) trouvée(s) dans l'arbre : {tuple(dans_arbre)}")
        nom_n_corrigé, code_corrigé = tuple(dans_arbre)[0].split("|")
        if d>0:
            LOG(f"Avertissement : la ville {nom_norm, code} a été corrigée en {nom_n_corrigé, code_corrigé}")
        v_d = Ville.objects.get(nom_norm=nom_n_corrigé, code=code_corrigé)
        return v_d
    
    else:
        v_d = Ville(nom_complet=nom, code=code, nom_norm=nom_norm)
        v_d.save()
        rel = Ville_Zone(ville=v_d, zone=zone_d)
        rel.save()
        return v_d

    
def liste_attributs(g):
    """
    Entrée : g (multidigraph)
    Sortie : dico (attribut -> liste des valeurs) des arêtes qui apparaissent dans g
    Fonction utile pour régler les paramètres de cycla_défaut.
    """

    res = {}
    for s in g.nodes:
        for t in g[s].keys():
            for a in g[s][t].values():
                for att, val in a.items():
                    if att not in ["name", "length", "geometry", "osmid"]:
                        if att not in res:res[att]=set()
                        res[att].add(str(val))
    return res


def désoriente(g, bavard=0):
    """
    Entrée : g (Graphe_nx)
    Effet : rajoute les arêtes inverses si elles ne sont pas présentes, avec un attribut 'sens_interdit' en plus.
    """
    
    def existe_inverse(s,t,a):
        """
        Indique si l’arête inverse de (s,t,a) est présente dans gx.
        """
        if s not in gx[t]:
            return False
        else:
            inverses_de_a = tuple(a_i for a_i in gx[t][s].values() if a.get("name",None)==a_i.get("name", None))
            if len(inverses_de_a)==1:
                return True
            elif len(inverses_de_a)==0:
                return False
            else:
                inverses_de_a = tuple(a_i for a_i in inverses_de_a if sorted(géom_texte(s,t,a,g) )==sorted(géom_texte(t,s,a_i,g)))
                if len(inverses_de_a)==1:
                    return True
                elif len(inverses_de_a) == 0:
                    return False
                else:
                    print(f"Avertissement : Arête en double : {s}, {t}, {inverses_de_a}")
                    return True

    
    def ajoute_inverse(s,t,a):
        if bavard>1:
            print(f"ajout de l’arête inverse de {s}, {t}, {a}")
        a_i = {att:val for att,val in a.items()}
        if "maxspeed" in a and a["maxspeed"] in ["10", "20", "30"]:
            a_i["contresens cyclable"]=True
        else:
            a_i["sens_interdit"]=True
        gx.add_edge(t,s,**a_i )

        
    gx=g.multidigraphe
    for s in gx.nodes:
        for t in gx[s].keys():
            if t!=s:  # Il semble qu’il y ait des doublons dans les boucles dans les graphes venant de osmnx
                for a in gx[s][t].values():
                    if a["highway"]!="cycleway" and not any("rond point" in c for c in  map(partie_commune, tuple_valeurs(a, "name"))) and not existe_inverse(s, t, a):
                        ajoute_inverse(s,t,a)
                    
@transaction.atomic
def sauv_données(à_sauver):
    """
    Sauvegarde les objets en une seule transaction.
    Pour remplacer bulk_create si besoin du champ id nouvellement créé.
    """
    for o in à_sauver:
        o.save()
    LOG("fin de sauv_données")

    
def géom_texte(s, t, a, g):
    """
    Entrée : a (dico), arête de nx.
             s_d, t_d (Sommet, Sommet), sommets de départ et d’arrivée de a
    Sortie : str adéquat pour le champ geom d'un objet Arête. 
    """
    if "geometry" in a:
        geom = a["geometry"].coords
    else:
        geom = (g.coords_of_nœud(s), g.coords_of_nœud(t))
    coords_texte = (f"{lon},{lat}" for lon, lat in geom)
    return ";".join(coords_texte)



def cycla_défaut(a, sens_interdit=False, pas=1.1):
    """
    Entrée : a, arête d'un graphe nx.
    Sortie (float) : cycla_défaut
    Paramètres:
        pas : pour chaque point de bonus, on multiplie la cycla par pas
        sens_interdit : si Vrai, bonus de -2
    Les critères pour attribuer des bonus en fonction des données osm sont définis à l’intérieur de cette fonction.
    """
    # disponible dans le graphe venant de osmnx :
    # maxspeed, highway, lanes, oneway, access, width
    critères= {
        #att : {val: bonus}
        "highway": {
            "residential":1,
            "cycleway":3,
            "step":-10,
            "pedestrian":1,
            "tertiary":1,
            "living_street":1,
            "footway":1,
        },
        "maxspeed": {
            "10":3,
            "20":2,
            "30":1,
            "70":-2,
            "90":-4,
            "130":-float("inf")
        },
        "sens_interdit":{True:-5}
    }
    bonus = 0
    for att in critères:
        if att in a:
            val_s = a[att]
            if isinstance(val_s, str) and val_s in critères[att]:
                bonus+=critères[att][val_s]
            elif isinstance(val_s, list):
                for v in val_s:
                    if v in critères[att]:
                        bonus+= critères[att][v]

    return pas**bonus


def a_la_valeur(a, att, val):
    """
    Entrée : a (arête nx)
             att
             val
    Indique si l’arête a à la valeur val pour l’attribut att
    """
    if att in a:
        if isinstance(a[att], str):
            return a[att]==val
        elif isinstance(a[att], list):
            return val in a[att]
        else:
            print(f"Avertissement : l’attribut {att} pour l’arête {a} n’était ni un str ni un list.")
            return False
    else:
        return False

    
def tuple_valeurs(a, att):
    """
    Renvoie le tuple des valeurs de l’attribut att dans l’arête a.
    """
    if att in a:
        if isinstance(a[att], list):
            return tuple(a[att])
        else:
            return (a[att],)
    else:
        return ()


def longueur_arête(s, t, a, g):
    """
    Entrées : a (dic), arête de nx
              g (graphe_par_django)
    Sortie : min(a["length"], d_euc(s,t))
    """
    deuc = distance_euc(g.coords_of_nœud(s), g.coords_of_nœud(t))
    if a["length"]<deuc:
        print(f"Distance euc ({deuc}) > a['length'] ({a['length']}) pour l’arête {a} de {s} à {t}")
        return deuc
    else:
        return a["length"]
    
    
def transfert_graphe(g, zone_d, bavard=0, rapide=1, juste_arêtes=False):
    """
    Entrée : g (Graphe_nx)
             zone_d (instance de Zone)

    Effet : transfert le graphe dans la base Django.
    La longueur des arêtes est mise à min(champ "length", d_euc de ses sommets).
    
    Sortie : arêtes créées, arêtes mises à jour
    
    Paramètres:
        rapide (int) : pour tout  (s,t) sommets voisins dans g,
                            0 -> efface toutes les arêtes de s vers t et remplace par celles de g
                            1 -> regarde si les arête entre s et t dans g correspondent à celles dans la base, et dans ce cas ne rien faire.
                        « correspondent » signifie : même nombre et mêmes noms.
                            2 -> si il y a quelque chose dans la base pour (s,t), ne rien faire.
        juste_arêtes (bool) : si vrai, ne recharge pas les sommets.
    """

    gx = g.multidigraphe

    tous_les_sommets = Sommet.objects.all()
    print(f"{len(tous_les_sommets)} sommets dans la base")

    ### Sommets ###
    if not juste_arêtes:
        LOG("Chargement des sommets")
        à_créer = []
        à_màj=[]
        nb=0
        for s in g.multidigraphe.nodes:
            if nb%100==0: print(f"    {nb} sommets vus")
            nb+=1
            lon, lat = g.coords_of_nœud(s)
            essai = Sommet.objects.filter(id_osm=s).first()
            if essai is None:
                s_d = Sommet(id_osm=s, lon=lon, lat=lat)
                à_créer.append(s_d)
            else:
                s_d = essai
                # màj des coords au cas où...
                s_d.lon = lon
                s_d.lat = lat
                à_màj.append(s_d)
                
        LOG(f"Ajout des {len(à_créer)} nouveaux sommets dans la base")
        sauv_données(à_créer)
        LOG(f"Mise à jour des {len(à_màj)} sommets modifiés")
        Sommet.objects.bulk_update(à_màj, ["lon", "lat"])

        LOG("Ajout de la zone à chaque sommet")
        # Pas possible avant car il faut avoir sauvé l’objet pour rajouter une relation ManyToMany.
        # Il faudrait un bulk_manyToMany ... -> utiliser la table d’association automatiquement créée par Django : through
        #https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.ManyToManyField
        LOG("Sommets créés", bavard=bavard)
        rel_àcréer = []
        for s_d in à_créer:
            rel = Sommet.zone.through(sommet_id=s_d.id, zone_id=zone_d.id)
            rel_àcréer.append(rel)
        LOG("Sommets mis à jour", bavard=bavard)
        for s_d in à_màj:
            if zone_d not in s_d.zone.all():
                rel = Sommet.zone.through(sommet_id=s_d.id, zone_id=zone_d.id)
                rel_àcréer.append(rel)
        Sommet.zone.through.objects.bulk_create(rel_àcréer)


    ### Arêtes ###

    # pour profiling
    temps = {"correspondance":0., "remplace_arêtes":0., "màj_arêtes":0., "récup_nom":0.}
    nb_appels = {"correspondance":0, "remplace_arêtes":0, "màj_arêtes":0, "récup_nom":0}

    # Création du dico sommet -> liste de (voisin, arête) pour les arêtes déjà existantes dans la base.
    dico_voisins = {}
    toutes_les_arêtes = Arête.objects.all().select_related("départ", "arrivée")
    for a in toutes_les_arêtes:
        s = a.départ.id_osm
        t = a.arrivée.id_osm
        if s not in dico_voisins: dico_voisins[s]=[]
        dico_voisins[s].append((t, a))

    #@mesure_temps("récup_nom", temps, nb_appels)
    def récup_noms(arêtes_d, nom):
        """ Renvoie le tuple des a∈arêtes_d qui ont pour nom 'nom'"""
        return [a_d for a_d in arêtes_d if nom==a_d.nom]
    
    #@mesure_temps("correspondance", temps, nb_appels)
    def correspondance(s_d, t_d, s, t, gx):
        """
        Entrées:
            - s_d, t_d (Sommet)
            - s, t (int)
            - gx (multidigraph)
        Sortie ( bool × (Arête list) × (dico list)) : le triplet ( les arêtes correspondent à celles dans la base, arêtes de la bases, arêtes de gx)
        Dans le cas où il y a correspondance, les deux listes renvoyées contiennent les arêtes dans le même ordre.
        Ne prend en compte que les arêtes de s_d vers t_d.
        « Correspondent » signifie ici même nombre, et mêmes noms. En cas de plusieurs arêtes de même nom, le résultat sera Faux dans tous les cas.
        """
        vieilles_arêtes = [a_d for (v, a_d) in dico_voisins.get(s, []) if v==t]
        if t not in gx[s]:
            return False, vieilles_arêtes, []
        else:
            arêtes = gx[s][t].values()
            noms = [ a.get("name", None) for a in arêtes ]
            if len(noms) != len(vieilles_arêtes):
                return False, vieilles_arêtes, arêtes
            else:
                arêtes_ordre = []
                for a in arêtes:
                    essai_a_d = récup_noms(vieilles_arêtes, a.get("name", None))
                    if len(essai_a_d) != 1:
                        #if vieilles_arêtes.filter(nom=a.get("name", None)).count()!=1:
                        return False, vieilles_arêtes, arêtes
                    else:
                        arêtes_ordre.append(essai_a_d[0])
                    
                return True, arêtes_ordre, arêtes

    
    #@mesure_temps("màj_arêtes", temps, nb_appels)
    def màj_arêtes(s_d, t_d, s, t, arêtes_d, arêtes_x):
        """
        Entrées:
            - arêtes_d (Arête list) : arêtes de la base
            - arêtes_x (dico list) : arêtes de gx
        Précondition : les deux listes représentent les mêmes arêtes, et dans le même ordre
        Effet:
            Met à jour les champs cycla_défaut, zone, géométrie des arêtes_d avec les données des arête_nx.
        Sortie : les arêtes modifiées. Il faudra encore un Arête.bulk_update.
        """
        res = []
        for a_d, a_x in zip(arêtes_d, arêtes_x):
            #a_d.geom = géom_texte(s, t, a_x, g)
            #a_d.zone.add(zone_d)
            a_d.cycla_défaut = cycla_défaut(a_x)
            res.append(a_d)
        return res

    #@mesure_temps("remplace_arêtes", temps, nb_appels)
    def remplace_arêtes(s_d, t_d, s, t, arêtes_d, gx, bavard=0):
        """
        Supprime les arêtes de arêtes_d, et crée à la place celles venant de gx[s][t].
        Sortie (Arête list): les arêtes créées. Pas encore sauvées.
        Effet : les arêtes à créer sont ajoutées dans à_créer.
        """
        #arêtes_d.delete()
        
        if t in gx[s]:
            arêtes_nx = gx[s][t].values()
        else:
            arêtes_nx = []
        
        for a in arêtes_d:
            LOG(f"arête à supprimer : {a} -> {a.départ, a.arrivée, a.nom}\n à remplacer par {arêtes_nx} -> {list(arêtes_nx)[0].get('name')}.", bavard=bavard-1)
            a.delete()
        
        res = []
        for a_nx in arêtes_nx:
            a_d = Arête(départ=s_d,
                        arrivée=t_d,
                        nom=a_nx.get("name", None),
                        longueur=longueur_arête(s, t, a_nx, g),
                        cycla_défaut=cycla_défaut(a_nx),
                        geom=géom_texte(s, t, a_nx, g)
                        )
            res.append(a_d)
        return res

    LOG("Chargement des arêtes depuis le graphe osmnx", bavard)
    nb = 0
    à_créer = []
    à_màj = []
    with transaction.atomic():  # Utile pour les suppressions d’anciennes arêtes.
        for s in gx.nodes:
            s_d = tous_les_sommets.get(id_osm=s)
            for t, _ in gx[s].items():
                if t != s:  # Suppression des boucles
                    nb += 1
                    if nb%500==0: print(f"    {nb} arêtes traitées\n ") #{temps}\n{nb_appels}\n")
                    t_d = tous_les_sommets.get(id_osm=t)
                    if rapide < 2:
                        correspondent, arêtes_d, arêtes_x = correspondance(s_d, t_d, s, t, gx)
                        if rapide == 0 or not correspondent:
                            à_créer.extend(remplace_arêtes(s_d, t_d, s, t, arêtes_d, gx, bavard=bavard-1))
                        else:
                            à_màj.extend(màj_arêtes(s_d, t_d, s, t, arêtes_d, arêtes_x))
    
    LOG(f"Ajout des {len(à_créer)} nouvelles arêtes dans la base", bavard)
    sauv_données(à_créer)  # bulk_create pas possible
    LOG(f"Mise à jour des {len(à_màj)} anciennes arêtes")
    Arête.objects.bulk_update(à_màj, ["cycla_défaut"])

    
    

def ajoute_zone_des_arêtes(zone_d, créées, màj):
    ### Zone des arêtes
    LOG("Ajout de la zone à chaque arête")
    nb = 0
    ## nouvelles arêtes -> rajouter zone_d mais aussi les éventuelles anciennes zones.
    rel_àcréer = []
    for a_d in créées:
        for z in union([zone_d], intersection(a_d.départ.zone.all(), a_d.arrivée.zone.all())):
            rel = Arête.zone.through(arête_id=a_d.id, zone_id=z.id)
            rel_àcréer.append(rel)
    Arête.zone.through.objects.bulk_create(rel_àcréer)
    ## anciennes arêtes mises à jour -> rajouter zone_d et ville_d si pas présente.
    rel_àcréer = []
    for a_d in màj:
        if zone_d not in a_d.zone.all():
            rel = Arête.zone.through(arête_id=a_d.id, zone_id=zone_d.id)
            rel_àcréer.append(rel)
        nb += 1
        if nb%1000==0: print(f"    {nb} arêtes traités")
    Arête.zone.through.objects.bulk_create(rel_àcréer)


@transaction.atomic()
def charge_dico_rues_nœuds(ville_d, dico):
    """
    Entrée :
        - ville_d (instance de ville)
        - dico : un dico nom_de_rue -> liste de nœuds
    Effet :
        remplit la table dijk_rue. Si une rue était déjà présente, elle sera supprimée.
    """
    rues_à_créer=[]
    for rue_n, (rue, nœuds) in dico.items():
        #rue_n = prétraitement_rue(rue)
        assert rue_n == prétraitement_rue(rue_n), f"La rue suivante n’était pas normalisée : {rue_n}"
        nœuds_texte = ",".join(map(str, nœuds))
        vieilles_rues = Rue.objects.filter(nom_norm=rue_n, ville=ville_d)
        vieilles_rues.delete()
        rue_d = Rue(nom_complet=rue, nom_norm=rue_n, ville=ville_d, nœuds_à_découper=nœuds_texte)
        rues_à_créer.append(rue_d)
    Rue.objects.bulk_create(rues_à_créer)
        


def cycla_défaut_of_csv(chemin, bavard=0):
    """
    Entrée : adresse d’un csv contenant des nom de rue et des valeurs de cycla défaut
    Effet : change la cycla défaut des rues concernées.
    """

    @transaction.atomic()
    def change_cycla(rue_d, valeur):
        """
        Effet : met à valeur la cycla_défaut de toutes les arêtes de la rue.
        """
        for a in rue_d.arêtes.all():
            a.cycla_défaut=valeur
            a.save()

    


@transaction.atomic()
def met_en_clique(g, nœuds, nom, cycla_défaut=1.1, bavard=0):
    """
    Entrée : g (graphe)
             nœuds (liste d’id osm)
             nom (str)
    Effet : rajoute toutes les arêtes nécessaires pour que l’ensemble des sommets dans nœuds devienne une clique. Les longueurs sont prises comme la distance euclidienne entre les deux sommets. Le nom qui sera rentré est celui passé en arg.
    Paramètres:
        cycla_défaut (float) : cycla défaut à mettre aux arêtes créées.
    """
    cpt = 0
    for s in nœuds:
        s_d = Sommet.objects.get(id_osm=s)
        for t in nœuds:
            t_d = Sommet.objects.get(id_osm=t)
            if t!=s:
                if not Arête.objects.filter(départ__id_osm=s, arrivée__id_osm=t).exists():
                    a = Arête(
                        départ = s_d,
                        arrivée = t_d,
                        longueur = g.d_euc(s,t),
                        geom = f"{s_d.lon},{s_d.lat};{t_d.lon},{t_d.lat}",
                        cycla_défaut= cycla_défaut
                    )
                    a.save()
                    cpt+=1
    print(f"{cpt} nouvelles arêtes créées.")
    
    
def place_en_clique(g, v_d):
    """
    Effet : Transforme en clique toutes les places.
    """
    for r in Rue.objects.filter( Q(nom_complet__icontains="place") | Q(nom_complet__icontains="square"), ville=v_d):
        print(f"Mise en clique : {r}")
        met_en_clique(g, r.nœuds(), r.nom_complet)
    








    

### vieux trucs ###



# def nv(g, nom_ville):
#     return normalise_ville(g, nom_ville).nom_norm

# #code_postal_norm = {nv(v):code for v,code in TOUTES_LES_VILLES.items()}

# #Utiliser bulk_create
# #https://pmbaumgartner.github.io/blog/the-fastest-way-to-load-data-django-postgresql/

# def villes_vers_django(g):
#     """
#     Effet : réinitialise la table dijk_ville
#     """
#     Ville.objects.all().delete()
#     villes_à_créer=[]
#     for nom, code in TOUTES_LES_VILLES.items():
#         villes_à_créer.append( Ville(nom_complet=nom, nom_norm=nv(g, nom), code=code))
#     Ville.objects.bulk_create(villes_à_créer)

        
# def charge_rues(bavard=0):
#     """ 
#     Transfert le contenu du csv CHEMIN_NŒUDS_RUES dans la base.
#     Réinitialise la table Rue (dijk_rue)
#     """

#     # Vidage des tables
#     Rue.objects.all().delete()
#     #Sommet.objects.all().delete() # À cause du on_delete=models.CASCADE, ceci devrait vider les autres en même temps
    
#     rues_à_créer=[]
#     with open(CHEMIN_NŒUDS_RUES, "r") as entrée:
#         compte=0
#         nb_lignes_lues=0
#         for ligne in entrée:
#             nb_lignes_lues+=1
#             if nb_lignes_lues%100==0:
#                 print(f"ligne {nb_lignes_lues}")
#             if bavard>1:print(ligne)
#             ville_t, rue, nœuds_à_découper = ligne.strip().split(";")

#             ville=normalise_ville(ville_t)
#             ville_n = ville.nom_norm
#             ville_d = Ville.objects.get(nom_norm=ville_n) # l’objet Django. # get renvoie un seul objet, et filter plusieurs (à confirmer...)
            
#             rue_n = prétraitement_rue(rue)
#             rue_d = Rue(nom_complet=rue, nom_norm=rue_n, ville=ville_d, nœuds_à_découper=nœuds_à_découper)
#             rues_à_créer.append(rue_d)
            
#         Rue.objects.bulk_create(rues_à_créer)
            
#     print("Chargement des rues vers django fini.")



@transaction.atomic
def charge_csv_chemins(zone_t, réinit=False):
    """
    Effet : charge le csv de CHEMIN_CHEMINS dans la base. Dans celui-ci, les villes sont supposées être entre parenthèses.
    Si réinit, vide au prélable la table.
    """
    z_d = Zone.objects.get(nom=zone_t)
    if réinit:
        Chemin_d.objects.all().delete()
    with open(CHEMIN_CHEMINS) as entrée:
        à_créer=[]
        for ligne in entrée:
            print(ligne)
            AR_t, pourcentage_détour_t, étapes_t,rues_interdites_t = ligne.strip().split("|")
            p_détour = int(pourcentage_détour_t)/100.
            if AR_t=="True": AR=True
            else: AR=False
            if étapes_t: étapes_t = conversion_ligne(étapes_t)
            if rues_interdites_t: rues_interdites_t = conversion_ligne(rues_interdites_t)
            début, fin = étapes_t[:255], étapes_t[-255:]
            interdites_début, interdites_fin = rues_interdites_t[:255], rues_interdites_t[-255:]
            c_d = Chemin_d(zone=z_d, ar=AR, p_détour=p_détour, étapes_texte=étapes_t, interdites_texte=rues_interdites_t, début=début, fin = fin, interdites_début=interdites_début, interdites_fin=interdites_fin)
            c_d.sauv()


def conversion_étape(texte, bavard=0):
    """
    Entrée : texte d’une étape où la ville est entre parenthèses
    Sortie : texte d’une étape avec la ville séparée par une virgule.
    """
    # Lecture de la regexp
    e = re.compile("(^[0-9]*) *([^()]+)(\((.*)\))?")
    essai = re.findall(e, texte)
    if bavard > 1: print(f"Résultat de la regexp : {essai}")
    if len(essai) == 1:
        num, rue, _, ville = essai[0]
    elif len(essai) == 0:
        raise SyntaxError(f"adresse mal formée : {texte}")
    else:
        print(f"Avertissement : plusieurs interprétations de {texte} : {essai}.")
    num, rue, _, ville = essai[0]
    rue=rue.strip()
    ville=ville.strip()

    if not num:
        res=""
    else:
        res= f"{int(num)} "
    return res + f"{rue}, {ville}"


def conversion_ligne(ligne):
    """
    Entrée : ligne (str) étapes séparées par des ; où les villes sont entre parenthèses
    Sortie (str) : idem mais où les villes sont séparées par des virgules.
    """
    étapes = ligne.split(";")
    return ";".join(conversion_étape(é) for é in étapes)
