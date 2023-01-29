import * as Pr from "./pour_recherche.js";
import * as AC from "./autoComplete.js";
import * as Pll from "./pour_leaflet.js";


// Spécifique à la recherche initiale:
// Récupère les champs départ et arrivée

// Précondition :
//  - url_api définie dans le gabarit
//  - $ a été chargé


// Les étapes sont des objets avec un champ « type » et d’autres champs spécifique au type.
//     Un json de la liste des étapes est mis dans le champ caché « toutes_les_étapes » du form : c’est ce champ qui sera lu par le serveur.


const leForm = document.getElementById("recherche");
let case_géol = document.getElementById("id_partir_de_ma_position");
let étiquette_géol = $('label[for="id_partir_de_ma_position"]');


// Autocomplétion
AC.autoComplète("départ", url_api, leForm);
AC.autoComplète("arrivée", url_api, leForm);




function extrait_json(texte){
    if (texte){
	return JSON.parse(texte);
    }else{
	return null;
    }
}

function récup_départ(){
    if (case_géol.checked){
	let latlon = leForm.localisation.value.split(",").map(parseFloat);
	return {type: "arête", coords: [latlon[1], latlon[0]]}; // On enregistre [lon, lat]
    }else if (leForm.données_cachées_départ.value){
	return JSON.parse(leForm.données_cachées_départ.value);
    }else{
	return {type : "adresse", adresse : leForm.départ.value};
    }
}

function récup_arrivée(){
    if (leForm.données_cachées_arrivée.value){
	return JSON.parse(leForm.données_cachées_arrivée.value);
    }else{
	return {type : "adresse", adresse : leForm.arrivée.value};
    }
}


// Enregistre les étapes avant de soumettre
function soumettre(){
    const départ = récup_départ();
    console.log(départ);
    const arrivée = récup_arrivée();
    console.log(départ, arrivée);
    Pr.envoieLeForm(leForm, [départ, arrivée]);
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
    const texte = Pll.texte_of_latLng(pos);
    console.log(`Position obtenue :  ${texte}. Je réaffiche la case « Partir de ma position ».` );
    leForm.elements["localisation"].value = texte;
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
