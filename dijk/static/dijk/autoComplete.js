//Autoriser les popover
// Ça a l’air plus compliqué en bootstrap5...
// https://getbootstrap.com/docs/5.0/components/popovers/
// $('[data-toggle="popover"]').popover();


// autocomplétion



function onSelectAutoComplète(e, ui, form, champ){
    // Lancé lors de la sélection d’un élément dans un champ autocomplété.
    // e : l’événement, ui : l’objet sélectionné
    // form : formulaire à modifier
    // Effet : ajoute un champ caché nommé {champ} avec les coords de ui
    lieu = ui.item;
    if (lieu.hasOwnProperty("lon")){
	coords = lieu.lon+","+lieu.lat;
	form.elements[champ].value = coords;
    }
}

function autoComplète(nomChamp, adresseSource, form, longMin){
    // longMin est facultatif. 3 par défaut.
    // l’élément du formulaire doit s’appeler "id_"+nomChamp, l’élément à remplir doit s’appeler "coords_"+nomChamp
    
    if (!longMin){const longMin=3;}
        $(function () {
        $("#id_"+nomChamp).autocomplete({
	        source: adresseSource,
	        minLength: longMin,
	        select: (e, ui) => onSelectAutoComplète(e, ui, form, "coords_"+nomChamp )
        });
    });
}

console.log("autoComplete.js chargé");

// $("#id_départ").autocomplete({
//     source: "{% url 'complète rue' %}",
//     minLength: 3,
//     select: (e, ui) =>
//     //(
//     // ui.item : le dico renvoyé par le serveur
//     // form = document.getElementById("recherche");
//     // lieu = ui.item;
//     // coords = lieu.lon+","+lieu.lat;
//     // form.elements["coords_départ"].value=coords;
//     //)
//     onSelectAutoComplète(e, ui, document.getElementById("recherche"), "coords_départ")    
// });

// $("#id_arrivée").autocomplete({
//     source: "{% url 'complète rue' %}",
//     minLength: 3,
//     select: (e, ui) =>
//     onSelectAutoComplète(e, ui, document.getElementById("recherche"), "coords_arrivée")
// });

// $("#rues_interdites").autocomplete({
//     source: "{% url 'complète rue' %}",
//     minLength: 4,
// });

// $("#étapes").autocomplete({
//     source: "{% url 'complète rue' %}",
//     minLength: 4,
// });	      

