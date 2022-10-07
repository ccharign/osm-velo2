# -*- coding:utf-8 -*-

############## Lire tout le graphe pour en extraire les nœuds des rues ###############

#from params import CHEMIN_NŒUDS_RUES
from lecture_adresse.normalisation import normalise_rue, normalise_ville, prétraitement_rue
from petites_fonctions import LOG
D_MAX_SUITE_RUE = 10  # Nombre max d’arêtes où on va chercher pour trouver la suite d’une rue.


def est_sur_rueville(g, s, rue, ville):
    """ Indique si le sommet s est sur la rue et la ville indiquées.
    Rappel : il peut y avoir plusieurs rues et villes associées à une arête. rue_dune_arête et ville_dune_arête renvoient un tuple (ou liste)"""
    villes = g.villes_dun_sommet(s)
    for t in g.voisins_nus(s):
        rues = g.rue_dune_arête(s, t)
        if rues is not None and rue in rues and ville in villes: return True
    return False


def prochaine_sphère(g, sph, rue, rue_n, ville, déjàVu, boule, dmax):
    """ sph est une sphère centrée en s.
        boule est la boule fermée correspondante.
        Renvoie les nœuds de rue qui sont sur la première sphère centrée en s qui contienne un nœud de rue. Recherche effectuée en partant de sph et en augmentant le rayon de 1 en 1 au plus dmax fois.
    La distance utilisée est le nombre d’arêtes."""
    if dmax==0:
        return []
    else:
        fini = False
        sph_suivante = []
        res_éventuel = []
        for t in sph:
            for u in g.voisins_nus(t):
                if u not in boule:
                    if est_sur_rueville(g, u, rue, ville) and u not in déjàVu[ville][rue_n]:
                        fini = True
                        res_éventuel.append(u)
                    sph_suivante.append(u)
                    boule.add(u)
        if not fini:
            return prochaine_sphère(g, sph_suivante, rue, rue_n, ville, déjàVu, boule, dmax-1)
        else:
            return res_éventuel
                



def extrait_nœuds_des_rues(g, bavard=0):
    """
    Sortie : (dictionnaire ville -> rue_n -> (rue, liste nœuds),
              la même pour les places piétonnes)
    La recherche est faite par des parcours de graphe pour avoir les sommets autant que possible dans l’ordre topologique.
    Grosse complication presque gratuite oui, c’était pour le sport.
    La liste des place piétonne est vue de la transformation d’icelles en cliques.
    """
    
    déjàVu = {} # dico (ville -> nom de rue -> set de nœuds). Ne sert que pour le cas d’une rue qui boucle.
    res = {} # dico (ville -> nom de rue -> liste des nœuds dans un ordre topologique )
    places_piétonnes = {}

    
    def suivre_rue(s, ville, rue, rue_n):
        """
        Entrées :
            s (int), sommet actuel
            rue (str), nom de la rue à suivre 
            rue_n (str), nom de la rue passé par prétraitement_rue
        Effet : remplit déjàVu[ville][rue] ainsi que res[ville][rue_n]
        """
        assert prétraitement_rue(rue_n) == rue_n, f"Rue non normalisée : {rue} (rue_n)"
        # Dans le cas d’une rue qui fourche on aura une branche après l’autre (parcours en profondeur de la rue).
        for t in prochaine_sphère(g, [s], rue, rue_n, ville, déjàVu, set([s]), D_MAX_SUITE_RUE): # Au cas où la rue serait découpées en plusieurs morceaux dans le graphe. Dans le cas basique, prochaine_sphère renvoie deux sommets, l’un d’eux étant sprec.
            if t not in déjàVu[ville][rue_n]:
                res[ville][rue_n][1].append(t)
                déjàVu[ville][rue_n].add(t)
                suivre_rue(t, ville, rue, rue_n)

    def partir_dune_arête(s, t, ville, rue, rue_n):
        """ 
        Précondition : s et t ont été marqués déjà vus et mis dans res.
        Lance suivre_rue dans le sens (s,t) puis dans le sens (t,s).
        """
        assert prétraitement_rue(rue_n) == rue_n, f"Rue non normalisée : {rue} (rue_n=={rue_n}, prétraitement_rue(rue_n)=={prétraitement_rue(rue_n)})"
        suivre_rue(s, ville, rue, rue_n)
        res[ville][rue_n][1].reverse()
        suivre_rue(t, ville, rue, rue_n)

    # def est_place_piétonne(s,t,nom):
    #     if "place" in nom.lower():
    #         for a in g.multidigraphe[s][t].values():
    #             if a.get("name")==nom and a.get("highway")=="pedestrian":
    #                 print(f"place piétonne : {nom}")
    #                 return True
    #     return False
                

    gx = g.multidigraphe

    for s in gx:
        villes = g.villes_dun_sommet(s, bavard=bavard-1)
        for ville in villes :
            if ville not in déjàVu:
                print(f"Nouvelle ville rencontrée : {ville}")
                déjàVu[ville] = {}
                res[ville] = {}
                places_piétonnes[ville]={}
            for t, arêtes in gx[s].items():
                if t == 3145210257:
                    print(f"Trouvé le nœud 3145210257. arêtes = {arêtes} s = {s} ")
                    input("presser une touche")
                    
                for a in arêtes.values():
                    rues = a.get("name", [])
                    if not isinstance(rues, list):
                        rues=[rues]
                    for rue in rues:
                        rue_n = prétraitement_rue(rue)
                        if "place" in rue_n and a.get("highway")=="pedestrian":
                            p_piétonne=True
                        else:
                            p_piétonne=False

                        #rues = g.rue_dune_arête(s, t)
                        #for rue, p_piétonne in rues:

                        if rue_n=="place georges clemenceau":
                            print(f"Place Clemenceau : {s, t}, p_piétonne={p_piétonne}")
                        if p_piétonne:
                            if rue_n not in places_piétonnes[ville]:
                                places_piétonnes[ville][rue_n]=set()
                            places_piétonnes[ville][rue_n].update([s,t])

                        if rue_n not in res[ville]:
                            #print(f"Nouvelle rue : {rue}, normalisée en {rue_n}")
                            res[ville][rue_n] = (rue, [t, s])
                            déjàVu[ville][rue_n] = set((s, t))
                            partir_dune_arête(s, t, ville, rue, rue_n)
                        elif s not in déjàVu[ville][rue_n] or t not in déjàVu[ville][rue_n]:  # Cas d’un nouveau tronçon d’une ancienne rue
                            res[ville][rue_n][1].extend((t, s))
                            déjàVu[ville][rue_n].update((s, t))
                            partir_dune_arête(s,t,ville,rue, rue_n)
                            LOG(f"Nouveau tronçon de {rue} à {ville}. Nœuds trouvés : {res[ville][rue_n]}", bavard=bavard-1)
    return res, places_piétonnes


def sortie_csv(g, bavard=0):
    """ 
    Met le dictionnaire ville -> rue -> nœuds dans le csv situé à CHEMIN_NŒUDS_RUES
    Structure d’une ligne : ville;rue;nœuds séparés par virgule.
    """
    res = extrait_nœuds_des_rues(g, bavard=bavard)
    print(f"Enregistrement des nœuds des rues dans {CHEMIN_NŒUDS_RUES}")
    if bavard>0:
        print(f"{sum( sum(len(v) for _,v in d.items() ) for _,d in res.items())} nœuds trouvés.")
    with open(CHEMIN_NŒUDS_RUES, "w", encoding="utf-8") as sortie:
        for ville, d in res.items():
            for rue, nœuds in d.items():
                ligne = f"{ville};{rue};{','.join(map(str,nœuds))}\n"
                sortie.write(ligne)

                
def charge_csv(g):
    """ 
    Charge le dictionnaire depuis le csv et le met dans l’attribut nœuds du graphe g.
    Les clefs (ville et rue) sont traitées via les fonctions de normalisation de lecture_adresse.normalisation.
    """
    with open(CHEMIN_NŒUDS_RUES, "r", encoding="utf-8") as entrée:
        dico_ville_norm = {}
        for ligne in entrée:
            ville, rue, nœuds_à_découper = ligne.strip().split(";")
            if ville in dico_ville_norm:
                ville_n = dico_ville_norm[ville]
            else:
                ville = normalise_ville(ville)
                ville_n=ville.nom_norm
                dico_ville_norm[ville]=ville_n
            rue = prétraitement_rue(rue) # Il ne devrait pas y avoir de faute de frappe dans le csv : je saute la recherche dans l’arbre lex.
            nœuds = set(map(int, nœuds_à_découper.split(",")))
            if ville_n not in g.g.nœuds : g.g.nœuds[ville_n]={}
            g.g.nœuds[ville_n][rue] = nœuds
    print("Chargement de la liste des nœuds de chaque rue finie.")
            
