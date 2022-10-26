

// https://stackoverflow.com/questions/23567203/leaflet-changing-marker-color
function markerHtmlStyles(coul){
    return `
  background-color: ${coul};
  width: 3rem;
  height: 3rem;
  display: block;
  left: -1.5rem;
  top: -1.5rem;
  position: relative;
  border-radius: 3rem 3rem 0;
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
    // Tuile de cyclosm
    // Sortie : l’objet map créé

    var laCarte = L.map('laCarte', {fullscreenControl: true}).fitWorld();

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

    var laCarte = L.map('laCarte', {fullscreenControl: true}).fitBounds([[s,o],[n,e]]);

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
    var locate_control = L.control.locate(
        {"locateOptions": {
	    "enableHighAccuracy": true,
	    "keepCurrentZoomLevel": true
	}}
    ).addTo(carte);

    // Échelle
    L.control.scale(imperial=false).addTo(carte);    
}




function voir_si_géoLoc(){
    //if (navigator.geolocalisation){
	form_recherche = document.getElementById("recherche");
	addHidden(form_recherche, "localisation", (0.,0.));
	navigator.geolocation.getCurrentPosition(
	    pos => àLaGéoloc(pos, form_recherche),
	    () => pasDeGéoloc(form_recherche)
	);
    //}
}


function àLaGéoloc(pos, form){
    // Met à jour le champ "localisation" du form
    texte = texte_of_latLng(pos);
    console.log("Position obtenue : " + texte );
    form.elements["localisation"].value = texte;
}


function pasDeGéoloc(form){
    // Supprime la chekbox « partir de ma position »
    console.log("Pas de géoloc");
    form_recherche.getElementsByClassName("checkbox")[0].remove();
}
