# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import geopandas as gpd
import pandas as pd
from shapely import wkt


class PopdislOutputProcessUtil:
    """This class converts various population dislocation results outputs to json format and shapefiles."""

    @staticmethod
    def get_heatmap_shp(pop_dislocation_result, pop_dislocation_result_path=None,
                        filter_on=True, filename="pop-disl-numprec.shp"):
        """Convert and filter opulation dislocatin output to shapefile that contains only guid and numprec column
            Args:
                pop_dislocation_result (obj): IN-CORE output of populationdislocation.
                pop_dislocation_result_path (string): Direct path of the csv of population dislocation result. A
                fallback for the case that object of popdisl is not provided.
                filename (str): Path and name to save json output file in. E.g "heatmap.shp"

            Returns:
                filename: full path and filename of the shapefile
        """
        if pop_dislocation_result_path:
            df = pd.read_csv(pop_dislocation_result_path, low_memory=False)
        else:
            df = pop_dislocation_result.get_dataframe_from_csv()

        df['geometry'] = df['geometry'].apply(wkt.loads)

        # only keep dislocated & guid
        if filter_on:
            df = df[(df['dislocated']) & (df['guid'].notnull()) & (df["numprec"].notnull())]

        # save as shapefile
        gdf = gpd.GeoDataFrame(df, crs='epsg:4326')
        gdf = gdf[["guid", "numprec", "geometry"]]
        gdf.to_file(filename)

        return filename
