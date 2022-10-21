# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import BaseAnalysis, AnalysisUtil
from shapely.ops import unary_union
from geovoronoi import voronoi_regions_from_coords, points_to_coords
import geopandas as gpd
import pandas as pd
import osmnx as ox
import numpy as np


class ElectricPowerAvailability(BaseAnalysis):
    """Building Damage Analysis calculates the probability of building damage based on
    different hazard type such as earthquake, tsunami, and tornado.

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        super(ElectricPowerAvailability, self).__init__(incore_client)

    def run(self):
        """Executes building power availability analysis."""
        # inventory dataset
        bldg_inv_gdf = self.get_input_dataset("buildings").get_dataframe_from_shapefile()
        sbustations_gdf = self.get_input_dataset("epfs").get_dataframe_from_shapefile()
        epf_damage = self.get_input_dataset("epf_damage").get_dataframe_from_shapefile()
        city_polygon = self.get_input_dataset("city_polygon").get_dataframe_from_shapefile()

        bldg_infra_availability = self.building_power_availability(bldg_inv_gdf, sbustations_gdf, epf_damage,
                                                                   city_polygon).drop(columns=['geometry'])
        # get substation guid and put it in the table
        self.set_result_csv_data("power_availability", bldg_infra_availability, name=self.get_parameter(
            "result_name")+"_power_availability", source='dataframe')

        return True

    def building_power_availability(self, bldg_inv_gdf, sbustations_gdf, epf_damage, city_polygon):
        """Run analysis for multiple buildings.

        Args:


        Returns:

        """
        # is flooded or not
        substation_flooded = ElectricPowerAvailability.is_substation_flooded(epf_damage)

        poly_shapes, pts = ElectricPowerAvailability.service_areas_to_substations(city_polygon, sbustations_gdf)

        # Create dataframe to keep track of access to infrastructure
        bldg_infra_availability = bldg_inv_gdf[['guid', 'geometry']]

        # Initialize substation index that services building
        bldg_infra_availability = bldg_infra_availability.assign(substation_guid="NA")

        # Create empty list to hold gpd dataframes corresponding to buildings in each substation
        bldg_groups = []

        # For each substation, identify buildings being serviced and assign state of substation functionality
        region_polygons = []
        for poly_shape_idx in range(len(poly_shapes)):
            idx = poly_shape_idx
            region_polygon = gpd.GeoDataFrame()
            region_polygon['geometry'] = None
            region_polygon.loc[0, 'geometry'] = poly_shapes[idx]
            region_polygon = region_polygon.set_crs("epsg:4326")

            region_polygons.append(region_polygon)

            bldg_points_within_region = gpd.sjoin(bldg_infra_availability, region_polygon, op='within', how='inner')
            bldg_points_within_region = pd.concat([bldg_points_within_region, pd.Series(dtype="float64")],
                                                  ignore_index=True)

            bldg_groups.append(bldg_points_within_region)

        # Assign electric power service availability to each building
        bldg_infra_availability = bldg_infra_availability.assign(is_power_available=True)
        for idx in range(len(poly_shapes)):
            substation_guid = epf_damage.loc[idx, "guid"]
            for building_id in bldg_groups[idx]["guid"]:
                bldg_infra_availability.loc[bldg_infra_availability["guid"] == str(building_id), 'substation_guid']\
                    = substation_guid
                bldg_infra_availability.loc[
                    bldg_infra_availability["guid"] == str(building_id), 'is_power_available'] = \
                    not substation_flooded[idx]

        return bldg_infra_availability

    @staticmethod
    def service_areas_to_substations(city_polygon, substations):
        city_polygon.set_crs(epsg=4326)
        city_polygon_shape = unary_union(city_polygon.geometry)
        # TDOO no idea why decimal matters; without it it won't work
        substation_coordinates = points_to_coords(substations.geometry).round(decimals=3)

        # Use Voronoi polygon to assign service areas to corresponding substations
        poly_shapes, pts = voronoi_regions_from_coords(substation_coordinates, city_polygon_shape)
        return poly_shapes, pts

    @staticmethod
    def is_substation_flooded(epf_damage):
        substation_flooded = [False for i in range(epf_damage.shape[0])]
        epf_damage = epf_damage.astype({"DS_3": float})
        for i, row in epf_damage.iterrows():
            substation_flooded[i] = (row["DS_3"] > 0)

        return substation_flooded

    def get_spec(self):
        """Get specifications of the building damage analysis.

        Returns:
            obj: A JSON object of specifications of the building damage analysis.

        """
        return {
            'name': 'electric-power-availability',
            'description': 'electric power availability analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'result dataset name',
                    'type': str
                }
            ],
            'input_datasets': [
                {
                    'id': 'buildings',
                    'required': True,
                    'description': 'Building Inventory',
                    'type': ['ergo:buildingInventoryVer4', 'ergo:buildingInventoryVer5',
                             'ergo:buildingInventoryVer6', 'ergo:buildingInventoryVer7'],
                },
                {
                    'id': 'city_polygon',
                    'required': True,
                    'description': 'city boundary',
                    'type': ['incore:cityPolygonShape'],
                },
                {
                    'id': 'epfs',
                    'required': True,
                    'description': 'Electric Power Facility Inventory',
                    'type': ['incore:epf',
                             'ergo:epf',
                             'incore:epfVer2'
                             ],
                },
                {
                    'id': 'epf_damage',
                    'required': True,
                    'description': 'Electric Power Damage',
                    'type': ['incore:epfDamageVer3']
                },
            ],
            'output_datasets': [
                {
                    'id': 'power_availability',
                    'parent_type': 'buildings',
                    'description': 'CSV file of power availability of each building',
                    'type': 'incore:buildingPowerAvailability'
                }
            ]
        }
