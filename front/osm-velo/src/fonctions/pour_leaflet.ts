import L from "leaflet"
import { Dico } from "../classes/types.ts";


// https://stackoverflow.com/questions/23567203/leaflet-changing-marker-color
function markerHtmlStyles(coul:string){
    return `
  background-color: ${coul};
  width: 2rem;
  height: 2rem;
  display: block;
  left: -1rem;
  top: -1rem;
  position: relative;
  border-radius: 2rem 2rem 0;t
  transform: rotate(45deg);
  border: 1px solid gray`;
}


export function mon_icone(coul:string){
    return L.divIcon({
	className: "my-custom-pin",
	iconAnchor: [0, 24],
	// labelAnchor: [-6, 0],
	popupAnchor: [0, -36],
	html: `<span style="${markerHtmlStyles(coul)}" />`
    });
}



// Mettre en entrée la liste des champs du dico à afficher ?
/**
 * Rajoute à la carte « carte » un marqueur avec un popup contenant les infos.
 * @param {dico} infos 
 * @param {L.map} carte 
 */
export function marqueur_avec_popup(infos: Dico, carte: L.Map) {

	const marqueur = L.marker(
		[infos.lat as number, infos.lon as number]
	).addTo(carte);
        
    let contenu = ["nom", "adresse", "horaires", "tél" ]
	.filter(c=>infos[c])
	.map(c=>infos[c])
	.join("<br>");
    
    //D’après le tuto de leaflet:
    marqueur.bindPopup(`<div class="pop">${contenu}</div>`);
    
}



export default function carteIci() {    // Crée une carte à la position actuelle
	// Tuiles de cyclosm
	// Sortie : l’objet map créé

	const laCarte = L.map('laCarte'//, {fullscreenControl: true}
	).fitWorld();

    coucheCyclosm(laCarte);

    ajoute_fonctionalités_à_la_carte(laCarte);

    laCarte.locate({setView: true, maxZoom: 12});

	return laCarte;
}






// Ajoute la couche de tuiles cyclosm à la carte
function coucheCyclosm(carte: L.Map){
    L.tileLayer(
	'https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png',
	{
	    maxZoom: 20,
	    attribution: '<a href="https://github.com/cyclosm/cyclosm-cartocss-style/releases" title="CyclOSM - Open Bicycle render">CyclOSM</a> | Map data: {attribution.OpenStreetMap}'
	}
    ).addTo(carte);
}



// Ajoute la couche osm classique puis la surcouche cyclosmlite
function coucheSimple(carte: L.Map) {

	// tuiles osm de base
	L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
	maxZoom: 19,
	attribution: '© OpenStreetMap'
    }).addTo(carte);

    // couche cyclosm-lite
    L.tileLayer(
	'https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm-lite/{z}/{x}/{y}.png',
	{
	    maxZoom: 19,
	    attribution: '<a href="https://github.com/cyclosm/cyclosm-cartocss-style/releases" title="CyclOSM - Open Bicycle render">CyclOSM</a> | Map data: {attribution.OpenStreetMap}',
	    opacity: .3,
	}
    ).addTo(carte);   
}



// Crée une carte sur la bb passée en arg
// Si cyclosm, tuiles cyclosm, sinon tuile osm normales avec une couche cyclosm_lite
// Sortie : la carte créé
export function carteBb(bb: number[], cyclosm=false){

    const s = bb[0],
	  o = bb[1],
	  n = bb[2],
	  e = bb[3];

    const laCarte = L.map('laCarte',
        //           {"fullscreenControl": true}
    )
	  .fitBounds([[s,o], [n,e]]);

    if (cyclosm){
	coucheCyclosm(laCarte);
    }else{
	coucheSimple(laCarte);
    }

    ajoute_fonctionalités_à_la_carte(laCarte);

    return laCarte;
}


function ajoute_fonctionalités_à_la_carte(carte: L.Map) {
    // Ajoute le bouton géoloc et l’échelle à la carte passée en arg.

    // Bouton de géoloc
	// L.control.locate(
	// 	{
	// 	    "locateOptions": {
	// 		"enableHighAccuracy": true,
	// 		//"keepCurrentZoomLevel": true
	// 	    }
	// 	}
	// ).addTo(carte);

    // Échelle
	L.control.scale({ "imperial": false })
     .addTo(carte);
    
    // Boussole
    // carte.addControl( new L.Control.Compass() );
}



