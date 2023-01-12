import * as Pr from "./pour_recherche.js";
import * as AC from "./autoComplete.js";


// Spécifique à la recherche initiale:
// Récupère les champs départ et arrivée

// url_api définie dans le gabarit



const leForm = document.getElementById("recherche");


// Autocomplétion
AC.autoComplète("départ", url_api, leForm);
AC.autoComplète("arrivée", url_api, leForm);


// Enregistrer les étapes avant de soumettre
function soumettre(){
    const départ = JSON.parse(leForm.données_cachées_départ.value);
    const arrivée = JSON.parse(leForm.données_cachées_arrivée.value);
    console.log(départ, arrivée);
    Pr.envoieLeForm(leForm, [départ, arrivée]);
}

document.getElementById("btn_soumettre").addEventListener(
    "click",
    soumettre
);
