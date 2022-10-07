# -*- coding:utf-8 -*-


#################### Élaguage ####################

import xml.etree.ElementTree as xml  # Manipuler le xml local
from params import CHEMIN_XML


def élague_xml(chemin):
    """
    Entrée : chemin, chemin vers un fichier .osm
             chemin_sortie, autre chemin
            
    Effet : enregistre dans CHEMIN_XML (défini dans params.py) un .osm contenant uniquement les voies, leur id, leur nom et les ref des nœuds qui la composent du .osm initial.
    """

    print(f"Chargement du xml {chemin}")
    a = xml.parse(chemin).getroot()
    print("Création de l'arbre simplifié")
    res = xml.Element("osm")
    for c in a:
        if c.tag == "way":
            fils = xml.SubElement(res, "way")
            fils.attrib["id"] = c.attrib["id"]
            
            for d in c:
                if d.tag == "nd":  # Les nœuds osm sur le way c
                    petit_fils = xml.SubElement(fils, "nd")
                    petit_fils.attrib["ref"] = d.attrib["ref"]
                elif d.tag == "tag" and d.attrib["k"] == "name":  # le nom de c
                    petit_fils = xml.SubElement(fils, "tag")
                    petit_fils.attrib["k"] = "name"
                    petit_fils.attrib["v"] = d.attrib["v"]
    print(f"Enregistrement du xml simplifié dans {CHEMIN_XML}")
    xml.ElementTree(res).write(CHEMIN_XML, encoding="utf-8")

