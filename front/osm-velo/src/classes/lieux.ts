
import L from "leaflet"
import { Dico, OverpassRes } from "./types.ts";
import { TypeLieu } from "./types-lieux.ts";


class Vecteur {

    x:number;
    y:number;
    
    constructor(x:number, y:number){
	this.x = x;
	this.y = y;
    }

    produitScalaire(autre_vecteur: Vecteur){
	return this.x*autre_vecteur.x + this.y*autre_vecteur.y;
    }
}



export class Lieu {

    static R_terre = 6360000; // en mètres
    static coeff_rad = Math.PI / 180; // Multiplier par ceci pour passer en radians

    coords: L.LatLng;
    infos: Dico = {};
    type_lieu: TypeLieu;
    id?: number;  // id osm
    marqueur : L.Marker;

    

    // Crée l’objet mais aussi un marqueur avec une popup. Le marqueur n’est pas lié à la carte.
    constructor(ll: L.LatLng, type_lieu: TypeLieu,  infos?:Dico, id?:number) {
	this.coords = ll;
        this.type_lieu = type_lieu;
	if (infos){
	    this.infos = infos;
	}
	if (id){
	    this.id = id;
	}
	this.marqueur = new L.Marker(ll)

	const contenu_popup = ["name", "opening_hours", "phone" ]
	    .filter(c=>this.infos[c])
	    .map(c=>this.infos[c])
	    .join("<br>");

	this.marqueur.bindPopup(`<div class="pop">${this.type_lieu.nom}<br>${contenu_popup}</div>`);

    }

    static from_overpass(données: OverpassRes, tousLesTls: TypeLieu[]) {

        // Récupérer le tl
        const tl = tousLesTls.filter(tl =>
            tl.catégorie_osm in données.tags
        ).filter(
            tl => données.tags[tl.catégorie_osm] === tl.nom_osm
        ).pop() as TypeLieu;
        
	const ll = new L.LatLng(données.lat, données.lon);
	const res = new Lieu(ll, tl,  données.tags, données.id);
	return res;
	
    }


    setLatlng(ll: L.LatLng){
	this.coords = ll;
    }

    // Renvoie un objet contenant uniquement les données utiles au serveur.
    // Remet les coords au format [lon, lat]
	// versDjango(){
	// 	const ll = this.getLatlng();
	// 	this.objet_initial.coords = [ll.lng, ll.lat];
	// 	return this.objet_initial;
	// }
	// 
    vecteurVers(autreLieu: Lieu){
	return this.vecteurVersLatLng(autreLieu.coords);
    }

    vecteurVersLatLng(ll2: L.LatLng){
	const ll1 = this.coords;
	const dx = Lieu.R_terre * Math.cos(ll1.lat*Math.PI/180) * (ll2.lng - ll1.lng)*Math.PI/180;
	const dy = Lieu.R_terre * (ll2.lat - ll1.lat)*Math.PI/180;
	return new Vecteur(dx, dy);
	}

}

