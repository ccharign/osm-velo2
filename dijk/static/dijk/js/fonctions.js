import * as Pll from "./pour_leaflet.js";

// Fonctions diverses, qui ne requièrent pas de bib externe.


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


// Met à jour le champ "localisation" du form
export function àLaGéoloc(pos, form){
    const texte = Pll.texte_of_latLng(pos);
    console.log("Position obtenue : " + texte );
    form.elements["localisation"].value = texte;
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
