# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import logging
import numpy as np
from scipy.spatial import KDTree
import sys
import pyproj

from rtree import index
from shapely.geometry import shape, Point, MultiLineString, LineString

import fiona
import uuid
import copy

logging.basicConfig(stream=sys.stderr, level=logging.INFO)


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
             obj: A nearest feature.
             obj: Nearest distances.

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
                crs=source.crs,
                driver=source.driver,
                schema=new_schema,
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
            str: A decimal value.
            int: A decimal value.

        """
        if degree == 0.0 or degree == None or degree == '':
            decimal = 'NA'
        else:
            degree = str(int(degree))
            decimal = int(degree[:-6]) + int(degree[-6:-4]) / 60 + (int(degree[-4:-2]) + int(degree[-2:]) / 100) / 3600

        return decimal

    @staticmethod
    def calc_geog_distance_from_linestring(line_segment, unit=1):
        """Calculate geometric matric from line string segment.

        Args:
            line_segment (Shapely.geometry):  A multi line string with coordinates of segments.
            unit (int, optional (Defaults to 1)): Unit selector, 1: meter, 2: km, 3: mile.

        Returns:
            float: Distance of a line.

        """
        dist = 0
        if isinstance(line_segment, MultiLineString):
            for line in line_segment.geoms:
                dist = dist + float(
                    GeoUtil.calc_geog_distance_between_points(Point(line.coords[0]), Point(line.coords[1]), unit))
        elif isinstance(line_segment, LineString):
            dist = float(
                GeoUtil.calc_geog_distance_between_points(Point(line_segment.coords[0]), Point(line_segment.coords[1]),
                                                          unit))

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

    @staticmethod
    def add_guid(inshp_filename, outshp_filename):
        """Add guid to shapefile

        Args:
            inshp_filename (str):  Full path and filename of Input Shapefile 
            outshp_filename (str): Full path and filename of Ouptut shapefile

        Returns:
            bool: A success or fail to add guid.

        """

        # TODO:
        # - need to handle when there is existing GUID
        # - need to handle when there is existing GUID and some missing guid for some rows
        # - need to handle when input and output are same

        shape_property_list = []
        schema = None
        incrs = None

        try:
            infile = fiona.open(inshp_filename)
            incrs = infile.crs
            # create list of each shapefile entry
            schema = infile.schema.copy()
            schema['properties']['guid'] = 'str:30'
            for in_feature in infile:
                # build shape feature
                tmp_feature = copy.deepcopy(in_feature)
                tmp_feature['properties']['guid'] = str(uuid.uuid4())
                shape_property_list.append(tmp_feature)
        except:
            logging.exception("Error reading/processing feature %s:", inshp_filename)
            return False

        try:
            with fiona.open(outshp_filename, 'w', crs=incrs, driver='ESRI Shapefile', schema=schema) as output:
                for i in range(len(shape_property_list)):
                    new_feature = shape_property_list[i]
                    output.write(new_feature)
        except:
            logging.exception("Error writing features %s:", outshp_filename)
            return False

        return True
