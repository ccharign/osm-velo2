import * as Pll from "./pour_leaflet.js";
import * as Marq from "./marqueurs.js";
import * as Pr from "./pour_recherche.js";


// variables globales venant du gabarit :
// - DONNÉES est un dico contenant les données envoyées par Django
// - L est la classe de base leaflet
// URL_GPX l’adresse de l’API pour récupérer les gpx


// Les variables globales à ce module :
const form_recherche = document.getElementById("recherche");
let toutes_les_étapes;


// L’étape d’étiquette i sera en case i de toutes_les_étapes
// Le départ en case 0

let nbArêtesInterdites = 0;
let étapes_interdites = [];

let clic_sur_iti = false;



function dernierÉlém(tab){
    return tab[tab.length-1];
}



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

function onClicSurIti(e, pourcentage_détour){
    	    console.log("Clic sur l’iti!");
	    // e.originalEvent.stopPropagation(); // Ceci ne fonctionne pas dans leaflet...
	    // je le fait à la main
    clic_sur_iti=true;
    window.open(URL_GPX + pourcentage_détour, '_self');
}


// Dans les itis, on a les marqueurs de début et fin (à enlever à terme...) ainsi que les étapes « passer par »
/**
@param{iti} objet de clefs 
Affiche l’itinéraire sur la carte indiqué.
*/
function afficheIti(iti, carte){
    
    // L’itinéraire
    let ligne = L.polyline(iti.points, {color: iti.couleur, weight: 6, opacity: .6})
	.addTo(laCarte)
        .on("click", e => onClicSurIti(e, iti.pourcentage_détour));
	   
    
    // Ses marqueurs
    for (let m of iti.marqueurs){
	Pll.marqueur_avec_popup(m, carte);
    }
}


// Création de la carte
const laCarte = Pll.carteBb(DONNÉES.bbox);


// itinéraires
for (let iti of DONNÉES.itis){
    afficheIti(iti, laCarte);
}



//////////////////////////////
// Récupération des étapes //
//////////////////////////////


toutes_les_étapes = Pr.récupJson(form_recherche.toutes_les_étapes.value);

// Ajout de coords départ et arrivée
let iti_vert = dernierÉlém(DONNÉES.itis); // On se base sur l’iti avec le plus grand p_détour
toutes_les_étapes[0].coords = iti_vert.points[0];
dernierÉlém(toutes_les_étapes).coords = dernierÉlém(iti_vert.points);

// Création des objets Étape.
// Ceci crée aussi les marqueurs
for (let i=0; i<toutes_les_étapes.length; i++){
    toutes_les_étapes[i] = new Marq.Étape(toutes_les_étapes[i], i, laCarte, toutes_les_étapes);
}


    




// // Recréer les marqueurs
// for (let i=1; i<toutes_les_étapes.length-1; i++){
//     let coords = toutes_les_étapes[i].coords;
//     if (coords){
// 	const latlng = [coords[1], coords[0]];
// 	Marq.nvÉtape(latlng, laCarte, i, toutes_les_étapes);
//     }else{
// 	console.log("étape sans coords : " + toutes_les_étapes[i].nom);
//     }
// }



	
////////////////////////////////////////
// Gérer les marqueurs //////////
////////////////////////////////////////

laCarte.on("click",
	   e => {
	       if (clic_sur_iti) {
		   clic_sur_iti=false;
	       }else{
		   ajouteMarqueur(e, laCarte);
	       }
	   }
	  );


// Appelé lors d’un clic sur la carte leaflet.
// Crée une étape si clic normal, une étape interdite si ctrl-clic
function ajouteMarqueur(e, carte) {
    // if (e.originalEvent.ctrlKey){
    // 	étapes_interdites.push(
    // 	    Marq.nvArêteInterdite(e.latlng, carte)
    // 	);
    // }
    // else{
	Marq.nvÉtape(e.latlng, carte, toutes_les_étapes);
    //}
}


///////////////////////////////////
////////// Trajet retour //////////
///////////////////////////////////

document.getElementById("btn_retour")
    .addEventListener(
	"click",
	e => {
	    Pr.envoieLeForm(form_recherche, toutes_les_étapes.reverse());
	}
    );



/////////////////////////
///// Envoi du form /////
/////////////////////////

document.getElementById("btn_relance_rapide")
    .addEventListener(
	"click",
	e => Pr.envoieLeForm(form_recherche, toutes_les_étapes)
    );
