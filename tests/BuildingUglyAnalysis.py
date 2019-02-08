"""

Copyright (c) 2019 University of Illinois and others.  All rights reserved.
This program and the accompanying materials are made available under the
terms of the Mozilla Public License v2.0 which accompanies this distribution,
and is available at https://www.mozilla.org/en-US/MPL/2.0/

"""

import random

import collections

from pyincore import InsecureIncoreClient, AnalysisUtil
from pyincore.baseanalysis import BaseAnalysis
import pprint

class BuildingUglyAnalysis(BaseAnalysis):
    def run(self):

        #omitting concurrency here, we could just to the same determine_parallelism_locally
        #as is done in other existing anlayses

        building_set = self.get_input_dataset("buildings").get_inventory_reader()
        results = []

        for building in building_set:
            results.append(self.building_ugly_analysis(building))

        self.set_result_csv_data("result", results, name=self.get_parameter("result_name"))

        return True

    def building_ugly_analysis(self, building):
        ugly_results = collections.OrderedDict()
        ugly_results['guid'] = building['properties']['guid']
        ugly_results["ugly_rating"] = str(random.randint(1,101))
        ugly_results["backward_guid"] = str(building['properties']['guid'])[::-1]

        return ugly_results


    def get_spec(self):
        return {
            'name': 'building-ugly',
            'description': 'determines if buildings are ugly',
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
                    'type': ['ergo:buildingInventoryVer5', 'ergo:buildingInventoryVer4'],
                }
            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'buidings',
                    'type': 'building-ugly'
                }
            ]
        }


if __name__ == "__main__":

    client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", "ywkim")
    analysis = BuildingUglyAnalysis(client)

    analysis.load_remote_input_dataset("buildings", "5a284f1fc7d30d13bc081a7e")
    #or you could do analysis.load_local_input_dataset("buildings", "/tmp/file.shp")

    #if you tried to load a dataset of the wrong type, like bridges:
    #analysis.load_remote_input_dataset("buildings", "xyzPretendBridgeId")
    # then the validation step would barf and complain that the dataset has the
    # wrong data type

    analysis.set_parameter("result_name", "is_ugly_result")
    analysis.run_analysis()

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(analysis.get_output_dataset("result"))