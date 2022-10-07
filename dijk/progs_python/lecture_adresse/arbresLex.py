# -*- coding:utf-8 -*-

### Implantation des arbres lexicographiques ###

def prefixed(lettre, l):
    """
    Entrées : 
        - lettre, un caractère
        - ll (str iterable)
    Sortie (str set): liste des lettre+m pour m dans l.
    """
    return set(lettre+mot for mot in l)


class ArbreLex():
    """
    Attributs:
        term (bool), indique si la racine est terminale
        fils (str -> ArbreLex), dictionnaire lettre -> fils
    """
    
    def __init__(self):
        """ Renvoie un arbre vide"""
        self.fils = {}
        self.term = False
    
    
    def tous_les_mots(self, n_max=float("inf")):
        """
        Renvoie la liste des mots de l’arbre
        n_max : nb max de résultats à renvoyer. Si le nb de mots dans l’arbre est > n_max, ceci renvoie [].
        """
        if n_max<=0:
            return []
        else:
            if self.term:
                res=[""]
            else:
                res=[]

            for x, a in self.fils.items():
                mots_dans_fils = a.tous_les_mots(n_max=n_max-len(res))
                if len(mots_dans_fils)==0:
                    # nb max de mots dépassé.
                    return []
                else:
                    res.extend(
                        map(lambda m:x+m, mots_dans_fils)
                    )
            return res
    
    
    def __len__(self):
        if self.term:
            res=1
        else:
            res=0
        return res+sum(len(a) for a in self.fils.values())

    
    def insère(self, mot):
        """
        Entrée : mot (str)
        Effet : insère mot dans l’arbre.
        """

        if mot == "":
            self.term = True
        else:
            if mot[0] in self.fils:
                self.fils[mot[0]].insère(mot[1:])
            else:
                self.fils[mot[0]] = ArbreLex()
                self.fils[mot[0]].insère(mot[1:])

                
    def rajoute(self, arbre):
        """
        Effet : ajoute le contenu de arbre dans self.
        """

        if arbre.term:
            self.term=True

        for lettre, fils_a in arbre.fils.items():
            if lettre in self.fils:
                self.fils[lettre].rajoute(fils_a)
            else:
                self.fils[lettre] = fils_a

        
    @classmethod
    def of_iterable(cls, l):
        """
        Entrée : l (str iterable)
        Sortie : l’arbre contenant les éléments de l.
        """
        res = cls()
        for mot in l:
            res.insère(mot)
        return res

    
    def __contains__(self, mot):
        if mot=="":
            return self.term
        else:
            return mot[0] in self.fils and  mot[1:] in self.fils[mot[0]]


    def contientPresque(self, mot, dmax):
        """
        Entrées : mot (str)
                  dmax (int), distance max (de Levenstein) à laquelle chercher.
        Sortie : indique si l’arbre contient un élément à distance dmax ou moins de mot.
        """

        if dmax == 0:
            return mot in self
        else:
            if len(mot)==0:
                #Seule possibilité : ajouter des lettres
                for lettre, f in self.fils.items():
                    if f.contientPresque(mot, dmax-1):
                        return True
                    
            else:
                # Premier essai : la bonne première lettre
                if mot[0] in self.fils:
                    if self.fils[mot[0]].contientPresque(mot[1:], dmax):
                        return True

                # Deuxième essai : supprimant une lettre
                if self.contientPresque(mot[1:], dmax-1) :
                    return True

                # Troisième essai : en changeant une lettre ou en ajoutant une
                for lettre, f in self.fils.items():
                    if lettre!=mot[0] and f.contientPresque(mot[1:], dmax-1) or f.contientPresque(mot, dmax-1):
                        return True

                return False


            
    def mots_les_plus_proches(self, mot, d_actuelle=0, d_max = float("inf")):
        """ Renvoie le couple (set des mots à distance minimale de mot, la distance minimale elle-même).
        Renvoie set() si aucun mot à distance <= dmax.
        """

        def rassemble_possibs(p1, p2):
            """ p1 et p2 sont des couples (set d’éléments de l’arbre, distance à mot)"""
            l1, d1 = p1
            l2, d2 = p2
            if d1==d2:
                return (l1.union(l2), d1)
            elif d1<d2:
                return p1
            else:
                return p2

        def prefixed(lettre, possib):
            """ possib est un couple (mots, distance).
            Renvoie le couple obtenu en mettant lettre devant chacun des mots.
            """
            mots, d = possib
            return (set(lettre+m for m in mots), d)
        
        
        if d_max == d_actuelle:
            # Seule possibilité : le mot lui-même
            if mot in self: return set([mot]), d_actuelle
            else: return set([]), float("inf")
            
        else:
            res = set([]), float("inf")
            if len(mot)==0:
                if self.term:
                    return (set([""]), d_actuelle)
                else:
                    #Seule possibilité : ajouter des lettres
                    for lettre, f in self.fils.items():
                        res = rassemble_possibs(
                            res,
                            prefixed(lettre, f.mots_les_plus_proches(mot[1:], d_actuelle=d_actuelle+1, d_max=d_max))
                        )
                    return res
                    
            else:
                # Premier essai : la bonne première lettre
                if mot[0] in self.fils:
                    res = rassemble_possibs(
                        res,
                        prefixed(mot[0], self.fils[mot[0]].mots_les_plus_proches(mot[1:], d_actuelle=d_actuelle, d_max=d_max))
                    )

                # Deuxième essai : supprimant une lettre
                res = rassemble_possibs(res,  self.mots_les_plus_proches(mot[1:], d_actuelle=d_actuelle+1, d_max=d_max))

                # Troisième essai : en changeant une lettre ou en ajoutant une
                for lettre, f in self.fils.items():
                    res = rassemble_possibs(
                        res,
                        prefixed(lettre, f.mots_les_plus_proches(mot, d_actuelle=d_actuelle+1, d_max=d_max))
                        )
                    if lettre != mot[0]:
                        res = rassemble_possibs(
                            res,
                            prefixed(lettre, f.mots_les_plus_proches(mot[1:], d_actuelle=d_actuelle+1, d_max=d_max))
                        )
                                            
                return res
    
    
    def complétion(self, mot:str, tol=float("inf"), n_max_rés=float("inf")):
        """
        Sortie (str list list) : tableau t->liste des mots commençant par mot avec t fautes de frappe.
        Ce tableau est vide si le nb de rés même avec tolérance 0 dépasse n_max_rés
        Précisément, la longueur du rés -1 est le plus grand t∈[|0, tol[| tel que le nb de résultat pour une tolérance ⩽ t est ⩽ n_max_rés.

        Paramètres:
            - tol (int ou infini) : nb de fautes de frappe max à autoriser. Si tol<0, [] est renvoyé.
            - n_max_rés (int ou infini), nb max de résultats à renvoyer. 
               tol sera automatiquement abaissé pour que le nb de rés soit <= n_max_rés.
        
        """

        res = [set() for _ in range(tol+1)]
        nb_rés=0
        
        if tol<0 or nb_rés<0: return [] # Cas de base utile dans les appels récursifs.
        
        elif len(mot)==0:
            res[0] = self.tous_les_mots(n_max=n_max_rés)
            return  res
        
        else:
            
            def ajoute_et_tronque_res(à_rajouter):
                """
                Entrée : à_rajouter (str list list)
                Précondition : len(à_rajouter)<=len(res)
                Effet : Ajoute dans res les éléments de à_rajouter. De plus les dernières cases de res sont supprimées afin que la somme des longueurs de ses éléments devienne <= n_max.
                Sortie : nb d'éléments dans res après l'opération.
                """
                n_tot=0
                i=0
                tout = set() # Union de toutes les cases de res déjà traitées. (Pour éviter qu’un mot arrive dans plusieurs cases.)
                while i<len(res):
                    # invariant de boucle : n_tot==\sum_{k=0}^{i-1} len(res[k])
                    à_rajouter_sans_doublon = [m for m in à_rajouter[i] if m not in tout]
                    if n_tot+len(res[i])+len(à_rajouter_sans_doublon) > n_max_rés:
                        res.pop()
                    else:
                        res[i].update(à_rajouter_sans_doublon)
                        tout.update(res[i])
                        n_tot+=len(res[i])
                        i+=1
                return n_tot

            
            # essai avec la bonne lettre
            if mot[0] in self.fils:
                res = [ prefixed(mot[0], l) for l in self.fils[mot[0]].complétion(mot[1:], tol=tol, n_max_rés=n_max_rés)]
                nb_rés = sum(len(r) for r in res)
                
            # Listes des autres essais : avec une faute de frappe.
            essais_à_faire=[ # syntaxe : (arbre où chercher, mot, fonction à appliquer à la matrice de mots récupérée)
                (self, mot[1:], lambda x:x), # en supprimant une lettre
                # Attention au « Python late closure binding » ci-dessous !!!
                *((f, mot[1:], lambda l, lettre=lettre:prefixed(lettre, l)) for (lettre, f) in self.fils.items() if lettre!=mot[0]), # En échangeant une lettre
                *((f, mot, lambda l, lettre=lettre:prefixed(lettre, l) ) for (lettre, f) in self.fils.items()) # En ajoutant une lettre
                ]
            
            # Parcours de la liste des essais à faire.
            for (a, m, fonction) in essais_à_faire:
                n_tol = len(res)-1 # nb max de fautes de frappe à garder compte tenu du n_max_rés.
                essai = [ fonction(l) for l in  a.complétion(m, tol=n_tol-1, n_max_rés=n_max_rés-nb_rés) ]
                nb_rés =  ajoute_et_tronque_res([set()] + essai)
                    
            return res
        
        
        
    
    def sauv(self, chemin):
        """
        Enregistre l’arbre dans le fichier spécifié.
        Chaque ligne contient le booléen term puis les lettre étiquettant les fils d’un certain nœuds.
        Les nœuds sont enregistrés selon un parcours en profondeur préfixe.
        """
        with open(chemin,"w") as sortie:
            def aux(a):
                fils = list(a.fils.items()) # Cette étape pour m’assurer que les fils seront traité dans le même ordre dans les deux opérations à suivre. Sans doute inutile...
                if len(fils)==0 and not a.term:
                    raise ValueError(f"Feuille non terminale dans mon arbre lexicographique.")
                ligne = str(int(a.term)) + "".join(lettre for lettre,_ in fils)
                sortie.write(ligne+"\n")
                for _, f in fils:
                    aux(f)
            aux(self)


    @classmethod
    def of_fichier(cls, chemin):
        """
        Renvoie l’arbre enregistré dans le fichier indiqué.
        """
        with open(chemin) as entrée:
            def aux():
                res = cls()
                ligne=entrée.readline().strip("\n")
                if len(ligne)==1:#C’est une feuille
                    res.term=True
                    return res
                else:
                    for lettre in ligne[1:]:
                        res.fils[lettre]=aux()
                    res.term=bool(int(ligne[0]))
                    return res
            return aux()
                
                
test = ArbreLex.of_iterable(["bal", "bla", "baffe", "bar", "art", "are", "as"])
test2 = ArbreLex.of_iterable([ "bla", "as"])
test3=ArbreLex.of_iterable(["truc", "base", "a","bague"])
