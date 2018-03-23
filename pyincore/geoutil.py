import logging

import fiona
import sys
from shapely.geometry import shape

logging.basicConfig(stream = sys.stderr, level = logging.INFO)


class GeoUtil:
    @staticmethod
    def get_location(feature):
        geom = shape(feature['geometry'])
        return geom.centroid

    @staticmethod
    def create_output(filename, source, results, types):
        # the reults is the dictionary

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

