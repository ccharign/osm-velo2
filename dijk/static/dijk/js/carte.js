import * as Pll from "./pour_leaflet.js";
import * as Marq from "./marqueurs.js";
import * as Pr from "./pour_recherche.js";


// variables globales venant du gabarit :
// - DONNÉES est un dico contenant les données envoyées par Django
// - L es la classe de base leaflet


// Les variables globales à ce module :
const form_recherche = document.getElementById("recherche");
let toutes_les_étapes;
let arrivée;
let nbÉtapes;		// nb d’étapes créées. Attention, peut être > au nb d’étapes existantes si suppression de certaines.
// L’étape d’étiquette i sera en case i de toutes_les_étapes
// Le départ en case 0
// L’arrivée est sortie du tab dans ce module pour pouvoir pusher facilement les nelles étapes
// étape supprimée = null dans toutes_les_étapes

let nbArêtesInterdites = 0;
let étapes_interdites = [];







// Étapes intermédiaires


// // On rajoute le départ devant
// if (form_recherche["données_cachées_départ"].length > 1){
//     toutes_les_étapes.unshift(JSON.parse(form_recherche["données_cachées_départ"].value));
// }else{
//     console.log("Pas d’autocomplétion utilisée pour le départ");
//     toutes_les_étapes.unshift(form_recherche["départ"].value);
// }


// // On rajoute l’arrivée à la fin
// if (form_recherche["données_cachées_arrivée"]){
//     toutes_les_étapes.unshift(JSON.parse(form_recherche["données_cachées_arrivée"].value));
// }else{
//     console.log("Pas d’autocomplétion utilisée pour l’arrivée");
//     toutes_les_étapes.unshift(form_recherche["arrivée"].value);
// }




//////////////
// La carte //
//////////////


// Dans les itis, on a les marqueurs de début et fin (à enlever!) ainsi que les étapes « passer par »
/**
@param{iti} objet de clefs 
Affiche l’itinéraire sur la carte indiqué.
*/
function afficheIti(iti, carte){
    L.polyline(iti.points, {color: iti.couleur, weight: 6, opacity: .6})
	.addTo(laCarte);

    for (let m of iti.marqueurs){
	Pll.marqueur_avec_popup(m, carte);
    }
}

const laCarte = Pll.carteBb(DONNÉES.bbox);

// itinéraires
for (let iti of DONNÉES.itis){
    afficheIti(iti, laCarte);
}



//////////////////////////////
// Récupération des étapes //
//////////////////////////////


toutes_les_étapes = Pr.récupJson(form_recherche.toutes_les_étapes.value);
nbÉtapes = toutes_les_étapes.length;


// Recréer les marqueurs
// Pour l’instant, pas de marqueur pour départ et arrivée
for (let i=1; i<toutes_les_étapes.length-1; i++){
    let coords = toutes_les_étapes[i].coords;
    if (coords){
	const latlng = [coords[1], coords[0]];
	Marq.nvÉtape(latlng, laCarte, i, toutes_les_étapes);
    }else{
	console.log("étape sans coords : " + toutes_les_étapes[i].nom);
    }
}

// Mettre l’arrivée de côté
arrivée = toutes_les_étapes.pop();


	
////////////////////////////////////////
// Gérer les marqueurs //////////
////////////////////////////////////////

laCarte.on("click",
	   e => ajouteMarqueur(e, laCarte)
	  );


// Appelé lors d’un clic sur la carte leaflet.
// Crée une étape si clic normal, une étape interdite si ctrl-clic
function ajouteMarqueur(e, carte) {
    if (e.originalEvent.ctrlKey){
	étapes_interdites.push(
	    Marq.nvArêteInterdite(e.latlng, carte)
	);
    }
    else{
	nbÉtapes++;
	toutes_les_étapes.push(
	    Marq.nvÉtape(e.latlng, carte, nbÉtapes, toutes_les_étapes)
	);
    }
}



/////////////////////////
///// Envoi du form /////
/////////////////////////

document.getElementById("btn_relance_rapide")
    .addEventListener(
	"click",
	e => Pr.envoieLeForm(form_recherche, toutes_les_étapes.concat([arrivée])) // J’avais mis arrivée à part.
    );
