// Fonction pour la gestion du formulaire de recherche.


export function récupJson(texte){
    if (texte){
	return JSON.parse(texte);
    }else{
	return [];
    }
}


/**
   Transforme les étapes en json et enregistre le tout dans le form, champ toutes_les_étapes puis soumet le form
*/
export function envoieLeForm(form, étapes){
    form.toutes_les_étapes.value = JSON.stringify(
	étapes.map(
	    o =>{
		if ("objet_initial" in o){return o.objet_initial;}
		else {return o;}
	    }
	)
    );
    form.submit();
}
