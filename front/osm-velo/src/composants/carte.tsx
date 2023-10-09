import L from "leaflet"

type propsCarte = {
    carte: L.Map;
    marqueurs: L.LayerGroup
}


export default function Carte({carte, marqueurs}:propsCarte){

    
    
    return(
        <div id="laCarte">
        </div>
    )
}
