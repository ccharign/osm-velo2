

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


function mon_icone(coul){
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
function marqueur_avec_popup(lon, lat, infos, carte){

    const marqueur = L.marker(
        [lat, lon]
    ).addTo(carte);
        
//     var popup = L.popup({"maxWidth": "100%"});
//     var html_à_mettre = $(`<div style="width: 100.0%; height: 100.0%;">{contenu}</div>`)[0];
//     popup.setContent(html_à_mettre);
//     marqueur.bindPopup(popup);
    //

    let contenu ="";
    for (champ of ["nom", "adresse", "horaires", "tél" ]){
	if (infos[champ]){
	    contenu += infos[champ]+"<br>";
	}
    };

    contenu= `<div class="pop">${contenu}</div>`;
    
    //D’après le tuto de leaflet:
    marqueur.bindPopup(contenu);
    
}



function latLng_of_texte(texte){
    // Entrée : chaîne de car "lon,lat"
    // Sortie : Objet latLng correspondant
    const tab_coords = texte.split(",").map(parseFloat);
    return L.latLng(tab_coords[1], tab_coords[0]);    
}


function texte_of_latLng(ll){
    // Entrée : objet latLng
    // Sortie : chaîne "lon,lat"
    return ll.coords.longitude + "," + ll.coords.latitude;
}


function carteIci(){
    // Crée une carte à la position actuelle
    // Tuiles de cyclosm
    // Sortie : l’objet map créé

    const laCarte = L.map('laCarte', {fullscreenControl: true}).fitWorld();

    L.tileLayer(
	'https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png',
	{
	    "maxZoom": 20,
	    "attribution": '<a href="https://github.com/cyclosm/cyclosm-cartocss-style/releases" title="CyclOSM - Open Bicycle render">CyclOSM</a> | Map data: {attribution.OpenStreetMap}'
	}
    ).addTo(laCarte);

    ajoute_fonctionalités_à_la_carte(laCarte);

    laCarte.locate({setView: true, maxZoom: 12});

    return laCarte;
}

function suivi_de_la_bb(carte, nom_form){
    carte.on(
	'moveend',
	function (){
	    t =  bbox_of_carte(carte);
	    texte= `${t[0]},${t[1]},${t[2]},${t[3]}`;
	    form = document.getElementById(nom_form);
	    
        form["id_bbox"].value = texte;
	});
}

function bbox_of_carte(carte){
    // Entrée : une carte leaflet
    // Sortie : (s, o, n, e)
    bounds = carte.getBounds();
    ne = bounds.getNorthEast();
    n = ne.lat; e=ne.lng;
    so = bounds.getSouthWest();
    s = so.lat; o=so.lng;
    return [s,o,n,e];
}


function carte_bb(s,o,n,e){
    // Crée une carte sur la bb passée en arg
    // Tuile osm normales avec une couche cyclosm_lite
    // Sortie : la carte créé

    const laCarte = L.map('laCarte', {fullscreenControl: true}).fitBounds([[s,o],[n,e]]);

    // tuiles osm de base
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
	maxZoom: 19,
	attribution: '© OpenStreetMap'
    }).addTo(laCarte);

    // couche cyclosm-lite
    L.tileLayer(
	'https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm-lite/{z}/{x}/{y}.png',
	{
	    "maxZoom": 19,
	    "attribution": '<a href="https://github.com/cyclosm/cyclosm-cartocss-style/releases" title="CyclOSM - Open Bicycle render">CyclOSM</a> | Map data: {attribution.OpenStreetMap}'
	}
    ).addTo(laCarte);

    ajoute_fonctionalités_à_la_carte(laCarte);

    console.log("Carte créé :");
    console.log(laCarte);
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
    L.control.scale(imperial=false).addTo(carte);    
}



