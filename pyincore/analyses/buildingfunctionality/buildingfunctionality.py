# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import numpy as np
import pandas as pd

from pyincore import BaseAnalysis


class BuildingFunctionality(BaseAnalysis):
    """The building functionality analysis can be used to calculate building functionality probabilities considering
    two situations: buildings are in at least a damage state 2 or greater or buildings are not damaged but electric
    power is not available to the building. Whether buildings can receive electrical power is assumed to depend on
    the interdependency between buildings and substations, and between buildings and poles in close proximity.
    If both the nearest pole to the building and the substation where buildings belong to its service area are
    functional, buildings are considered to be able to receive electric power.
    """
    def __init__(self, incore_client):
        super().__init__(incore_client)

    def get_spec(self):

        return {
            'name': 'functionality_probability',
            'description': 'calculate the functionality probability of each building',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': False,
                    'description': 'result dataset name',
                    'type': str
                },
                {
                    'id': 'num_cpu',
                    'required': False,
                    'description': 'If using parallel execution, the number of cpus to request',
                    'type': int
                },
                {
                    'id': 'num_samples',
                    'required': True,
                    'description': 'Number of Monte Carlo samples',
                    'type': int
                }
            ],
            'input_datasets': [
                {
                    'id': 'building_damage_mcs_samples',
                    'required': True,
                    'description': 'building damage samples',
                    'type': ['incore:sampleFailureState'],
                },
                {
                    'id': 'substations_damage_mcs_samples',
                    'required': True,
                    'description': 'substations damage samples',
                    'type': ['incore:sampleFailureState'],
                },
                {
                    'id': 'poles_damage_mcs_samples',
                    'required': True,
                    'description': 'poles damage samples',
                    'type': ['incore:sampleFailureState'],
                },
                {
                    'id': 'interdependency_dictionary',
                    'required': True,
                    'description': 'JSON file of interdependency between buildings and substations and poles',
                    'type': ['incore:buildingInterdependencyDict'],
                },
            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'description': 'CSV file of functionality probability',
                    'type': 'incore:epfVer1'
                }
            ]
        }

    def run(self):
        """Executes building functionality analysis"""
        interdependency_dict = self.get_input_dataset("interdependency_dictionary").get_json_reader()
        buildings_df = self.get_input_dataset("building_damage_mcs_samples").get_dataframe_from_csv()
        substations_df = self.get_input_dataset("substations_damage_mcs_samples").get_dataframe_from_csv()
        poles_df = self.get_input_dataset("poles_damage_mcs_samples").get_dataframe_from_csv()

        functionality_probabilities = [self.functionality(building, buildings_df, substations_df, poles_df,
                                                          interdependency_dict) for building in buildings_df['guid']]

        results = pd.DataFrame(functionality_probabilities, columns=['building_guid', 'probability'])

        self.set_result_csv_data("result", results, name=self.get_parameter("result_name"),
                                 source='dataframe')

        return True

    def functionality(self, building, buildings, substations, poles, interdependency):
        """

        Args:
            building: building guid
            buildings: buildings DataFrame
            substations: substations DataFrame
            poles: poles DataFrame
            interdependency: interdependency between buildings and substations and poles dictionary

        Returns: probability [0,1] of building being functional

        """
        # if building is defined in the interdependency lookup table
        if building in interdependency.keys():
            building_mc_samples = buildings.loc[buildings["guid"] == building]
            substations_mc_samples = \
                substations.loc[substations["guid"] == interdependency[building]["substations_guid"]]
            poles_mc_samples = poles.loc[poles["guid"] == interdependency[building]["poles_guid"]]
            try:
                buildings_list = list(building_mc_samples.iloc[0])[1].split(",")
            except IndexError:
                print("error with buildings")
                print(building_mc_samples)
                return {building: -1}
            try:
                substations_list = list(substations_mc_samples.iloc[0])[1].split(",")
            except IndexError:
                print("error with substations")
                print(interdependency[building]["substations_guid"])
                return {building: -1}
            try:
                poles_list = list(poles_mc_samples.iloc[0])[1].split(",")
            except IndexError:
                print("error with poles")
                print(interdependency[building]["poles_guid"])
                return {building: -1}

            functionality_samples = [self.functionality_probability(building_sample, substation_sample, pole_sample)
                                     for building_sample, substation_sample, pole_sample in
                                     zip(buildings_list, substations_list, poles_list)]
            functionality_sum = np.sum(functionality_samples)
            probability = 0.0
            if functionality_sum > 0:
                probability = (functionality_sum/self.get_parameter("num_samples"))
            return building, probability

        else:
            return building, "NA"

    def functionality_probability(self, building_sample, substation_sample, pole_sample):
        """ This function is subject to change. For now, buildings have a 1-to-1 relationship with
        substations and poles, so it suffices to check that the poles and substations are up.
        Args:
            building_sample: monte carlo samples of building functionality
            substation_sample: monte carlo samples of substation functionality
            pole_sample: monte carlo samples of pole functionality

        Returns: 1 if building is functional, 0 otherwise

        """
        if building_sample == "1" and substation_sample == "1" and pole_sample == "1":
            return 1
        else:
            return 0
