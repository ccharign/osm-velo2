export class BoundingBox{
    s:number;
    o:number;
    n: number;
    e:number;

    constructor(s:number, o:number, n:number, e:number){
	this.s=s;
	this.o=o;
	this.n=n;
	this.e=e;
    }

    toOverpass(){
	return `(${this.s},${this.o},${this.n},${this.e})`
    }

    static ofCarte(carte:L.Map){
	const bounds = carte.getBounds();
	const ne = bounds.getNorthEast();
	const n = ne.lat;
	const e = ne.lng;
	const so = bounds.getSouthWest();
	const s = so.lat;
	const o = so.lng;
	return new BoundingBox(s,o,n,e)
    }
}
