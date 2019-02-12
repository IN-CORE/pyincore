# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import logging

import fiona
import numpy as np
from scipy.spatial import KDTree
import sys
import pyproj
import networkx as nx
import matplotlib.pyplot as plt

from rtree import index
from shapely.geometry import shape, Point

logging.basicConfig(stream = sys.stderr, level = logging.INFO)


class GeoUtil:
    """Utility methods for georeferenced data."""
    @staticmethod
    def get_location(feature):
        """Location of the object.

         Args:
             feature (obj):  A JSON mapping of a geometric object from the inventory.

         Note:
             From the Shapely documentation: The centroid of an object might be one of its points,
             but this is not guaranteed.

         Returns:
             point: A representation of the object’s geometric centroid.

         """
        geom = shape(feature['geometry'])
        return geom.centroid

    @staticmethod
    def find_nearest_feature(features, query_point):
        """Finds the first nearest feature/point in the feature set given a set of features
        from shapefile and one set point.

         Args:
             features (obj):  A JSON mapping of a geometric objects from the inventory.
             query_point (obj): A query point

         Returns:
             obj, obj: A nearest feature and distances

         """
        points = np.asarray([feature['geometry']['coordinates'] for feature in features])
        tree = KDTree(points)
        query_point = np.asarray([[query_point.x, query_point.y]])

        result = tree.query(query_point, 1)

        nearest_feature = features[result[1][0]]
        distances = result[0]

        return nearest_feature, distances

    @staticmethod
    def create_output(filename, source, results, types):
        """Create Fiona output.

        Args:
            filename (str):  A name of a geo dataset resource recognized by Fiona package.
            source (obj): Resource with format driver and coordinate reference system.
            results (obj): Output with key/column names and values.
            types (dict): Schema key names.

        Returns:
            obj: Output with metadata names and values.

        """
        # create new schema
        new_schema = source.schema.copy()
        col_names = results[list(results.keys())[0]].keys()
        for col in col_names:
            new_schema['properties'][col] = types[col]
        empty_data = {}
        for col in col_names:
            empty_data[col] = None

        with fiona.open(
                filename, 'w',
                crs = source.crs,
                driver = source.driver,
                schema = new_schema,
        ) as sink:
            for f in source:
                try:
                    new_feature = f.copy()
                    if new_feature['id'] in results.keys():
                        new_feature['properties'].update(
                            results[new_feature['id']])
                    else:
                        new_feature['properties'].update(empty_data)
                    sink.write(new_feature)
                except Exception as e:
                    logging.exception("Error processing feature %s:", f['id'])

    @staticmethod
    def decimal_to_degree(decimal: float):
        """Convert decimal latitude and longitude to degree to look up in National
        Bridge Inventory.

        Args:
            decimal (float):  Decimal value.

        Returns:
            int: 8 digits int, first 2 digits are degree, another 2 digits are minutes,
                last 4 digits are xx.xx seconds.

        """
        decimal = abs(decimal)
        degree = int(decimal)
        minutes = int((decimal - degree) * 60)
        seconds = (decimal - degree - minutes / 60) * 3600
        overall_degree = format(degree, '02d') + format(minutes, '02d') \
                         + format(int(seconds), '02d') + format(
            int(seconds % 1 * 100), '02d')

        return int(overall_degree)

    @staticmethod
    def degree_to_decimal(degree: int):
        """Convert degree latitude and longitude to degree to look up in National Bridge Inventory.

        Args:
            degree (int):  8 digits int, first 2 digits are degree, another 2 digits are minutes,
            last 4 digits are xx.xx seconds.

        Returns:
            str, int: Decimal value.

        """
        if degree == 0.0 or degree == None or degree == '':
            decimal = 'NA'
        else:
            degree = str(int(degree))
            decimal = int(degree[:-6]) + int(degree[-6:-4])/60 + (int(degree[-4:-2]) + int(degree[-2:])/100)/3600

        return decimal

    def create_network_graph_from_field(filename, fromnode_fldname, tonode_fldname, is_directed = False):
        """Create network graph from field.

        Args:
            filename (str):  A name of a geo dataset resource recognized by Fiona package.
            fromnode_fldname (str): Line feature, from node field name.
            tonode_fldname (str): Line feature, to node field name.
            is_directed (bool, optional (Defaults to False)): Graph type. True for directed Graph,
                False for Graph.

        Returns:
            obj, dict: Graph and coordinates.

        """
        # iterate link
        link = fiona.open(filename)
        fromnode_list = []
        tonode_list = []
        node_list = []
        size = 0

        for line_feature in link:
            from_node_val = line_feature['properties'][fromnode_fldname.lower()]
            to_node_val = line_feature['properties'][tonode_fldname.lower()]
            fromnode_list.append(from_node_val - 1 )
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
        for line_feature in link:
            from_node_val = line_feature['properties'][fromnode_fldname.lower()]
            to_node_val = line_feature['properties'][tonode_fldname.lower()]
            line_geom = (line_feature['geometry'])
            coords_list = line_geom.get('coordinates')
            from_coord = coords_list[0]
            to_coord = coords_list[1]
            coords[int(from_node_val) - 1] = from_coord
            coords[int(to_node_val) - 1] = to_coord

        return graph, coords

    @staticmethod
    def plot_graph_network(graph, coords):
        """Plot graph.

        Args:
            graph (obj):  A nx graph to be drawn.
            coords (dict): Position coordinates.

        """
        # nx.draw(graph, coords, with_lables=True, font_weithg='bold')

        # other ways to draw
        nx.draw_networkx_nodes(graph, coords, cmap=plt.get_cmap('jet'), node_size=100, node_color='g', with_lables=True, font_weithg='bold')
        nx.draw_networkx_labels(graph, coords)
        nx.draw_networkx_edges(graph, coords, edge_color='r', arrows=True)
        plt.show()

    @staticmethod
    def get_network_graph(filename, is_directed=False):
        """Get network graph from filename.

        Args:
            filename (str):  A name of a geo dataset resource recognized by Fiona package.
            is_directed (bool, optional (Defaults to False)): Graph type. True for directed Graph,
                False for Graph.

        Returns:
            obj, dict: Graph and node coordinates.

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
    def validate_network_node_ids(nodefilename, linkfilename, fromnode_fldname, tonode_fldname, nodeid_fldname):
        """Check if the node id in from or to node exist in the real node id.

        Args:
            nodefilename (str):  A name of a geo dataset resource recognized by Fiona package.
            linkfilename (str): A name of the line.
            fromnode_fldname (str): Line feature, from node field name.
            tonode_fldname (str): Line feature, to node field name.
            nodeid_fldname (str): Node field id name.

        Returns:
            bool: Validation of node existence.

        """
        validate = True
        # iterate link
        link = fiona.open(linkfilename)
        link_node_list = []
        for line_feature in link:
            from_node_val = line_feature['properties'][fromnode_fldname.lower()]
            to_node_val = line_feature['properties'][tonode_fldname.lower()]
            link_node_list.append(from_node_val)
            link_node_list.append(to_node_val)

        # iterate node
        node = fiona.open(nodefilename)
        node_list = []
        for node_feature in node:
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

    @staticmethod
    def calc_geog_distance_from_linestring(line_segment, unit=1):
        """Calculate geometric matric from line string segment.

        Args:
            line_segment (obj):  A multi line string with coordinates of segments.
            unit (int, optional (Defaults to 1)): Unit selector, 1: meter, 2: km, 3: mile.

        Returns:
            float: Distance of a line.

        """
        dist = 0
        if (line_segment.__class__.__name__) == "MultiLineString":
            for line in line_segment:
                dist = dist + float(GeoUtil.calc_geog_distance_between_points(Point(line.coords[0]), Point(line.coords[1]), unit))
        elif (line_segment.__class__.__name__) == "LineString":
            dist = float(GeoUtil.calc_geog_distance_between_points(Point(line_segment.coords[0]), Point(line_segment.coords[1]), unit))

        return dist

    @staticmethod
    def calc_geog_distance_between_points(point1, point2, unit=1):
        """Calculate geometric matric between two points, this only works for WGS84 projection.

        Args:
            point1 (Point):  Point 1 coordinates.
            point2 (Point):  Point 2 coordinates.
            unit (int, optional (Defaults to 1)): Unit selector, 1: meter, 2: km, 3: mile.

        Returns:
            str: Distance between points.

        """
        dist = 0
        geod = pyproj.Geod(ellps='WGS84')
        angle1, angle2, distance = geod.inv(point1.x, point1.y, point2.x, point2.y)
        # print(point1.x, point1.y, point2.x, point2.y)
        km = "{0:8.4f}".format(distance / 1000)
        meter = "{0:8.4f}".format(distance)
        mile = float(meter) * 0.000621371

        if unit == 1:
            return meter
        elif unit == 2:
            return km
        elif unit == 3:
            return mile

        return meter


    @staticmethod
    def create_rtree_index(inshp):
        """Create rtree bounding index for an input shape.

        Args:
            inshp (obj):  Shapefile with features.

        Returns:
            obj: rtree bounding box index.

        """
        print("creating node index.....")
        feature_list = []
        for feature in inshp:
            line = shape(feature['geometry'])
            feature_list.append(line)
        idx = index.Index()
        for i in range(len(feature_list)):
            idx.insert(i, feature_list[i].bounds)

        return idx
