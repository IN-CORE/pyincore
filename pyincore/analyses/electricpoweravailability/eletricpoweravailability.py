# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import concurrent.futures
from itertools import repeat

from pyincore import BaseAnalysis, HazardService, \
    FragilityService, AnalysisUtil, GeoUtil
from pyincore.analyses.buildingdamage.buildingutil import BuildingUtil
from pyincore.models.dfr3curve import DFR3Curve


class ElectricPowerAvailability(BaseAnalysis):
    """Building Damage Analysis calculates the probability of building damage based on
    different hazard type such as earthquake, tsunami, and tornado.

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(ElectricPowerAvailability, self).__init__(incore_client)

    def run(self):
        """Executes building power availability analysis."""
        # inventory dataset
        bldg_set = self.get_input_dataset("buildings").get_inventory_reader()
        substation_set = self.get_input_dataset("epfs").get_inventory_reader()
        epf_damage = self.get_input_dataset("epf_damage").get_csv_reader()
        epf_damage_result = AnalysisUtil.get_csv_table_rows(epf_damage, ignore_first_row=False)

        power_availability = self.building_power_availability(bldg_set, substation_set, epf_damage_result)

        self.set_result_csv_data("power_availability", power_availability, name=self.get_parameter(
            "result_name")+"_power_availability")

        return True


    def building_power_availability(self, bldg_set, substation_set, epf_damage_result):
        """Run analysis for multiple buildings.

        Args:


        Returns:

        """


        return power_availability

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
