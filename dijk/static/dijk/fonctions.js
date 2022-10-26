





////////////////////////////////////
// Gestion des clics sur la carte //
////////////////////////////////////




// Mettre en entrée la liste des champs du dico à afficher ?

function marqueur_avec_popup(lon, lat, infos, carte){
    // infos : dico
    // Rajoute à la carte « carte » un marqueur avec un popup contenant les infos.

    var marqueur = L.marker(
        [lat, lon]
    ).addTo(carte);
        
//     var popup = L.popup({"maxWidth": "100%"});
//     var html_à_mettre = $(`<div style="width: 100.0%; height: 100.0%;">{contenu}</div>`)[0];
//     popup.setContent(html_à_mettre);
//     marqueur.bindPopup(popup);
    //

    var contenu ="";
    for (champ of ["nom", "horaires", "tél" ]){
	if (infos[champ]){
	    contenu=contenu+infos[champ]+"<br>";
	}
    };

    contenu= `<div class="pop">${contenu}</div>`;
    
    //D’après le tuto de leaflet:
    marqueur.bindPopup(contenu);
    
}


var nbÉtapes = 0;
var nbArêtesInterdites = 0;



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





function gèreLesClics(carte){
    carte.on("click",
	     e => addMarker(e, carte)
	    );
}


function marqueurs_of_form(form, carte){
    
    récupMarqueurs(
	form.elements["marqueurs_é"].value,
	coords => nvÉtape(coords, carte)
    );
    récupMarqueurs(
	form.elements["marqueurs_i"].value,
	coords => nvArêteInterdite(coords, carte)
    );
}



function récupMarqueurs(texte, fonction) {
    // Entrée :
    //     texte contient des coords (chacune de la forme "lon,lat") séparées par un ;
    // Effet : transforme chaque coord en un objet latLng puis lance fonction dessus.
    for (coords_t of (texte.split(";"))){
	if (coords_t){
	    coord =  latLng_of_texte(coords_t);
	    fonction(coord);
	}
    }
}


function addMarker(e, carte) {
    // Appelé lors d’un clic sur la carte leaflet.
    if (e.originalEvent.ctrlKey){
	nvArêteInterdite(e.latlng, carte);
    }
    else{
	nvÉtape(e.latlng, carte);
    }
}




function nvÉtape(latlng, carte){
    nbÉtapes+=1;
    
    //const markerPlace = document.querySelector(".marker-position");
    //markerPlace.textContent = `new marker: ${e.latlng.lat}, ${e.latlng.lng}`;

    
    const marker = new L.marker( latlng, {draggable: true, icon: mon_icone('green'), });
    marker.bindTooltip(""+nbÉtapes, {permanent: true, direction:"bottom"})// étiquette
	  .addTo(carte)
	  .bindPopup(buttonRemove);
    
    marker.champ_du_form = "étape_coord"+nbÉtapes;

    // event remove marker
    marker.on("popupopen", () => removeMarker(carte, marker));

    // event draged marker
    marker.on("dragend", dragedMarker);

    form = document.getElementById("relance_rapide");
    addHidden(form, marker.champ_du_form, latlng.lng +","+ latlng.lat);
}


function nvArêteInterdite(latlng, carte){

    // Création du marqueur
    nbArêtesInterdites+=1;
    const marker = new L.marker( latlng, {
	icon: mon_icone('red'),
	draggable: true
    })
	  .addTo(carte)
	  .bindPopup(buttonRemove);

    marker.champ_du_form = "interdite_coord"+nbArêtesInterdites;

    // event remove marker
    marker.on("popupopen", () => removeMarker(carte, marker));

    // event draged marker
    marker.on("dragend", dragedMarker);
    
    // Ajout du champ hidden au formulaire
    form = document.getElementById("relance_rapide");
    addHidden(form, marker.champ_du_form, latlng.lng +","+ latlng.lat);
}


const buttonRemove =
  '<button type="button" class="remove">Supprimer</button>';


// contenu des popup des marqueurs
function removeMarker(carte, marker) {
    
    //const marker = this;// L’objet sur lequelle cette méthode est lancée
    const btn = document.querySelector(".remove");
    
    btn.addEventListener("click", function () {
	//const markerPlace = document.querySelector(".marker-position");
	//markerPlace.textContent = "goodbye marker";
	hidden = document.getElementById(marker.champ_du_form);
	hidden.remove();
	carte.removeLayer(marker);
    });
}


// draged
function dragedMarker() {
  //const markerPlace = document.querySelector(".marker-position");
  //markerPlace.textContent = `change position: ${this.getLatLng().lat}, ${
  //  this.getLatLng().lng
    //}`;
    const marker=this;
    document.getElementById(marker.champ_du_form).value = marker.getLatLng().lng+","+ marker.getLatLng().lat;
}


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
