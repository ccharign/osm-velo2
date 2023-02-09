import * as fonctions from "./fonctions.js";
import {latLng_of_texte, mon_icone} from "./pour_leaflet.js";

// Pour la gestion des marqueurs sur la carte:
// Création lors d’un clic, déplacement, suppression



// Sera mis dans les popup
const bouton_suppr = '<button type="button" class="supprimeÉtape">Supprimer</button>';




export class Étape{

    static R_terre = 6360000; // en mètres
    static coeff_rad = Math.PI/180; // Multiplier par ceci pour passer en radians

    // Le constructeur de base
    // toute_les_étapes est le tableau duquel supprimer l’objet créé le cas échéant.
    // numéro : l’indice de l’étape dans toutes_les_étapes.
    // Les coords sont dans this.objet_initial.coords au format [lon, lat]
    constructor(o, numéro, carte, toutes_les_étapes){
	this.objet_initial = o;
	this.numéro = numéro;
	this.carte = carte;
	this.toutes_les_étapes = toutes_les_étapes;
	this.marqueur = this.nvMarqueur();
    }

    // Constructeur prenant un objet LatLng
    static ofLatlng(ll, numéro, carte, toutes_les_étapes){
	return new Étape(
	    {coords: [ll.lng, ll.lat], type: "arête"},
	    numéro,
	    carte,
	    toutes_les_étapes
	);
    }

    // Constructeur prenant un objet quelconque. Un objet Étape est renvoyé si présence d’un attribut « coords ».
    // Sinon l’objet passé en arg est renvoyé tel quel.
    // static ofObjet(o, numéro, carte, toutes_les_étapes){
    // 	if ("coords" in o){
    // 	    return new Étape(o);
    // 	}else{
    // 	    return o;
    // 	}
    // }


    // Change le numéro et màj l’étiquette
    setNuméro(i){
	this.numéro=i;
	this.marqueur.getTooltip().setContent(`${i}`);
	// this.marqueur.closeTooltip();
	// this.marqueur.bindTooltip(`${i}`);
    }

    getLatlng(){
	return { lng: this.objet_initial.coords[0], lat: this.objet_initial.coords[1]};
    }

    setLatlng(ll){
	this.objet_initial.coords = [ll.lng, ll.lat];
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

    // Renvoie un objet contenant uniquement les données utiles au serveur.
    versDjango(){
	return this.objet_initial;
    }

    // Renvoie le vecteur de this vers autreÉtape. En mètres.
    // vecteurVersCoords(lon2, lat2){
    // 	const ll1 = this.getLatlng();
    // 	const lat1 = ll1[0];
    // 	const lon1 = ll1[1];
    // 	const dx = Étape.R_terre * Math.cos(lat1) * (lon2-lon1);
    // 	const dy = Étape.R_terre * (lat2-lat1);
    // 	return new Vecteur(dx, dy);
    // }

    vecteurVers(autreÉtape){
	return this.vecteurVersLatLng(autreÉtape.getLatlng());
    }

    vecteurVersLatLng(ll2){
	const ll1 = this.getLatlng();
	const dx = Étape.R_terre * Math.cos(ll1.lat*Math.PI/180) * (ll2.lng - ll1.lng)*Math.PI/180;
	const dy = Étape.R_terre * (ll2.lat - ll1.lat)*Math.PI/180;
	return new Vecteur(dx, dy);
    }
}


class Vecteur{
    
    constructor(x, y){
	this.x = x;
	this.y = y;
    }

    produitScalaire(autre_vecteur){
	return this.x*autre_vecteur.x + this.y*autre_vecteur.y;
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





// Crée une nouvelle étape
// toutes_les_étapes : tableau dans lequel insérer et éventuellement supprimer l’étape créée.
// Effet: la nouvelle étape est rajoutée à sa place dans toutes_les_étapes
// Sortie: l’objet sérialisable représentant celle-ci. Les coords au format (lon, lat)
export function nvÉtape(latlng, carte, toutes_les_étapes){

    const i = numOùInsérer(latlng, toutes_les_étapes);
    console.log(`Insertion en ${i}. Nombre d’étapes (avant insertion) ${toutes_les_étapes.length}`);
    const rés = Étape.ofLatlng(latlng, i, carte, toutes_les_étapes);

    // Insertion dans la variable globale toutes_les_étapes
    toutes_les_étapes.splice(i, 0, rés);
    
    // màj des numéros des étapes suivante
    for (let k=i+1; k<toutes_les_étapes.length; k++){
	toutes_les_étapes[k].setNuméro(k);
    }

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



// contenu des popup des marqueurs
// function supprimeMarqueur(carte, marqueur, num_étape, toutes_les_étapes) {
    
//     const btn = document.querySelector(".remove");
    
//     btn.addEventListener("click", function () {
// 	carte.removeLayer(marqueur);
// 	toutes_les_étapes[num_étape]=null;
//     });
// }


// // draged
// function auDéplacement(e, num_étape, toutes_les_étapes) {
//     let latlng = e.target.getLatLng();
//     toutes_les_étapes[num_étape].coords = [latlng.lng, latlng.lat];
//     //document.getElementById(marker.champ_du_form).value = marker.getLatLng().lng + "," + marker.getLatLng().lat;
// }
