import * as Pll from "./pour_leaflet.js";
import * as Pf from "./fonctions.js";

let laCarte;


// Localisation
const form = document.getElementById("fouine");
navigator.geolocation.getCurrentPosition(
    pos => Pf.àLaGéoloc(pos, form),
    () => console.log("Échec de la géolocalisation.")
);

if (bbox){
    const lonLat = bbox.split(",").map(parseFloat);
    laCarte = Pll.carte_bb(bbox);
}else{
    laCarte = Pll.carteIci(form);
}

Pll.suivi_de_la_bb(laCarte, "fouine");
