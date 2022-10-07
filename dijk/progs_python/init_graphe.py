# -*- coding:utf-8 -*-

### Fichier destiné à être chargé à chaque utilisation ###


#import networkx as nx
from time import perf_counter
from petites_fonctions import chrono
from params import RACINE_PROJET, DONNÉES, BBOX_DÉFAUT

# tic=perf_counter()
# from graphe_par_networkx import Graphe_nw
# chrono(tic, "graphe_par_networkx")

tic=perf_counter()
from module_graphe import  Graphe_mélange  # ma classe de graphe
chrono(tic, "module_graphe")

#from initialisation.ajoute_villes import ajoute_villes
#import initialisation.noeuds_des_rues as nr

# tic=perf_counter()
# import networkx as nx
# chrono(tic, "networkx")

#tic=perf_counter()
#from osmnx.io import load_graphml#, save_graphml
#chrono(tic, "Chargement de osmnx.io.load_graphml (depuis init_graphe)")

import subprocess
import os
#ox.config(use_cache=True, log_console=True)


## Pour load_graphml
from shapely import wkt
from pathlib import Path
import ast

# Pour la simplification dans osmnx :
# https://github.com/gboeing/osmnx-examples/blob/master/notebooks/04-simplify-graph-consolidate-nodes.ipynb

# filtrage
# https://stackoverflow.com/questions/63466207/how-to-create-a-filtered-graph-from-an-osm-formatted-xml-file-using-osmnx


#################### Récupération du graphe  ####################




def charge_graphe(bbox=BBOX_DÉFAUT, option={"network_type":"all"}, bavard=1):
    """
    Renvoie le graphe (instance de Graphe) correspondant à la bbox indiquée.
    """
    
<<<<<<< HEAD
    s,o,n,e = bbox 
    nom_fichier = f'{DONNÉES}/{s}{o}{n}{e}.graphml'
    if bavard>0:print(f"Nom du fichier du graphe : {nom_fichier}")
    if os.path.exists(nom_fichier):
        tic=perf_counter()
        g = load_graphml(nom_fichier)
        #g = read_graphml(nom_fichier, node_type=int)
        if bavard>0:
            print("Graphe en mémoire !")
            chrono(tic, f"load_graphml({nom_fichier})")
    else:
        print(f"\nGraphe pas en mémoire à {nom_fichier}, je le charge via osmnx.\\")

        à_exécuter = [
            os.path.join(RACINE_PROJET, "progs_python/initialisation/crée_graphe.py"),
            nom_fichier,
            str(bbox)
        ]
        if bavard>0:print(à_exécuter)
        sortie = subprocess.run(à_exécuter)
        if bavard>1:print(sortie.stdout)
        print(sortie.stderr)
        g = load_graphml(nom_fichier)
        #g = read_graphml(nom_fichier, node_type=int)
=======
    # s,o,n,e = bbox 
    # nom_fichier = f'{DONNÉES}/{s}{o}{n}{e}.graphml'
    # if bavard>0:print(f"Nom du fichier du graphe : {nom_fichier}")
    # if os.path.exists(nom_fichier):
    #     tic=perf_counter()
    #     g = load_graphml(nom_fichier)
    #     #g = read_graphml(nom_fichier, node_type=int)
    #     if bavard>0:
    #         print("Graphe en mémoire !")
    #         chrono(tic, f"osmnx.io.load_graphml({nom_fichier})")
    # else:
    #     print(f"\nGraphe pas en mémoire à {nom_fichier}, je le charge via osmnx.\\")

    #     à_exécuter = [
    #         os.path.join(RACINE_PROJET, "progs_python/initialisation/crée_graphe.py"),
    #         nom_fichier,
    #         str(bbox)
    #     ]
    #     if bavard>0:print(à_exécuter)
    #     sortie = subprocess.run(à_exécuter)
    #     if bavard>1:print(sortie.stdout)
    #     print(sortie.stderr)
    #     g = load_graphml(nom_fichier)
    #     #g = read_graphml(nom_fichier, node_type=int)
>>>>>>> sommets_par_django
        
    #gr = Graphe(Graphe_mélange(g))
    gr=Graphe_mélange("nimp")

    #gr.g.simplifie()
    #save_graphml(g, nom_fichier)
    
    # gr.g.charge_cache()  # nœud_of_rue
    
    # print("Chargement de la cyclabilité")
    # tic=perf_counter()
    # cycla_max=gr.g.charge_cycla()
    # gr.cycla_max=cycla_max
    # chrono(tic, "ajout de la cycla au graphe")
    

    # print("Ajout du nom des villes")
    # tic=perf_counter()
    # ajoute_villes(gr, bavard=bavard-1)
    # chrono(tic, "ajout du nom des villes au graphe")

    # Plus besoin vu que les rues sont dans la base Django
    # print("Ajout de la liste des nœuds de chaque rue")
    # tic=perf_counter()
    # nr.charge_csv(gr)
    # chrono(tic, "ajout de la liste des nœuds de chaque rue au graphe.")
    
    print("Chargement du graphe fini.\n")
    return gr








### fonction de chargement du graphe (pour éviter de charger osmnx entier) ###


def load_graphml(filepath, node_dtypes=None, edge_dtypes=None, graph_dtypes=None):
    """
    Load an OSMnx-saved GraphML file from disk.

    This converts node, edge, and graph-level attributes (serialized as
    strings) to their appropriate data types. These can be customized as
    needed by passing in dtypes arguments providing types or custom converter
    functions. For example, if you want to convert some attribute's values to
    `bool`, consider using the built-in `ox.io._convert_bool_string` function
    to properly handle "True"/"False" string literals as True/False booleans:
    `ox.load_graphml(fp, node_dtypes={my_attr: ox.io._convert_bool_string})`

    If you manually configured the `all_oneway=True` setting, you may need to
    manually specify here that edge `oneway` attributes should be type `str`.

    Parameters
    ----------
    filepath : string or pathlib.Path
        path to the GraphML file
    node_dtypes : dict
        dict of node attribute names:types to convert values' data types. the
        type can be a python type or a custom string converter function.
    edge_dtypes : dict
        dict of edge attribute names:types to convert values' data types. the
        type can be a python type or a custom string converter function.
    graph_dtypes : dict
        dict of graph-level attribute names:types to convert values' data
        types. the type can be a python type or a custom string converter
        function.

    Returns
    -------
    G : networkx.MultiDiGraph
    """
    filepath = Path(filepath)

    # specify default graph/node/edge attribute values' data types
    default_graph_dtypes = {"simplified": _convert_bool_string}
    default_node_dtypes = {
        "elevation": float,
        "elevation_res": float,
        "lat": float,
        "lon": float,
        "osmid": int,
        "street_count": int,
        "x": float,
        "y": float,
    }
    default_edge_dtypes = {
        #"bearing": float,
        #"grade": float,
        #"grade_abs": float,
        "length": float,
        "oneway": _convert_bool_string,
        "osmid": int,
        #"speed_kph": float,
        #"travel_time": float,
    }

    # override default graph/node/edge attr types with user-passed types, if any
    if graph_dtypes is not None:
        default_graph_dtypes.update(graph_dtypes)
    if node_dtypes is not None:
        default_node_dtypes.update(node_dtypes)
    if edge_dtypes is not None:
        default_edge_dtypes.update(edge_dtypes)

    # read the graphml file from disk
    G = nx.read_graphml(filepath, node_type=default_node_dtypes["osmid"], force_multigraph=True)

    # convert graph/node/edge attribute data types
    print("Converting node, edge, and graph-level attribute data types")
    G = _convert_graph_attr_types(G, default_graph_dtypes)
    G = _convert_node_attr_types(G, default_node_dtypes)
    G = _convert_edge_attr_types(G, default_edge_dtypes)

    print(f'Loaded graph with {len(G)} nodes and {len(G.edges)} edges from "{filepath}"')
    return G


def _convert_graph_attr_types(G, dtypes=None):
    """
    Convert graph-level attributes using a dict of data types.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        input graph
    dtypes : dict
        dict of graph-level attribute names:types

    Returns
    -------
    G : networkx.MultiDiGraph
    """
    # remove node_default and edge_default metadata keys if they exist
    G.graph.pop("node_default", None)
    G.graph.pop("edge_default", None)

    for attr in G.graph.keys() & dtypes.keys():
        G.graph[attr] = dtypes[attr](G.graph[attr])

    return G


def _convert_node_attr_types(G, dtypes=None):
    """
    Convert graph nodes' attributes using a dict of data types.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        input graph
    dtypes : dict
        dict of node attribute names:types

    Returns
    -------
    G : networkx.MultiDiGraph
    """
    for _, data in G.nodes(data=True):
        for attr in data.keys() & dtypes.keys():
            data[attr] = dtypes[attr](data[attr])
    return G


def _convert_edge_attr_types(G, dtypes=None):
    """
    Convert graph edges' attributes using a dict of data types.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        input graph
    dtypes : dict
        dict of edge attribute names:types

    Returns
    -------
    G : networkx.MultiDiGraph
    """
    # for each edge in the graph, eval attribute value lists and convert types
    for _, _, data in G.edges(data=True, keys=False):

        # remove extraneous "id" attribute added by graphml saving
        data.pop("id", None)

        # first, eval stringified lists to convert them to list objects
        # edge attributes might have a single value, or a list if simplified
        for attr, value in data.items():
            if value.startswith("[") and value.endswith("]"):
                try:
                    data[attr] = ast.literal_eval(value)
                except (SyntaxError, ValueError):
                    pass

        # next, convert attribute value types if attribute appears in dtypes
        for attr in data.keys() & dtypes.keys():
            if isinstance(data[attr], list):
                # if it's a list, eval it then convert each item
                data[attr] = [dtypes[attr](item) for item in data[attr]]
            else:
                # otherwise, just convert the single value
                data[attr] = dtypes[attr](data[attr])

        # if "geometry" attr exists, convert its well-known text to LineString
        if "geometry" in data:
            data["geometry"] = wkt.loads(data["geometry"])

    return G


def _convert_bool_string(value):
    """
    Convert a "True" or "False" string literal to corresponding boolean type.

    This is necessary because Python will otherwise parse the string "False"
    to the boolean value True, that is, `bool("False") == True`. This function
    raises a ValueError if a value other than "True" or "False" is passed.

    If the value is already a boolean, this function just returns it, to
    accommodate usage when the value was originally inside a stringified list.

    Parameters
    ----------
    value : string {"True", "False"}
        the value to convert

    Returns
    -------
    bool
    """
    if value in {"True", "False"}:
        return value == "True"
    elif isinstance(value, bool):
        return value
    else:  # pragma: no cover
        raise ValueError(f'invalid literal for boolean: "{value}"')
