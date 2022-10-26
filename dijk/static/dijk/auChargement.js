//Autoriser les popover
$('[data-toggle="popover"]').popover();


// autocomplétion

$("#id_départ").autocomplete({
    source: "{% url 'complète rue' %}",
    minLength: 3,
    select: (e, ui) =>
    //(
    // ui.item : le dico renvoyé par le serveur
    // form = document.getElementById("recherche");
    // lieu = ui.item;
    // coords = lieu.lon+","+lieu.lat;
    // form.elements["coords_départ"].value=coords;
    //)
    onSelect(e, ui, document.getElementById("recherche"), "coords_départ")    
});

$("#id_arrivée").autocomplete({
    source: "{% url 'complète rue' %}",
    minLength: 4,
    select: (e, ui) => onSelect(e, ui, document.getElementById("recherche"), "coords_arrivée")
});

$("#rues_interdites").autocomplete({
    source: "{% url 'complète rue' %}",
    minLength: 4,
});

$("#étapes").autocomplete({
    source: "{% url 'complète rue' %}",
    minLength: 4,
});	      

