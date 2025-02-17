

// https://stackoverflow.com/questions/23567203/leaflet-changing-marker-color
function markerHtmlStyles(coul){
    return `
  background-color: ${coul};
  width: 2rem;
  height: 2rem;
  display: block;
  left: -1rem;
  top: -1rem;
  position: relative;
  border-radius: 2rem 2rem 0;
  transform: rotate(45deg);
  border: 1px solid gray`;
}


export function mon_icone(coul){
    return L.divIcon({
	className: "my-custom-pin",
	iconAnchor: [0, 24],
	labelAnchor: [-6, 0],
	popupAnchor: [0, -36],
	html: `<span style="${markerHtmlStyles(coul)}" />`
    });
}



// Mettre en entrée la liste des champs du dico à afficher ?
/**
 * Rajoute à la carte « carte » un marqueur avec un popup contenant les infos.
 * @param {number} lon 
 * @param {number} lat 
 * @param {dico} infos 
 * @param {L.map} carte 
 */
export function marqueur_avec_popup(infos, carte){

    const marqueur = L.marker(
        [infos.lat, infos.lon]
    ).addTo(carte);
        
    let contenu = ["nom", "adresse", "horaires", "tél" ]
	.filter(c=>infos[c])
	.map(c=>infos[c])
	.join("<br>");
    
    //D’après le tuto de leaflet:
    marqueur.bindPopup(`<div class="pop">${contenu}</div>`);
    
}


// Entrée : chaîne de car "lon,lat"
// Sortie : Objet latLng correspondant
export function latLng_of_texte(texte){
    const tab_coords = texte.split(",").map(parseFloat);
    return L.latLng(tab_coords[1], tab_coords[0]);    
}

// Entrée : objet latLng
// Sortie : chaîne "lon,lat"
export function texte_of_latLng(ll){
    return ll.coords.longitude + "," + ll.coords.latitude;
}


export function carteIci(){    // Crée une carte à la position actuelle
    // Tuiles de cyclosm
    // Sortie : l’objet map créé

    const laCarte = L.map('laCarte', {fullscreenControl: true}).fitWorld();

    coucheCyclosm(laCarte);

    ajoute_fonctionalités_à_la_carte(laCarte);

    laCarte.locate({setView: true, maxZoom: 12});

    return laCarte;
}




// Ajoute un listener à la carte qui met à jour le champ id_bbox du form
export function suivi_de_la_bb(carte, nom_form){
    carte.on(
	'moveend',
	function (){
	    const t =  bbox_of_carte(carte);
	    const texte = `${t[0]},${t[1]},${t[2]},${t[3]}`;
	    const form = document.getElementById(nom_form);
	    
        form["id_bbox"].value = texte;
	});
}


// Entrée : une carte leaflet
// Sortie : (s, o, n, e)
function bbox_of_carte(carte){
    const bounds = carte.getBounds();
    const ne = bounds.getNorthEast();
    const n = ne.lat;
    const e=ne.lng;
    const so = bounds.getSouthWest();
    const s = so.lat;
    const o=so.lng;
    return [s,o,n,e];
}


// Ajoute la couche de tuiles cyclosm à la carte
function coucheCyclosm(carte){
    L.tileLayer(
	'https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png',
	{
	    maxZoom: 20,
	    attribution: '<a href="https://github.com/cyclosm/cyclosm-cartocss-style/releases" title="CyclOSM - Open Bicycle render">CyclOSM</a> | Map data: {attribution.OpenStreetMap}'
	}
    ).addTo(carte);
}



// Ajoute la couche osm classique puis la surcouche cyclosmlite
function coucheSimple(carte){
    
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
export function carteBb(bb, cyclosm=false){

    const s = bb[0],
	  o = bb[1],
	  n = bb[2],
	  e = bb[3];

    const laCarte = L.map('laCarte', {"fullscreenControl": true})
	  .fitBounds([[s,o], [n,e]]);

    if (cyclosm){
	coucheCyclosm(laCarte);
    }else{
	coucheSimple(laCarte);
    }

    ajoute_fonctionalités_à_la_carte(laCarte);

    return laCarte;
}


function ajoute_fonctionalités_à_la_carte(carte){
    // Ajoute le bouton géoloc et l’échelle à la carte passée en arg.
    
    // Bouton de géoloc
    const locate_control = L.control.locate(
        {"locateOptions": {
	    "enableHighAccuracy": true,
	    "keepCurrentZoomLevel": true
	}}
    ).addTo(carte);

    // Échelle
    L.control.scale({"imperial": false})
	.addTo(carte);

    // Boussole
    // carte.addControl( new L.Control.Compass() );
}



