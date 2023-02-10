// Fonction pour la gestion du formulaire de recherche.


export function récupJson(texte){
    if (texte){
	return JSON.parse(texte);
    }else{
	return [];
    }
}

// Remplit le champ toutes_les_étapes du form avec le json de étapes
export function màjToutes_les_étapes(form, étapes){
    form.toutes_les_étapes.value = JSON.stringify(
	étapes.map(
	    o => {return o.versDjango();}
	)
    );
}

/**
   Transforme les étapes en json et enregistre le tout dans le form, champ toutes_les_étapes puis soumet le form
*/
export function envoieLeForm(form, étapes){
    màjToutes_les_étapes(form, étapes);
    form.submit();
}
