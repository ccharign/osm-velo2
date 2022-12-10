// Pour la gestion des marqueurs sur la carte:
// Création lors d’un clic, déplacement, suppression et mise à jour des champs du formulaire



let nbÉtapes = 0;
let nbArêtesInterdites = 0;


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
