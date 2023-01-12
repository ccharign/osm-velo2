import * as fonctions from "./fonctions.js";
import {latLng_of_texte, mon_icone} from "./pour_leaflet.js";

// Pour la gestion des marqueurs sur la carte:
// Création lors d’un clic, déplacement, suppression et mise à jour des champs du formulaire




// Inutile maintenant que toutes les étapes sont dans form.toutes_les_étapes
// function marqueurs_of_form(form, carte){
    
//     récupMarqueurs(
// 	form.elements["marqueurs_é"].value,
// 	coords => nvÉtape(coords, carte)
//     );
//     récupMarqueurs(
// 	form.elements["marqueurs_i"].value,
// 	coords => nvArêteInterdite(coords, carte)
//     );
// }



// function récupMarqueurs(texte, fonction) {
//     // Entrée :
//     //     texte contient des coords (chacune de la forme "lon,lat") séparées par un ;
//     // Effet : transforme chaque coord en un objet latLng puis lance fonction dessus.
//     for (let coords_t of (texte.split(";"))){
// 	if (coords_t){
// 	    fonction(latLng_of_texte(coords_t));
// 	}
//     }
// }




// Crée une nouvelle étape
// toutes_les_étapes : tableau dans lequel insérer et éventuellement supprimer l’étape créée.
// Sortie : l’objet sérialisable représentant celle-ci.
export function nvÉtape(latlng, carte, num_étape, toutes_les_étapes){

    
    const marqueur = new L.marker( latlng, {draggable: true, icon: mon_icone('green'), });
    marqueur.bindTooltip(""+num_étape, {permanent: true, direction:"bottom"})// étiquette
	  .addTo(carte)
	  .bindPopup(buttonRemove);
    
    marqueur.champ_du_form = "étape_coord"+num_étape;

    // créer un bouton « supprimer » dans la popup
    marqueur.on("popupopen",
	      () => supprimeMarqueur(carte, marqueur, num_étape, toutes_les_étapes)
	     );

    // màl les coords si déplacé
    marqueur.on("dragend",
	      e => auDéplacement(e, num_étape, toutes_les_étapes)
	     );

    return {"type": "arête", "coords": [latlng.lng, latlng.lat]};
}



export function nvArêteInterdite(latlng, carte, num_étape, toutes_les_étapes){

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
    marker.on("popupopen", () => supprimeMarqueur(carte, marqueur, num_étape, toutes_les_étapes));

    // event draged marker
    marker.on("dragend", dragedMarker);
    
    // Ajout du champ hidden au formulaire
    // const form_relance = document.getElementById("relance_rapide");
    // fonctions.addHidden(form_relance, marker.champ_du_form, latlng.lng +","+ latlng.lat);
}

// Sera mis dans les popup
const buttonRemove =
  '<button type="button" class="remove">Supprimer</button>';


// contenu des popup des marqueurs
function supprimeMarqueur(carte, marqueur, num_étape, toutes_les_étapes) {
    
    const btn = document.querySelector(".remove");
    
    btn.addEventListener("click", function () {
	// let hidden = document.getElementById(marker.champ_du_form);
	// hidden.remove();
	carte.removeLayer(marqueur);
	toutes_les_étapes[num_étape]=null;
    });
}


// draged
function auDéplacement(e, num_étape, toutes_les_étapes) {
    let latlng = e.target.getLatLng();
    toutes_les_étapes[num_étape].coords = [latlng.lng, latlng.lat];
    //document.getElementById(marker.champ_du_form).value = marker.getLatLng().lng + "," + marker.getLatLng().lat;
}
