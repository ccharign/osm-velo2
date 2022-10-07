# -*- coding:utf-8 -*-

#from petites_fonctions import recherche_inversée
from lecture_adresse.normalisation import normalise_rue, normalise_ville
import re
import xml.etree.ElementTree as xml
from params import CHEMIN_RUE_NUM_COORDS

    
#################### Récupération des numéros de rues ####################
    

def coords_of_nœud_xml(c):
    return float(c.attrib["lat"]), float(c.attrib["lon"])


def int_of_num(n, bavard=0):
    """ Entrée : une chaîne représentant un numéro de rue.
        Sortie : ce numéro sous forme d’entier. Un éventuel "bis" ou "ter" sera supprimé."""
    e = re.compile("\ *([0-9]*)[^0-9]*$")
    if bavard: print(n, re.findall(e, n))
    num = re.findall(e, n)[0]
    return int(num)


def normalise_ville(ville):
    """En minuscule avec capitale majuscule."""
    return ville.title()


def commune_of_adresse(adr):
    """ Entrée : adresse renvoyée par Nominatim.reverse.
        Sortie : la commune (on espère)"""
    à_essayer = ["city", "village", "town"]
    for clef in à_essayer:
        try:
            return adr[clef]
        except KeyError :
            pass



def extrait_rue_num_coords(chemin="données_inutiles/pau.osm", bavard=0):
    """ Entrée : fichier xml d’openstreetmap (pas la version élaguée)
        Effet : crée à l’adresse CHEMIN_RUE_NUM_COORDS un fichier csv associant à chaque rue la list des (numéro connu, coords correspondantes)"""
    

    print("Chargement du xml")
    a = xml.parse("données_inutiles/pau.osm").getroot()
    
    print("Extraction des adresses connues")
    
    def ajoute_dans_res(villerue, val):
        if villerue not in res:
            res[villerue] = []
        res[villerue].append(val)
        
    res = {}
    nums_seuls = []
    for c in a:
        if c.tag == "node":  # Sinon on n’a pas les coords.
            # Voyons si nous disposons d’une adresse pour ce nœud.
            num, rue, ville = None, None, None
            for d in c:
                if d.tag == "tag" and d.attrib["k"] == "addr:housenumber":
                    num = d.attrib["v"]
                if d.tag == "tag" and d.attrib["k"] == "addr:street":
                    rue = d.attrib["v"]
                if d.tag == "tag" and d.attrib["k"] == "addr:city":
                    ville = normalise_ville(d.attrib["v"])
            if num is not None:
                try:
                    num = int_of_num(num)
                    if rue is not None and num is not None and ville is not None:
                        ajoute_dans_res(ville+";"+rue, (num, float(c.attrib["lat"]), float(c.attrib["lon"])))
                    else:
                        # juste un numéro
                        nums_seuls.append( (c.attrib["id"], num, float(c.attrib["lat"]), float(c.attrib["lon"])) )
                except Exception as e:  # pb dans le xml
                    print(f"Pb à  la lecture du nœud {num, rue, ville}  : {e}.\n Nœud abandonné.")
            


    print("Recherche des rues des numéros orphelins")
    print("Recherche inversée Nominatim limitée à une recherche par seconde...")
    nb=0
    for id_node, num, lat, lon in nums_seuls:
        try:
            adresse = recherche_inversée((lat, lon), bavard=bavard-1).raw["address"]
            print(adresse)
            if bavard>0: print(adresse)
            villerue = normalise_ville( commune_of_adresse(adresse)) + ";" + normalise_rue( adresse["road"] )
            ajoute_dans_res(villerue, (num, lat, lon))
            nb+=1
        except Exception as e:
            print(f"Erreur pour {id_node, num, lat, lon} : {e}")
    print(f"{nb} adresses collectées")
        
    print(f"Écriture du fichier {CHEMIN_RUE_NUM_COORDS}")
    sortie = open(CHEMIN_RUE_NUM_COORDS, "w", encoding="utf-8")
    for villerue, l in res.items():
        if len(l) > 1:  # Une seule adresse dans la rue ça ne permet pas d’interpoler.
            l_pair = [x for x in l if x[0]%2 == 0]
            l_impair = [x for x in l if x[0]%2 != 0]
            
            def à_écrire(ll):
                ll.sort()
                ll = [ x for i,x in enumerate(ll) if i==0 or x[0]!=ll[i-1][0] ]  # dédoublonnage des numéros
                if bavard: print(à_écrire)
                return "|".join([str(c)[1:-1] for c in ll])
                
            sortie.write(f"{villerue}:{';'.join([à_écrire(l_pair), à_écrire(l_impair)])}\n")
    sortie.close()
    #return nums_seuls
