import Base from "../layouts/base.tsx";
import "leaflet/dist/leaflet.css"
import L from "leaflet"
import carteIci from "../fonctions/pour_leaflet.ts";
import { useEffect, useState } from "react";
import FormAutourDeMoi from "../composants/forms/autourDeMoi.tsx";
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';

// Page « Autour de moi »
// Une carte et un formulaire pour chercher des lieux.


export default function AutourDeMoi() {

    let [carte, setCarte] = useState<L.Map | null>(null);
    const marqueurs = new L.LayerGroup();

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
	<Base>
            <Container>
                <Row>
                    <Col md={9} >
	                <div id="laCarte">
                        </div>
	            </Col>
                    <Col>
	                {carte ? <FormAutourDeMoi carte={carte as L.Map} marqueurs={marqueurs} /> : null}
                    </Col>
                </Row>
            </Container>
            
	</Base>
    )
}
