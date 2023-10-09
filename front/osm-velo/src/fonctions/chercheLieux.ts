import { Lieu } from "../classes/lieux.ts";
import { OverpassRes } from "../classes/types.ts";
import { BoundingBox } from "../classes/bounding-box.ts";
import { TypeLieu } from "../classes/types-lieux.ts";



function tlsMêmeCatégorieVersOverpass(tls:TypeLieu[], catégorie:string){

    // exemple node["amenity"~(pub|bar|restaurant)]
    return `node[${catégorie}~"^(${tls.map(tl => tl.nom_osm).join("|")})$"]`
}


export default async function chercheLieux(carte: L.Map, types_de_lieux: TypeLieu[]): Promise<Lieu[]> {
    
    console.log("Lieux recherchés :", types_de_lieux);
    const bb = BoundingBox.ofCarte(carte);

    // On regroupe les tl par catégorie osm
    const tl_par_catégorie = new Map<string, TypeLieu[]>();

    for (const tl of types_de_lieux){
        if (tl_par_catégorie.has(tl.catégorie_osm)){
            tl_par_catégorie.get(tl.catégorie_osm)?.push(tl)
        }else{
            tl_par_catégorie.set(tl.catégorie_osm, [tl])
        }
    }

    // Création de la requête
    let requête =  "[out:json][timeout:25];";

    for (const catégorie of tl_par_catégorie.keys()){
        requête += tlsMêmeCatégorieVersOverpass(tl_par_catégorie.get(catégorie) as TypeLieu[], catégorie) + bb.toOverpass()+";";
    }
    
    requête += "out body;";
    console.log(requête);

    // Envoi de la requête
    const res_req = await fetch('https://www.overpass-api.de/api/interpreter?'+"data="+requête);
    const res_overpass = await res_req.json();
    const lieux = res_overpass.elements.map( (x:OverpassRes) => Lieu.from_overpass(x, types_de_lieux));
    console.log("lieux reçus d’overpass", lieux);
    return lieux;
}


