import L from "leaflet"
import { useEffect} from "react";
import carteIci from "../fonctions/pour_leaflet";

type propsCarte = {
    carte: L.Map|null;
    marqueurs: L.LayerGroup;
    setCarte: React.Dispatch<React.SetStateAction<L.Map | null>>;
}


export default function Carte({ carte, setCarte, marqueurs }: propsCarte) {

    useEffect(
	() => {
	    if (!carte) {
		const laCarte=carteIci();
		marqueurs.addTo(laCarte);
		setCarte(laCarte);
	    }else{
		marqueurs.addTo(carte);
	    }
            },
            []
        )


    return (
        <div id="laCarte">
        </div>
    )
}
