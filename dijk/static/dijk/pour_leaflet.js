// Fonctions destinées à être utilisées ailleurs que dans osm-vélo

// https://stackoverflow.com/questions/23567203/leaflet-changing-marker-color
function markerHtmlStyles(coul){
    return `
  background-color: ${coul};
  width: 3rem;
  height: 3rem;
  display: block;
  left: -1.5rem;
  top: -1.5rem;
  position: relative;
  border-radius: 3rem 3rem 0;
  transform: rotate(45deg);
  border: 1px solid gray`;
}

function mon_icone(coul){
    return L.divIcon({
	className: "my-custom-pin",
	iconAnchor: [0, 24],
	labelAnchor: [-6, 0],
	popupAnchor: [0, -36],
	html: `<span style="${markerHtmlStyles(coul)}" />`
    });
}
