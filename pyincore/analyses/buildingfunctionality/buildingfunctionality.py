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

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        super().__init__(incore_client)

    def get_spec(self):
        """Get specifications of the building functionality analysis.

        Returns:
            obj: A JSON object of specifications of the building functionality analysis.

        """
        return {
            "name": "functionality_probability",
            "description": "calculate the functionality probability of each building",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": False,
                    "description": "result dataset name",
                    "type": str,
                }
            ],
            "input_datasets": [
                {
                    "id": "building_damage_mcs_samples",
                    "required": True,
                    "description": "building damage samples",
                    "type": ["incore:sampleFailureState"],
                },
                {
                    "id": "substations_damage_mcs_samples",
                    "required": False,
                    "description": "substations damage samples",
                    "type": ["incore:sampleFailureState"],
                },
                {
                    "id": "poles_damage_mcs_samples",
                    "required": False,
                    "description": "poles damage samples",
                    "type": ["incore:sampleFailureState"],
                },
                {
                    "id": "interdependency_dictionary",
                    "required": False,
                    "description": "JSON file of interdependency between buildings and substations and poles",
                    "type": ["incore:buildingInterdependencyDict"],
                },
            ],
            "output_datasets": [
                {
                    "id": "functionality_samples",
                    "description": "CSV file of functionality samples",
                    "type": "incore:funcSample",
                },
                {
                    "id": "functionality_probability",
                    "description": "CSV file of functionality probability",
                    "type": "incore:funcProbability",
                },
            ],
        }

    def run(self):
        """Executes building functionality analysis"""

        # enable index on "guid" column
        buildings_df = (
            self.get_input_dataset("building_damage_mcs_samples")
            .get_dataframe_from_csv()
            .set_index("guid")
        )

        interdependency_dataset = self.get_input_dataset("interdependency_dictionary")
        if interdependency_dataset is not None:
            interdependency_dict = interdependency_dataset.get_json_reader()
        else:
            interdependency_dict = None

        substations_dataset = self.get_input_dataset("substations_damage_mcs_samples")
        if substations_dataset is not None:
            substations_df = substations_dataset.get_dataframe_from_csv().set_index(
                "guid"
            )
        else:
            substations_df = None

        poles_dataset = self.get_input_dataset("poles_damage_mcs_samples")
        if poles_dataset is not None:
            poles_df = poles_dataset.get_dataframe_from_csv().set_index("guid")
        else:
            poles_df = None

        if (
            poles_dataset is not None or substations_dataset is not None
        ) and interdependency_dataset is None:
            raise ValueError(
                "Please provide interdependency table if pole or substation damage is "
                "considered in the building functionality calculation."
            )

        functionality_probabilities = []
        functionality_samples = []
        for building_guid in buildings_df.index:
            building_guid, sample, probability = self.functionality(
                building_guid,
                buildings_df,
                substations_df,
                poles_df,
                interdependency_dict,
            )
            functionality_probabilities.append([building_guid, probability])
            functionality_samples.append([building_guid, sample])

        fp_results = pd.DataFrame(
            functionality_probabilities, columns=["guid", "probability"]
        )
        fs_results = pd.DataFrame(functionality_samples, columns=["guid", "failure"])

        self.set_result_csv_data(
            "functionality_probability",
            fp_results,
            name=self.get_parameter("result_name") + "_functionality_probability",
            source="dataframe",
        )

        self.set_result_csv_data(
            "functionality_samples",
            fs_results,
            name=self.get_parameter("result_name") + "_functionality_samples",
            source="dataframe",
        )

        return True

    def functionality(
        self, building_guid, buildings, substations, poles, interdependency
    ):
        """

        Args:
            building_guid (str): A building defined by its guid.
            buildings (pd.DataFrame): A list of buildings.
            substations (pd.DataFrame): A list of substations.
            poles (pd.DataFrame): A list of poles.
            interdependency (dict): An interdependency between buildings and substations and poles.

        Returns:
            str: A building guid.
            str: A functionality sample that is a string of "0,0,1...".
            str: A probability [0,1] of building being functional.

        """

        building_mc_samples = buildings.loc[building_guid]
        building_list = []
        try:
            building_list = building_mc_samples["failure"].split(",")
        except IndexError:
            print("error with buildings")
            print(building_mc_samples)
            return {building_guid: -1}

        # if building is defined in the interdependency lookup table
        if interdependency is not None:
            if building_guid in interdependency.keys():
                if substations is not None:
                    substations_mc_samples = substations.loc[
                        interdependency[building_guid]["substations_guid"]
                    ]
                    substation_list = []
                    try:
                        substation_list = substations_mc_samples["failure"].split(",")
                    except IndexError:
                        print("error with substations")
                        print(interdependency[building_guid]["substations_guid"])
                        return {building_guid: -1}
                else:
                    substation_list = None

                if poles is not None:
                    poles_mc_samples = poles.loc[
                        interdependency[building_guid]["poles_guid"]
                    ]
                    pole_list = []
                    try:
                        pole_list = poles_mc_samples["failure"].split(",")
                    except IndexError:
                        print("error with poles")
                        print(interdependency[building_guid]["poles_guid"])
                        return {building_guid: -1}
                else:
                    pole_list = None

                if substation_list is not None and pole_list is not None:
                    functionality_samples = [
                        BuildingFunctionality._calc_functionality_samples(
                            building_sample, substation_sample, pole_sample
                        )
                        for building_sample, substation_sample, pole_sample in zip(
                            building_list, substation_list, pole_list
                        )
                    ]
                elif substation_list is not None:
                    functionality_samples = [
                        BuildingFunctionality._calc_functionality_samples(
                            building_sample, substation_sample, None
                        )
                        for building_sample, substation_sample in zip(
                            building_list, substation_list
                        )
                    ]
                elif pole_list is not None:
                    functionality_samples = [
                        BuildingFunctionality._calc_functionality_samples(
                            building_sample, None, pole_sample
                        )
                        for building_sample, pole_sample in zip(
                            building_list, pole_list
                        )
                    ]
                else:
                    functionality_samples = [
                        BuildingFunctionality._calc_functionality_samples(
                            building_sample, None, None
                        )
                        for building_sample in building_list
                    ]
                probability = BuildingFunctionality._calc_functionality_probability(
                    functionality_samples
                )
                return (
                    building_guid,
                    ",".join([str(sample) for sample in functionality_samples]),
                    probability,
                )

            else:
                return building_guid, "NA", "NA"

        # else if only building MC failure is available
        else:
            functionality_samples = [
                BuildingFunctionality._calc_functionality_samples(building_sample)
                for building_sample in building_list
            ]
            probability = BuildingFunctionality._calc_functionality_probability(
                functionality_samples
            )
            return (
                building_guid,
                ",".join([str(sample) for sample in functionality_samples]),
                probability,
            )

    @staticmethod
    def _calc_functionality_samples(
        building_sample, substation_sample=None, pole_sample=None
    ):
        """This function is subject to change. For now, buildings have a 1-to-1 relationship with
        substations and poles, so it suffices to check that the poles and substations are up.

        Args:
            building_sample (str): Monte Carlo samples of building functionality.
            substation_sample (str|None): Monte Carlo samples of substation functionality.
            pole_sample (str|None): Monte Carlo samples of pole functionality.

        Returns:
            int: 1 if building is functional, 0 otherwise

        """
        if (
            building_sample == "1"
            and (substation_sample == "1" or substation_sample is None)
            and (pole_sample == "1" or pole_sample is None)
        ):
            return 1
        else:
            return 0

    @staticmethod
    def _calc_functionality_probability(functionality_samples):
        functionality_sum = np.sum(functionality_samples)
        num_samples = len(functionality_samples)
        probability = 0.0
        if functionality_sum > 0:
            probability = functionality_sum / num_samples

        return probability
