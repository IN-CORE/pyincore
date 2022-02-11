# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import numpy as np
import pandas as pd
from pyincore import BaseAnalysis


class HousingRecovery(BaseAnalysis):
    """ The analysis predicts building values and value changes over time following a disaster event.
    The model is calibrated with respect to demographics, parcel data, and building value trajectories
    following Hurricane Ike (2008) in Galveston, Texas. The model predicts building value at the parcel
    level for 8 years of observation. The models rely on Census (Decennial or American Community Survey, ACS)
    and parcel data immediately prior to the disaster event (year -1) as inputs for prediction.

    The Galveston, TX example makes use of 2010 Decennial Census and Galveston County Appraisal District (GCAD) tax assessor data and outputs from other analysis (i.e., Building Damage, Housing Unit Allocation, Population Dislocation) .

    The CSV outputs of the building values for the 6 years following the disaster event (with year 0 being the impact year).

    Contributors
        | Science: Wayne Day, Sarah Hamideh
        | Implementation: Michal Ondrejcek, Santiago Núñez-Corrales, and NCSA IN-CORE Dev Team

    Related publications
        Hamideh, S., Peacock, W. G., & Van Zandt, S. (2018). Housing recovery after disasters: Primary versus
        seasonal/vacation housing markets in coastal communities. Natural Hazards Review.

    Args:
        incore_client (IncoreClient): Service authentication.

    """
    def __init__(self, incore_client):
        super(HousingRecovery, self).__init__(incore_client)

    def get_spec(self):
        return {
            'name': 'housing-recovery',
            'description': 'Housing Recovery Analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'Result CSV dataset name',
                    'type': str
                }
            ],
            'input_datasets': [
                {
                    'id': 'building_damage',
                    'required': True,
                    'description': 'Structural building damage',
                    'type': ['buildingDamageVer6'],
                },
                {
                    'id': 'population_dislocation',
                    'required': True,
                    'description': 'Population Dislocation aggregated to the block group level',
                    'type': ['incore:popDislocation']
                },
                {
                    'id': 'census_appraisal_data',
                    'required': False,
                    'description': 'Census tax data, 2010 Decennial Census and Galveston County Appraisal '
                                   'District (GCAD) tax assessor data',
                    'type': ['incore:censusAppraisalData']
                }
            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'description': 'A csv file with the building values for the 6 years following the disaster '
                                   'event (with year 0 being the impact year)',
                    'type': 'incore:buildingValues'
                }
            ]
        }

    def run(self):
        """Merges Housing Unit Inventory, Address Point Inventory and Building Inventory.
         The results of this analysis are aggregated per structure/building. Generates
         one csv result per iteration.

        Returns:
            bool: True if successful, False otherwise

        """
        # Get desired result name
        result_name = self.get_parameter("result_name")

        # Datasets
        building_damage = self.get_input_dataset("building_damage").get_dataframe_from_csv(low_memory=False)
        pop_disl = self.get_input_dataset("population_dislocation").get_dataframe_from_csv(low_memory=False)
        census_appraisal = self.get_input_dataset("census_appraisal_data").get_dataframe_from_csv(low_memory=False)

        return True
