// Formulaire « autour de moi »
// Sélectionner des types de lieux pous lancer la recherche sur overpass.

// Entrées:
//    - la carte
//


import chercheLieux from "../../fonctions/chercheLieux.ts"
import { Button, FormGroup, FormControlLabel, Checkbox } from "@mui/material"
import { tous_les_gtls } from "../../données/gtls.ts"
import L from "leaflet"
import { GroupeTypeLieu, TypeLieu } from "../../classes/types-lieux.ts"
import { ChangeEvent, useEffect, useState } from "react"


type props = {
    carte: L.Map;
    marqueurs: L.LayerGroup;
}






export default function FormAutourDeMoi({ carte, marqueurs }: props) {


    ///////////////////////
    //// Envoi du form ////
    ///////////////////////


    async function envoieForm(){
	console.log("J’efface les marqueurs précédents");
	marqueurs.clearLayers();

	// crée les nv marqueurs et les met dans le layerGroup « marqueurs »
	(await chercheLieux(carte as L.Map, typesLieuxSélectionnés())).forEach(
	    lieu => marqueurs.addLayer(lieu.marqueur)
	);
	console.log("Marqueurs après", marqueurs);
        marqueurs.addTo(carte);
    }

    

    ////////////////////////////////////
    //// Gestion des types de lieux ////
    ////////////////////////////////////


    // la liste des type de lieux : c’est un dico type_lieu -> bool
    const [type_lieux_sélectionnés, setTlsSélectionnés] = useState(new Map<TypeLieu, boolean>());

    

    
    // fonction renvoyant la fonction pour changer un tl
    function changeTl(tl: TypeLieu){
		return (_event:ChangeEvent<HTMLInputElement>, checked:boolean) => setTlsSélectionnés(
			prev => new Map(prev.set(tl, checked))
		);
    }
    
    // Fonction finale pour récupérer le tableau des types_lieux sélectionnés
    function typesLieuxSélectionnés() {
	const res = [];
	for (const tl of type_lieux_sélectionnés.keys()) {
	    if (type_lieux_sélectionnés.get(tl)) {
		res.push(tl);
	    }
	};
	return res;
    }


    
    //////////////////////////////////////////////
    //// Gestion des groupes de types de lieu ////
    //////////////////////////////////////////////
    

    // state pour les gtls sélectionnés: pour savoir si on affiche la liste des types de lieux correspondant
    const [gtls_cliqués, setGtlsCliqués] = useState(new Map<GroupeTypeLieu, boolean>());


    function setGtlCliqué(gtl: GroupeTypeLieu, checked: boolean) {
	setGtlsCliqués(
	    prev => new Map(prev.set(gtl, checked)) // Il faut faire un new Map sans quoi React ne se rend pas compte qu’elle a changé
	)
    }
    

    // Appelé lors d’un clic sur gtl
    // marque tous les tls correspondant
    // et marque cliqué ou pas le gtl, ce qui fera apparaître les sous-checkboxes
    function changeGtl(gtl: GroupeTypeLieu) {
	return (
	    (_event: ChangeEvent<HTMLInputElement>, checked: boolean) => {
		// màj tous les tl lié à ce gtl
			gtl.types_lieux.forEach(
				tl => type_lieux_sélectionnés.set(tl, checked)
			);
		// marque le gtl
		setGtlCliqué(gtl, checked);
	    }
	)
    }
    

    // renvoie le fragment de formulaire lié au gtl passé en arg.
    // une checkbox pour le gtl, et celles des tl correspondant si le gtl est sélectionné.
    function checkBoxOfGtl(gtl: GroupeTypeLieu) {

        // les sous-cb pour les types_lieux du gtl
	const sous_checkboxes = gtl.types_lieux.map(
	    tl =>
		<li key={gtl+toString()+tl.toString()} list-style-type:none>
		    <FormControlLabel
			control={< Checkbox
			    onChange={changeTl(tl)}
			    checked={type_lieux_sélectionnés.get(tl)}
						/>}
				label={tl.toString()}
		    />
		</li>
            
		);
        
	return (
	    <FormGroup>
		<FormControlLabel key={gtl.toString()}
				  control={<Checkbox
					       onChange={changeGtl(gtl)}
                                               indeterminate={gtl.unMaisPasTous(type_lieux_sélectionnés)}
                                               checked={gtl.types_lieux.every(tl => type_lieux_sélectionnés.get(tl))}
					   />}
				      label={gtl.toString()}
		/>
		{// Afficher les sous-checkboxes si le gtl est sélectionné
		gtls_cliqués.get(gtl) ? <ul> {sous_checkboxes}</ul> : null
                
		}
	    </FormGroup>
	)
    }


    ////////////////////////
    //// Initialisation ////
    ////////////////////////

	useEffect(
	    () => {
		// les gtls
		const tout_faux = new Map<GroupeTypeLieu, boolean>();
		tous_les_gtls.forEach(
		    gtl => tout_faux.set(gtl, false)
		);
		setGtlsCliqués(tout_faux);
		// les types de lieux
		const tous_les_tls = new Map();
		tous_les_gtls.forEach(
		    gtl => {
			gtl.types_lieux.forEach(tl => tous_les_tls.set(tl, false))
		    }
		);
		setTlsSélectionnés(tous_les_tls);
		
	    },
	    []
	);



    /////////////////
    //// Le html ////
    /////////////////
    
	return (
		<form >
			<FormGroup>

				{tous_les_gtls.map(checkBoxOfGtl)}

				<Button
					variant="contained"
					onClick={envoieForm}
				>
					Chercher les lieux
				</Button>
			</FormGroup>
		</form>

	)
}
