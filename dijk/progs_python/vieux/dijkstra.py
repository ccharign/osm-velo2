#! usr/bin/python3
# -*- coding:utf-8 -*-

from petites_fonctions import distance_euc, deuxConséc  # pour A*
from heapq import heappush, heappop  # pour faire du type List une structure de tas-min
import copy

class PasDeChemin(Exception):
    pass



##############################################################################
############################## Dijkstra de base ##############################
##############################################################################


def chemin(g, départ, arrivée, p_détour):
    """  Nécessite une classe graphe avec méthode « voisins » qui prend un sommet s et le pourcentage de détour p_détour et renvoie un itérable de (point, longueur de l'arrête corrigée)"""
    assert p_détour < 10, f"J'ai reçu p_détour = {p_détour}. As-tu pensé à diviser par 100 le pourcentage ?"
    dist = {départ: 0.}  #dist[s] contient l'estimation actuelle de d(départ, i) si s est gris, et la vraie valeur si s est noir.
    pred = {départ: -1}
    àVisiter =[(0, départ)]  # tas des sommets à visiter. Doublons autorisés.

    fini = False
    while len(àVisiter) > 0 and not fini:
        _, s = heappop(àVisiter)  # dist[s] == d(départ,s) d'après la démo du cours.
        if s == arrivée: fini = True
        else:
            for t, l in g.voisins(s, p_détour):
                if t not in dist or dist[s]+l < dist[t]:  # passer par s vaut le coup
                    dist[t] = dist[s]+l
                    heappush(àVisiter, (dist[t], t))
                    pred[t] = s
                    
    
    ## reconstruction du chemin
    if arrivée in dist:
        chemin = [arrivée]
        s = arrivée
        while s != départ:
            s = pred[s]
            chemin.append(s)
        chemin.reverse()
        return chemin
    else:
        raise PasDeChemin(f"Pas de chemin trouvé de {départ} à {arrivée}")

    

def chemin_étapes(g, c):
    """ Entrée : g : graphe
                 c : objet de la classe chemin
        Sortie : chemin passant par ces points
    """
    s = c.départ()
    res = []
    for t in c.étapes[1:]:
        res.extend(chemin(g, s, t, c.p_détour)[:-1])
        s = t
    res.append(s)
    return res




#######################################################################
########## En prenant pour étapes des *ensembles* de sommets ##########
#######################################################################


def vers_une_étape(g, départ, arrivée, p_détour, dist, pred, première_étape):
    """
    Entrées : g, graphe avec méthode voisins qui prend un sommet et un p_détour et qui renvoie une liste de (voisin, longueur de l’arête)
              départ et arrivée, ensembles de sommets
              p_détour ∈ [0,1]
              dist : dictionnaire donnant la distance initiale à prendre pour chaque élément de départ (utile quand départ sera juste une étape intermédiaire)
              pred : dictionnaire des prédécesseurs déjà calculés.
              première_étape (bool) : indique si on en est à la première étape du trajet final.

    Effet : pred et dist sont remplis de manière à fournir tous les plus courts chemins d’un sommet de départ vers un sommet d’arrivée, en prenant compte des bonus/malus liés aux valeurs initiales de dist.
    Sauf si première_étape, on impose de passer par au moins une arête de départ.
    """

    àVisiter = []
    for (s, d) in dist.items():
        heappush(àVisiter, (d, s))

    fini = False
    sommetsFinalsTraités = set({})
    
    while len(àVisiter) > 0 and not fini:
        
        _, s = heappop(àVisiter)
        
        if s in arrivée:
            sommetsFinalsTraités.add(s)
            fini = len(sommetsFinalsTraités) == len(arrivée)
            
        for t, l in g.voisins(s, p_détour):
            #if t in départ or s not in départ or pred[s] not in départ or première_étape : # Pour forcer à passer par au moins une arête de départ (sauf pour la première étape da trajet).
                if t not in dist or dist[s]+l < dist[t]:  # passer par s vaut le coup
                    dist[t] = dist[s]+l
                    heappush(àVisiter, (dist[t], t))
                    pred[t] = s


def reconstruction(chemin, pred, départ):
    """ Entrées : chemin, la fin du chemin retourné. chemin[0] est le point d’arrivée final, chemin[-1] est un sommet dans l’arrivée de cette étape.
                  départ, sommets de départ de l’étape (structure permettant un «in»)
                  arrivée, sommets d’arrivée de l’étape. Doit être itérable
                  dist, le dictionnaire sommet -> dist min à un sommet de départ, créé par Dijkstra.
        Effet : remplit chemin avec un plus court trajet de chemin[-1] vers un sommet de départ.
    """  
    s = chemin[-1]
    while s not in départ:
        s = pred[s]
        chemin.append(s)


def chemin_étapes_ensembles(g, c):
    """
   
    Entrées : départ et arrivée, deux sommets
              c, instance de Chemin (c.étapes est une liste d’Étapes. Pour toute étape é, é.nœuds est une liste de nœuds.)
    Sortie : plus court chemin d’un sommet de étapes[0] vers un sommet de étapes[-1] qui passe par au moins une arête de chaque étape intéremédiaire.
    """
    
    étapes = c.étapes
    départ = étapes[0].nœuds
    arrivée = étapes[-1].nœuds
    
    dist = {s: 0. for s in départ}
    pred = {s: -1 for s in départ}
    preds_précs = []

    for i in range(1, len(étapes)):
        vers_une_étape(g, étapes[i-1].nœuds, étapes[i].nœuds, c.p_détour, dist, pred, i==1)
        preds_précs.append(copy.deepcopy(pred))  # pour la reconstruction finale
        # preds_précs[k] contient les données pour aller de étapes[k] vers étapes[k+1], k==i-1
        dist = {s: d for (s, d) in dist.items() if s in étapes[i].nœuds}  # On efface tout sauf les sommets de l’étape qu’on vient d’atteindre

    if all(s not in dist for s in arrivée):
        raise PasDeChemin(f"Pas de chemin trouvé pour {c} (sommets non atteint : {e}).")
    else:
        _, fin = min(((dist[s], s) for s in arrivée))  # pb si un des sommets d’arrivée est ateint mais pas tous. N'arrive que si arrivée n’est pas connexe...
        chemin = [fin]
        for i in range(len(étapes)-1, 0, -1):
            reconstruction(chemin, preds_précs[i-1], étapes[i-1].nœuds)
        chemin.reverse()
        return chemin

        


    
    ############################################################
    ########## Troisième version : les étapes sont des ensembles, on les relie par des plus court chemins, et on relie ces plus court chemins entre eux (a priori dans l'ensemble)##########
    # plus utilisée : je l’ai renommé en chemin_étapes_ensembles2
    ############################################################

    
def chemin_entre_deux_ensembles(g, départ, arrivée, p_détour):
    
    """
    Entrées : g graphe
              départ et arrivée instances de Étape.
    Sortie : plus court chemin d'un sommet de départ vers un sommet d'arrivée
    """
    
    assert p_détour < 10, f"J'ai reçu p_détour = {p_détour}. Avez-vous pensé à diviser par 100 le pourcentage ?"
    dist = {s: 0. for s in départ.nœuds}  #dist[s] contient l'estimation actuelle de d(départ, i) si s est gris, et la vraie valeur si s est noir.
    pred = {s: -1 for s in départ.nœuds}
    àVisiter =[(0., s) for s in départ.nœuds]  # tas des sommets à visiter. Doublons autorisés.

    fini = False
    while len(àVisiter) > 0 and not fini:
        _, s = heappop(àVisiter)  # dist[s] == d(départ,s) d'après la démo du cours.
        if s in arrivée.nœuds:
            nœud_final = s
            fini = True
        else:
            for t, l in g.voisins(s, p_détour):
                if t not in dist or dist[s]+l < dist[t]:  # passer par s vaut le coup
                    dist[t] = dist[s]+l
                    heappush(àVisiter, (dist[t], t))
                    pred[t] = s
                    
    
    ## reconstruction du chemin
    if fini:
        s = nœud_final
        chemin = [s]
        while s not in départ.nœuds:
            s = pred[s]
            chemin.append(s)
        chemin.reverse()
        return chemin
    else:
        raise PasDeChemin(f"Pas de chemin trouvé de {départ} à {arrivée}")



def chemin_étapes_ensembles2(g, c):
    """
    Entrées : g, graphe
              c, instance de Chemin
    Sortie : chemin obtenu un reliant les étapes de c par des plus court chemin, puis en reliant entre eux ces morceaux par des plus courts chemins dans g (en pratique ces morceaux devraient rester au sein de l'étape).
    """
    
    tronçons = []
    for é, és in deuxConséc(c.étapes):
        tronçons.append(chemin_entre_deux_ensembles(g, é, és, c.p_détour))

    res=[]
    for t1, t2 in deuxConséc(tronçons):
        res.extend(t1)
        res.extend(chemin(g, t1[-1], t2[0], c.p_détour))
    res.extend(tronçons[-1])

    return res
