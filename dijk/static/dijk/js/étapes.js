
// Classe de base pour une étape
export class Étape{

    constructor(o=null){
	this.objet_initial = o;
    }

    versDjango(){
	return this.objet_initial;
    }

    màj(o){
	this.objet_initial = o;
    }
}


class Vecteur{
    
    constructor(x, y){
	this.x = x;
	this.y = y;
    }

    produitScalaire(autre_vecteur){
	return this.x*autre_vecteur.x + this.y*autre_vecteur.y;
    }
}


// Les objet de cette classe sont des étapes munies de coords
// le calcul de vecteurs et produit scalaires est implémenté
export class ÉtapeAvecCoords extends Étape{

    static R_terre = 6360000; // en mètres
    static coeff_rad = Math.PI/180; // Multiplier par ceci pour passer en radians

    constructor(o, ll){
	super(o);
	this.latLng = ll;
    }
    
    getLatlng(){
	return this.latLng;
    }

    setLatlng(ll){
	this.latLng = ll;
    }

    // Renvoie un objet contenant uniquement les données utiles au serveur.
    // Remet les coords au format [lon, lat]
    versDjango(){
	const ll = this.getLatlng();
	this.objet_initial.coords = [ll.lng, ll.lat];
	return this.objet_initial;
    }

        vecteurVers(autreÉtape){
	return this.vecteurVersLatLng(autreÉtape.getLatlng());
    }

    vecteurVersLatLng(ll2){
	const ll1 = this.getLatlng();
	const dx = ÉtapeAvecCoords.R_terre * Math.cos(ll1.lat*Math.PI/180) * (ll2.lng - ll1.lng)*Math.PI/180;
	const dy = ÉtapeAvecCoords.R_terre * (ll2.lat - ll1.lat)*Math.PI/180;
	return new Vecteur(dx, dy);
    }

}
