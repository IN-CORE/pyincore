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
                    'id': 'functionality_samples',
                    'description': 'CSV file of functionality samples',
                    'type': 'incore:funcSample'
                },
                {
                    'id': 'functionality_probability',
                    'description': 'CSV file of functionality probability',
                    'type': 'incore:funcProbability'
                }
            ]
        }

    def run(self):
        """Executes building functionality analysis"""
        interdependency_dict = self.get_input_dataset("interdependency_dictionary").get_json_reader()

        # enable index on "guid" column
        buildings_df = self.get_input_dataset("building_damage_mcs_samples").get_dataframe_from_csv().set_index("guid")
        substations_df = self.get_input_dataset("substations_damage_mcs_samples").get_dataframe_from_csv().set_index("guid")
        poles_df = self.get_input_dataset("poles_damage_mcs_samples").get_dataframe_from_csv().set_index("guid")

        functionality_probabilities = []
        functionality_samples = []
        for building_guid in buildings_df.index:
            building_guid, sample, probability = self.functionality(building_guid, buildings_df, substations_df, poles_df,
                                                               interdependency_dict)
            functionality_probabilities.append([building_guid, probability])
            functionality_samples.append([building_guid, sample])

        fp_results = pd.DataFrame(functionality_probabilities, columns=['building_guid', 'probability'])
        fs_results = pd.DataFrame(functionality_samples, columns=['building_guid', 'samples'])

        self.set_result_csv_data("functionality_probability",
                                 fp_results,
                                 name=self.get_parameter("result_name") + "_functionality_probability",
                                 source='dataframe')

        self.set_result_csv_data("functionality_samples",
                                 fs_results,
                                 name=self.get_parameter("result_name") + "_functionality_samples",
                                 source='dataframe')

        return True

    def functionality(self, building_guid, buildings, substations, poles, interdependency):
        """

        Args:
            building_guid: building guid
            buildings: buildings DataFrame
            substations: substations DataFrame
            poles: poles DataFrame
            interdependency: interdependency between buildings and substations and poles dictionary

        Returns: building, functionality sampe that is a string of "0,0,1...", probability [0,1] of building being
        functional

        """
        # if building is defined in the interdependency lookup table
        if building_guid in interdependency.keys():
            building_mc_samples = buildings.loc[building_guid]
            substations_mc_samples = substations.loc[interdependency[building_guid]["substations_guid"]]
            poles_mc_samples = poles.loc[interdependency[building_guid]["poles_guid"]]


            building_list = []
            try:
                #building_list = list(building_mc_samples.iloc[0])[1].split(",")
                building_list = building_mc_samples["failure"].split(",")
            except IndexError:
                print("error with buildings")
                print(building_mc_samples)
                return {building_guid: -1}
            
            substation_list = []
            try:
                substation_list = substations_mc_samples["failure"].split(",")
            except IndexError:
                print("error with substations")
                print(interdependency[building_guid]["substations_guid"])
                return {building_guid: -1}
            
            pole_list = []
            try:
                pole_list = poles_mc_samples["failure"].split(",")
            except IndexError:
                print("error with poles")
                print(interdependency[building_guid]["poles_guid"])
                return {building_guid: -1}

            functionality_samples = [self.functionality_probability(building_sample, substation_sample, pole_sample)
                                     for building_sample, substation_sample, pole_sample in
                                     zip(building_list, substation_list, pole_list)]
            functionality_sum = np.sum(functionality_samples)
            num_samples = len(functionality_samples)
            probability = 0.0
            if functionality_sum > 0:
                probability = (functionality_sum/num_samples)
            return building_guid, ",".join([str(sample) for sample in functionality_samples]), probability

        else:
            return building_guid, "NA", "NA"

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
