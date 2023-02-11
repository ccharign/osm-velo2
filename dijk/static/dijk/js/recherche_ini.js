import * as Pr from "./pour_recherche.js";
import * as AC from "./autoComplete.js";
import * as Pll from "./pour_leaflet.js";
import * as É from "./étapes.js";


// Spécifique à la recherche initiale:
// Récupère les champs départ et arrivée avec autocomplétion

// Précondition :
//  - url_api définie dans le gabarit
//  - $ a été chargé


// Les étapes sont des objets avec un champ « type » et d’autres champs spécifique au type.
//     Un json de la liste des étapes est mis dans le champ caché « toutes_les_étapes » du form : c’est ce champ qui sera lu par le serveur.


const leForm = document.getElementById("recherche");
let case_géol = document.getElementById("id_partir_de_ma_position");
let étiquette_géol = $('label[for="id_partir_de_ma_position"]');
let localisation;  // aura des champs longitude et latitude (objet issu de navigator.geolocation.getCurrentPosition)
const ÉTAPES = [new É.Étape(), new É.Étape()];		// Contiendra les étapes


//////////////////////////////
////// Autocomplétion ////////
//////////////////////////////



function onSelectAutoComplète(e, ui, étape){
    // Lancé lors de la sélection d’un élément dans un champ autocomplété.
    // e : l’événement, ui : l’objet sélectionné
    // Effet : enregistre dans étape la valeur de «àCacher» de l’objet ui sélectionné par l’autocomplétion.
    const lieu = ui.item;
    étape.màj(extrait_json(lieu.àCacher));
}

// Met en place l’autocomplétion pour le champ indiqué dans le form indiqué.
// longMin est facultatif. 3 par défaut.
// l’élément du formulaire doit s’appeler "id_"+nomChamp, l’élément à remplir doit s’appeler "données_cachées_"+nomChamp
function autoComplète(nomChamp,  étape, longMin=3){
    $(function () {
        $("#id_"+nomChamp).autocomplete({
	    source: url_api,
	    minLength: longMin,
	    select: (e, ui) => onSelectAutoComplète(e, ui, étape )
        });
    });
}


autoComplète("départ", ÉTAPES[0]);
autoComplète("arrivée", ÉTAPES[1]);




function extrait_json(texte){
    if (texte){
	return JSON.parse(texte);
    }else{
	return null;
    }
}


function récup_départ(){
    
    if (case_géol.checked){
	//let latlon = leForm.localisation.value.split(",").map(parseFloat); // NB: les coords ont déjà été enregistrées dans le format lon,lat
	const ll = {lat: localisation.latitude, lng:localisation.longitude};
	ÉTAPES[0] = new É.ÉtapeAvecCoordsÉtapeAvecCoord({type: "arête", coords: ll}, ll);
	
    }else if (!ÉTAPES[0].objet_initial){ // l’objet Étape du départ n’a pas été rempli
	// Je fais une étape adresse avec le contenu du champ (qui n’a donc pas été autocomplété)
	ÉTAPES[0] = new É.Étape({type : "adresse", adresse : leForm.départ.value});
    }
}


function récup_arrivée(){    
    if (!ÉTAPES[1].objet_initial){
	ÉTAPES[1] = new É.Étape({type : "adresse", adresse : leForm.arrivée.value});
    }
}


// Enregistre les étapes avant de soumettre
function soumettre(){
    récup_départ();
    récup_arrivée();
    console.log(ÉTAPES);
    Pr.envoieLeForm(leForm, ÉTAPES);
}

document.getElementById("btn_soumettre").addEventListener(
    "click",
    soumettre
);

document.getElementById("id_arrivée").addEventListener(
    "keypress",
    e => {if (e.code==="Enter"){soumettre();};}
);


////////////////////
// géoloc
////////////////////



// Met à jour le champ "localisation" du form
function àLaGéoloc(pos){
    //const texte = `${pos.coords.longitude},${pos.coords.latitude}`;
    localisation = pos.coords;
    console.log(`Position obtenue : lon,lat =  ${localisation}. Je réaffiche la case « Partir de ma position ».` );
    //leForm.elements["localisation"].value = texte;
    case_géol.hidden=false;
    étiquette_géol.show();
}



// Initialement la case est cachée
console.log("Je cache la case « Partir de ma position »");
case_géol.hidden=true;
étiquette_géol.hide();


// Afficher une fois la position obtenue
navigator.geolocation.getCurrentPosition(
    pos => àLaGéoloc(pos),
    () => console.log("Échec de la géolocalisation."),
    {"enableHighAccuracy": true,
     "maximumAge": 10000}
);
