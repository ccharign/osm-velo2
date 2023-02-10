import * as fonctions from "./fonctions.js";
import * as É from "./étapes.js";
import {latLng_of_texte, mon_icone} from "./pour_leaflet.js";

// Pour la gestion des marqueurs sur la carte:
// Création lors d’un clic, déplacement, suppression



// Sera mis dans les popup
const bouton_suppr = '<button type="button" class="supprimeÉtape">Supprimer</button>';




export class ÉtapeMarquée extends É.ÉtapeAvecCoords{

    // Le constructeur de base
    // toute_les_étapes est le tableau duquel supprimer l’objet créé le cas échéant.
    // numéro : l’indice de l’étape dans toutes_les_étapes.
    constructor(o, numéro, carte, toutes_les_étapes){
	//this.objet_initial = o;
	super(o, o.coords);
	this.numéro = numéro;
	this.carte = carte;
	this.toutes_les_étapes = toutes_les_étapes;
	this.marqueur = this.nvMarqueur();
    }

    // Constructeur prenant un objet LatLng
    static ofLatlng(ll, numéro, carte, toutes_les_étapes){
	return new ÉtapeMarquée(
	    {coords: ll, type: "arête"},
	    numéro,
	    carte,
	    toutes_les_étapes
	);
    }

    // Change le numéro et màj l’étiquette
    setNuméro(i){
	this.numéro=i;
	this.marqueur.getTooltip().setContent(`${i}`);
    }


    nvMarqueur(){
	const marqueur = new L.marker( this.getLatlng(), {draggable: true, icon: mon_icone('green'), });
	marqueur.bindTooltip(this.numéro.toString(), {permanent: true, direction:"bottom"})  // étiquette
	    .addTo(this.carte)
	    .bindPopup(bouton_suppr);
    
	// marqueur.champ_du_form = "étape_coord"+num_étape;

	// binder la suppression de l’étape au bouton de la popup
	marqueur.on("popupopen",
		    () => {
			const bouton = document.querySelector(".supprimeÉtape");
			bouton.addEventListener("click",
						()=>{
						    this.carte.removeLayer(this.marqueur);
						    this.toutes_les_étapes.splice(this.numéro,1);
						    màjNumérosÉtapes(this.toutes_les_étapes, this.numéro);
						}
					       );
		    }
		   );

	// màj les coords si déplacé
	marqueur.on("dragend",
		    e => {
			this.setLatlng(e.target.getLatLng());
		    }
		   );
	
	return marqueur;
    }

}





// latlng: coords du point cliqué
// toutes_les_étapes : toutes les étapes sauf l’arrivée. L’arrivée est en troisième arg.
// Sortie : indice où mettre la nouvelle étapes dans toutes_les_étapes
function numOùInsérer(latlng, toutes_les_étapes){
    
    let res = toutes_les_étapes.length-1; // On n’insère jamais après l’arrivée.
    let fini = false;
    
    let éa = toutes_les_étapes[res];	// étape actuelle
    let ép = toutes_les_étapes[res-1]; // étape préc
    let vi = ép.vecteurVers(éa); // vecteur suivant l’itinéraire actuel
    let vé = ép.vecteurVersLatLng(latlng); // vecteur vers l’étape à rajouter

    while (res>1 && vi.produitScalaire(vé)<0){ // On n’insère jamais avant le départ càd en 0
	res--;
	éa = ép;
	ép = toutes_les_étapes[res-1];
	vi = ép.vecteurVers(éa);
	vé = ép.vecteurVersLatLng(latlng);
    }

    return res;
}


function màjNumérosÉtapes(étapes, début){
    for (let k=début; k<étapes.length; k++){
	étapes[k].setNuméro(k);
    }

}


// Crée une nouvelle étape
// toutes_les_étapes : tableau dans lequel insérer et éventuellement supprimer l’étape créée.
// Effet: la nouvelle étape est rajoutée à sa place dans toutes_les_étapes
// Sortie: l’objet sérialisable représentant celle-ci. Les coords au format (lon, lat)
export function nvÉtape(latlng, carte, toutes_les_étapes){

    const i = numOùInsérer(latlng, toutes_les_étapes);
    console.log(`Insertion en ${i}. Nombre d’étapes (avant insertion) ${toutes_les_étapes.length}`);
    const rés = ÉtapeMarquée.ofLatlng(latlng, i, carte, toutes_les_étapes);

    // Insertion dans la variable globale toutes_les_étapes
    toutes_les_étapes.splice(i, 0, rés);
    
    // màj des numéros des étapes suivante
    màjNumérosÉtapes(toutes_les_étapes, i+1);

    return rés;
}



// export function nvArêteInterdite(latlng, carte, num_étape, toutes_les_étapes){

//     // Création du marqueur
//     nbArêtesInterdites += 1;
//     const marker = new L.marker( latlng, {
// 	icon: mon_icone('red'),
// 	draggable: true
//     })
// 	  .addTo(carte)
// 	  .bindPopup(buttonRemove);

//     marker.champ_du_form = "interdite_coord"+nbArêtesInterdites;

//     // event remove marker
//     marker.on("popupopen", () => supprimeMarqueur(carte, marqueur, num_étape, toutes_les_étapes));

//     // event draged marker
//     marker.on("dragend", dragedMarker);
    
//     // Ajout du champ hidden au formulaire
//     // const form_relance = document.getElementById("relance_rapide");
//     // fonctions.addHidden(form_relance, marker.champ_du_form, latlng.lng +","+ latlng.lat);
// }
