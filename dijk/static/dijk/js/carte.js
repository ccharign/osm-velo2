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


// Dans les itis, on a les marqueurs des étapes « passer par » (qui peuvent varier selon l’iti)
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

function tabVersLatlng(tab){
    const lat = tab[0];
    const lng = tab[1];
    return {lat: lat, lng: lng};
}

toutes_les_étapes = Pr.récupJson(form_recherche.toutes_les_étapes.value);

// Ajout de coords départ et arrivée
const iti_vert = dernierÉlém(DONNÉES.itis); // On se base sur l’iti avec le plus grand p_détour
toutes_les_étapes[0].coords = tabVersLatlng(iti_vert.points[0]);
dernierÉlém(toutes_les_étapes).coords = tabVersLatlng(dernierÉlém(iti_vert.points));

// Création des objets ÉtapeMarquée.
// Ceci crée aussi les marqueurs
for (let i=0; i<toutes_les_étapes.length; i++){
    toutes_les_étapes[i] = new Marq.ÉtapeMarquée(toutes_les_étapes[i], i, laCarte, toutes_les_étapes);
}


if (DONNÉES.form_enregistrer_présent){
    // Le formulaire « Enregistrer contrib » est affiché, remplissons son champ toutes_les_étapes
    Pr.màjToutes_les_étapes(
	document.getElementById("enregistrer_chemin"),
	toutes_les_étapes
    );
}
   


	
/////////////////////////////////
// Gérer les marqueurs //////////
/////////////////////////////////

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
