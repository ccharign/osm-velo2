import * as Pll from "./pour_leaflet.js";
import * as Pf from "./fonctions.js";


// variables globales venant de autourDeMoi.html: BBOX et TEXTE_MARQUEURS



//////////////////////////////
// Création de la Carte
//////////////////////////////

const form = document.getElementById("fouine");

let laCarte;

if (BBOX){
    const bbox = BBOX.split(",").map(parseFloat);
    laCarte = Pll.carteBb(bbox);
}else{
    // navigator.geolocation.getCurrentPosition(
    // 	pos => Pf.àLaGéoloc(pos, form),
    // 	() => console.log("Échec de la géolocalisation."),
    // 	{"enableHighAccuracy": true,
    // 	 "maximumAge": 10000}
    // );

    laCarte = Pll.carteIci(form);
}

Pll.suivi_de_la_bb(laCarte, "fouine");



//////////////////////////////
///// Les marqueurs /////
//////////////////////////////

const marqueurs = Pf.tab_of_json(TEXTE_MARQUEURS);

for (let m of marqueurs){
    Pll.marqueur_avec_popup(m, laCarte);
}
