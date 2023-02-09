import * as Pll from "./pour_leaflet.js";

// Fonctions diverses, qui ne requièrent pas de bib externe.

export function dernierÉLém(tab){
    return tab[tab.length-1];
}


// Lecture d’un json représantant un array avec gestion du cas ""
export function tab_of_json(texte){
    if (texte){
	return JSON.parse(texte);
    }else{
	return [];
    }
}



// Rajoute un champ caché avec la géoloc
export function init_géoLoc(form){
    //if (navigator.geolocalisation){
	// form_recherche = document.getElementById("recherche");
	addHidden(form, "localisation", (0.,0.));
	navigator.geolocation.getCurrentPosition(
	    pos => àLaGéoloc(pos, form),
	    () => pasDeGéoloc(form)
	);
    //}
}




    // Supprime la chekbox « partir de ma position »
export function pasDeGéoloc(form){
    console.log("Pas de géoloc");
    form.getElementsByClassName("checkbox")[0].remove();
}







export function addHidden(theForm, key, value) {
    // Create a hidden input element, and append it to the form:
    console.log(`Je crée un hidden. this : ${this}, form: ${theForm}, key:${key}`);
    var input = document.createElement('input');
    input.type = 'hidden';
    input.name = key; // 'the key/name of the attribute/field that is sent to the server
    input.value = value;
    input.id = key;
    theForm.appendChild(input);
}
