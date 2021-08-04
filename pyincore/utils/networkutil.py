import fiona
import csv
import copy
import uuid
import networkx as nx
import matplotlib.pyplot as plt

from shapely.geometry import shape, LineString, Point, mapping
from fiona.crs import from_epsg


class NetworkUtil:
    @staticmethod
    def build_dataset_by_node(node_filename, graph_filename, id_field, out_filename):
        """Create line dataset based on node shapefile and graph file graph should be in csv format.

        Args:
            node_filename (string):  A node shapefile file name pull path with *.shp file extension.
            graph_filename (string): A graph csv file name pull path.
            id_field (string): A field name for node shapefiles unique id that matches the information in the graph.
            out_filename (string): A line file name pull path that will be newly created by the process.

        Returns:
            bool: To indicated if the line was created or not.

        """
        # read graph
        with open(graph_filename) as f:
            reader = csv.reader(f, delimiter=',')
            graph_list = list(reader)
        # remove the first element, which is a header, from a list
        graph_list.pop(0)

        # read node shapefile and make it as a list so it can be accessed for the building line file
        # also, add uuid in the field
        innode = fiona.open(node_filename)

        # create list of each shapefile entry
        node_list = []
        node_id_list = []

        # create a schema for output line file
        schema = {
            'geometry': 'LineString',
            'properties': {
                'linkid': 'str:10',
                'uuid': 'str:30',
                'from_node': 'str:10',
                'to_node': 'str:10'
            }
        }

        for in_feature in innode:
            # build shape feature
            tmp_feature = copy.deepcopy(in_feature)
            tmp_feature['properties']['uuid'] = str(uuid.uuid4())
            node_id = str(tmp_feature['properties'][id_field])
            node_list.append(tmp_feature)
            node_id_list.append(node_id)

        # iterate graph and find from-node and to-node geography
        line_geom_list = []
        line_id_list = []
        line_from_list = []
        line_to_list = []
        for graph_row in graph_list:
            line_id = str(graph_row[0])
            from_id = str(graph_row[1])
            to_id = str(graph_row[2])
            line_id_list.append(line_id)
            line_from_list.append(from_id)
            line_to_list.append(to_id)

            # initialize the location
            from_location_in_node_list = 0
            to_location_in_node_list = 0
            for i in range(len(node_id_list)):
                if str(node_id_list[i]) == from_id:
                    from_location_in_node_list = i
                if str(node_id_list[i]) == to_id:
                    to_location_in_node_list = i

            from_geo = node_list[from_location_in_node_list]['geometry']
            to_geo = node_list[to_location_in_node_list]['geometry']
            line_geom = LineString([Point(shape(from_geo).coords), Point(shape(to_geo).coords)])
            line_geom_list.append(line_geom)

        # create line feature
        with fiona.open(out_filename, 'w', crs=from_epsg(4326), driver='ESRI Shapefile', schema=schema) as layer:
            for i in range(len(line_geom_list)):
                # filling schema
                schema['geometry'] = mapping(line_geom_list[i])
                schema['properties']['linkid'] = line_id_list[i]
                schema['properties']['uuid'] = str(uuid.uuid4())
                schema['properties']['from_node'] = line_from_list[i]
                schema['properties']['to_node'] = line_to_list[i]

                layer.write(schema)

        return True

    @staticmethod
    def build_dataset_by_line(line_filename, line_id_field, fromnode_field, tonode_field, out_node_filename,
                              out_graph_filename):
        """Create node dataset based on line shapefile and graph file graph should be in csv format

        Args:
            line_filename (string):  line shapefile file name pull path with *.shp file extension.
            line_id_field (string): line shapefile unique id field
            fromnode_field (string): field name for fromnode in line shapefile
            tonode_field (string): field name for tonode in line shapefile
            out_node_filename (string): output node shapefile name with *.shp extension
            out_graph_filename (string): output graph csv file name with *.csv extension

        Returns:
            bool: To indicated if the shapefile and graph were created or not.

        """
        # read line shapefile
        linefile = fiona.open(line_filename)

        node_list = []
        node_id_list = []
        graph_list = []

        for line in linefile:
            line_geom = shape(line['geometry'])
            seg_coord_list = list(line_geom.coords)

            # to check if this is a multiline string
            if len(seg_coord_list) > 2:
                print("The line shapefile is a multiline string. The process will be aborted")
                return False

            line_id = str(line['properties'][line_id_field])
            fromnode_id = str(line['properties'][fromnode_field])
            tonode_id = str(line['properties'][tonode_field])
            fromnode_coord = seg_coord_list[0]
            tonode_coord = seg_coord_list[1]
            graph_line_list = []
            graph_line_list.append(line_id)
            graph_line_list.append(fromnode_id)
            graph_line_list.append(tonode_id)
            graph_list.append(graph_line_list)

            # check if to from node is in the node_id_list
            is_new_node = True
            for i in range(len(node_id_list)):
                if fromnode_id == node_id_list[i]:
                    is_new_node = False
                    break
            if is_new_node:
                node_id_list.append(fromnode_id)
                node_list.append(Point(fromnode_coord))

            # check if to to node is in the node_id_list
            is_new_node = True
            for i in range(len(node_id_list)):
                if tonode_id == node_id_list[i]:
                    is_new_node = False
                    break
            if is_new_node:
                node_id_list.append(tonode_id)
                node_list.append(Point(tonode_coord))

        # create a schema for output line file
        schema = {
            'geometry': 'Point',
            'properties': {
                'nodeid': 'str:10',
                'uuid': 'str:30'
            }
        }

        # create output node feature
        with fiona.open(out_node_filename, 'w', crs=from_epsg(4326), driver='ESRI Shapefile', schema=schema) as layer:
            for i in range(len(node_id_list)):
                # filling schema
                schema['geometry'] = mapping(node_list[i])
                schema['properties']['nodeid'] = node_id_list[i]
                schema['properties']['uuid'] = str(uuid.uuid4())

                layer.write(schema)

        with open(out_graph_filename, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerows([[line_id_field, fromnode_field, tonode_field]])
            writer.writerows(graph_list)

        return True

    @staticmethod
    def create_network_graph_from_field(indataset, fromnode_fldname, tonode_fldname, is_directed=False):
        """Create network graph from field.

        Args:
            indataset (str):  A name of a geo dataset resource recognized by Fiona package.
            fromnode_fldname (str): Line feature, from node field name.
            tonode_fldname (str): Line feature, to node field name.
            is_directed (bool, optional (Defaults to False)): Graph type. True for directed Graph,
                False for Graph.

        Returns:
            obj: A graph from field.
            dict: Coordinates.

        """
        # iterate link
        fromnode_list = []
        tonode_list = []
        node_list = []
        size = 0

        for line_feature in indataset:
            if fromnode_fldname in line_feature["properties"]:
                from_node_val = line_feature['properties'][fromnode_fldname]
            elif fromnode_fldname.lower() in line_feature["properties"]:
                from_node_val = line_feature['properties'][fromnode_fldname.lower()]
            if tonode_fldname in line_feature["properties"]:
                to_node_val = line_feature['properties'][tonode_fldname]
            elif tonode_fldname.lower() in line_feature["properties"]:
                to_node_val = line_feature['properties'][tonode_fldname.lower()]
            fromnode_list.append(from_node_val - 1)
            tonode_list.append(to_node_val - 1)
            node_list.append(from_node_val - 1)
            node_list.append(to_node_val - 1)

        # create node list
        node_list.sort()
        node_list = list(set(node_list))

        # create graph
        graph = None
        if is_directed:
            graph = nx.DiGraph()
        else:
            graph = nx.Graph()

        for i in range(len(fromnode_list)):
            graph.add_edge(fromnode_list[i], tonode_list[i])

        # initialize coords dictionary
        coords = dict((i, None) for i in range(len(node_list) - 1))

        # create coordinates
        node_coords_list = [None] * (len(node_list))
        for line_feature in indataset:
            if fromnode_fldname in line_feature["properties"]:
                from_node_val = line_feature['properties'][fromnode_fldname]
            elif fromnode_fldname.lower() in line_feature["properties"]:
                from_node_val = line_feature['properties'][fromnode_fldname.lower()]
            if tonode_fldname in line_feature["properties"]:
                to_node_val = line_feature['properties'][tonode_fldname]
            elif tonode_fldname.lower() in line_feature["properties"]:
                to_node_val = line_feature['properties'][tonode_fldname.lower()]
            line_geom = (line_feature['geometry'])
            coords_list = line_geom.get('coordinates')
            from_coord = coords_list[0]
            to_coord = coords_list[1]
            coords[int(from_node_val) - 1] = from_coord
            coords[int(to_node_val) - 1] = to_coord

        return graph, coords

    @staticmethod
    def plot_network_graph(graph, coords):
        """Plot graph.

        Args:
            graph (obj):  A nx graph to be drawn.
            coords (dict): Position coordinates.

        """
        # nx.draw(graph, coords, with_lables=True, font_weithg='bold')

        # other ways to draw
        nx.draw_networkx_nodes(graph, coords, cmap=plt.get_cmap('jet'), node_size=100, node_color='g', with_lables=True,
                               font_weithg='bold')
        nx.draw_networkx_labels(graph, coords)
        nx.draw_networkx_edges(graph, coords, edge_color='r', arrows=True)
        plt.show()

    @staticmethod
    def read_network_graph_from_file(filename, is_directed=False):
        """Get network graph from filename.

        Args:
            filename (str):  A name of a geo dataset resource recognized by Fiona package.
            is_directed (bool, optional (Defaults to False)): Graph type. True for directed Graph,
                False for Graph.

        Returns:
            obj: A graph from field.
            dict: Coordinates.

        """
        geom = nx.read_shp(filename)
        node_coords = {k: v for k, v in enumerate(geom.nodes())}
        # create graph
        graph = None
        if is_directed:
            graph = nx.DiGraph()
        else:
            graph = nx.Graph()

        graph.add_nodes_from(node_coords.keys())
        l = [set(x) for x in geom.edges()]
        edg = [tuple(k for k, v in node_coords.items() if v in sl) for sl in l]

        graph.add_edges_from(edg)

        return graph, node_coords

    @staticmethod
    def validate_network_node_ids(nodedataset, linkdataset, fromnode_fldname, tonode_fldname, nodeid_fldname):
        """Check if the node id in from or to node exist in the real node id.

        Args:
            nodedataset (str):  A name of a node geo dataset resource recognized by Fiona package.
            linkdataset (str): A name of a link geo dataset resource recognized by Fiona package.
            fromnode_fldname (str): Line feature, from node field name.
            tonode_fldname (str): Line feature, to node field name.
            nodeid_fldname (str): Node field id name.

        Returns:
            bool: Validation of node existence.

        """
        validate = True
        # iterate link
        link_node_list = []
        for line_feature in linkdataset:
            if fromnode_fldname in line_feature["properties"]:
                from_node_val = line_feature['properties'][fromnode_fldname]
            elif fromnode_fldname.lower() in line_feature["properties"]:
                from_node_val = line_feature['properties'][fromnode_fldname.lower()]
            if tonode_fldname in line_feature["properties"]:
                to_node_val = line_feature['properties'][tonode_fldname]
            elif tonode_fldname.lower() in line_feature["properties"]:
                to_node_val = line_feature['properties'][tonode_fldname.lower()]
            link_node_list.append(from_node_val)
            link_node_list.append(to_node_val)

        # iterate node
        node_list = []
        for node_feature in nodedataset:
            if nodeid_fldname in node_feature["properties"]:
                node_val = node_feature['properties'][nodeid_fldname]
            elif nodeid_fldname.lower() in node_feature["properties"]:
                node_val = node_feature['properties'][nodeid_fldname.lower()]
            node_list.append(node_val)

        link_node_list.sort()
        node_list.sort()
        link_node_list = list(set(link_node_list))
        node_list = list(set(node_list))

        for node in link_node_list:
            if node in node_list == False:
                validate = False

        return validate
