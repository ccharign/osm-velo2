import Base from "../../src/layouts/base"
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Carte from "../composants/carte.tsx";
import { useState } from "react";
import L from "leaflet";


export default function Itinéraires() {

    let [carte, setCarte] = useState<L.Map | null>(null);
    const marqueurs = new L.LayerGroup();

    return (
        <Base>
            <p>Recherche d’itinéraires</p>

            <Container>
                <Row>

                    <Col md={9} >
                        <Carte carte={carte} setCarte={setCarte} marqueurs={marqueurs} />
                    </Col>

                    <Col>
                        {carte ? <FormAutourDeMoi carte={carte as L.Map} marqueurs={marqueurs} /> : null}
                    </Col>

                </Row>
            </Container>


        </Base>
    )
}
