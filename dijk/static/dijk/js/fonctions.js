
// Fonctions diverses, qui ne requierent pas de bib externe.

function voir_si_géoLoc(){
    //if (navigator.geolocalisation){
	form_recherche = document.getElementById("recherche");
	addHidden(form_recherche, "localisation", (0.,0.));
	navigator.geolocation.getCurrentPosition(
	    pos => àLaGéoloc(pos, form_recherche),
	    () => pasDeGéoloc(form_recherche)
	);
    //}
}


function àLaGéoloc(pos, form){
    // Met à jour le champ "localisation" du form
    texte = texte_of_latLng(pos);
    console.log("Position obtenue : " + texte );
    form.elements["localisation"].value = texte;
}


function pasDeGéoloc(form){
    // Supprime la chekbox « partir de ma position »
    console.log("Pas de géoloc");
    form_recherche.getElementsByClassName("checkbox")[0].remove();
}






////////////////////////////////////
// Gestion des clics sur la carte //
////////////////////////////////////







// Ordre des events handler:
// https://stackoverflow.com/questions/2360655/jquery-event-handlers-always-execute-in-order-they-were-bound-any-way-around-t
// [name] is the name of the event "click", "mouseover", ..
// same as you'd pass it to bind()
// [fn] is the handler function
// $.fn.bindFirst = function(name, fn) {
//     // bind as you normally would
//     // don't want to miss out on any jQuery magic
//     this.on(name, fn);

//     // Thanks to a comment by @Martin, adding support for
//     // namespaced events too.
//     this.each(function() {
//         var handlers = $._data(this, 'events')[name.split('.')[0]];
//         // take out the handler we just inserted from the end
//         var handler = handlers.pop();
//         // move it at the beginning
//         handlers.splice(0, 0, handler);
//     });
// };






function addHidden(theForm, key, value) {
    // Create a hidden input element, and append it to the form:
    console.log(`Je crée un hidden. this : ${this}, form: ${theForm}, key:${key}`);
    var input = document.createElement('input');
    input.type = 'hidden';
    input.name = key; // 'the key/name of the attribute/field that is sent to the server
    input.value = value;
    input.id = key;
    theForm.appendChild(input);
}
