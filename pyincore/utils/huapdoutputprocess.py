# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import json
import pandas as pd


class HUADislOutputProcess:
    """This class converts csv results outputs of Joplin Housing unit allocation and population dislocation
     analysis to json format."""

    HU_CATEGORIES = ["housing_unit_characteristics",
                     "housing_unit_dislocations",
                     "housing_unit_in_total"]

    @staticmethod
    def get_pd_results(pd_result):
        """Load results directly from the output files of the Joplin Population Dislocation analysis,
        than convert the results to json formats.

        Args:
            pd_result (obj): A result of House unit allocation analysis.

        Returns:
            obj: PD by race json: A JSON of hua by race results ordered by cluster and category.
            obj: PD by income json. A JSON of the hua by income results ordered by cluster and category.
            obj: PD by tenure. A JSON of the hua by tenure ordered by cluster and category.
            obj: PD total. A JSON of the hua total results ordered by cluster and category.

        """
        pd_res = pd_result.get_dataframe_from_csv()

        pd_by_race_json = pd_res.to_json
        pd_by_income_json = pd_res.to_json
        pd_by_tenure_json = pd_res.to_json
        pd_total_json = pd_res.to_json

        income_categories = ["HH1 (less than $15,000)",
                             "HH2 ($15,000 to $35,000)",
                             "HH3 ($35,000 to $70,000)",
                             "HH4 ($70,000 to $120,000)",
                             "HH5 (More than $120,000)",
                             "Unknown",
                             "total"]
        hu_disl = [311, 280, 741, 741, 131, 422, 1999]
        hu_disl_tot = [3252, 3133, 9272, 9252, 1887, 4210, 23261]
        hua_income = {}
        pd_by_income_json = []
        for i in range(len(income_categories)):
            hua_income[HUADislOutputProcess.HU_CATEGORIES[0]] = income_categories[i]
            hua_income[HUADislOutputProcess.HU_CATEGORIES[1]] = hu_disl[i]
            hua_income[HUADislOutputProcess.HU_CATEGORIES[2]] = hu_disl_tot[i]
            pd_by_income_json.append(hua_income)

        print(pd_by_income_json)
        # [
        #     {
        #         "housing_unit_characteristics": "HH1 (less than $15,000)",
        #         "housing_unit_dislocation": 311,
        #         "housing_unit_in_total": 3252
        #     },
        #     {
        #         "housing_unit_characteristics": "HH2 ($15,000 to $35,000)",
        #         "housing_unit_dislocation": 280,
        #         "housing_unit_in_total": 3133
        #     },
        #     {
        #         "housing_unit_characteristics": "HH3 ($35,000 to $70,000)",
        #         "housing_unit_dislocation": 741,
        #         "housing_unit_in_total": 9272
        #     },
        #     {
        #         "housing_unit_characteristics": "HH4 ($70,000 to $120,000)",
        #         "housing_unit_dislocation": 741,
        #         "housing_unit_in_total": 9252
        #     },
        #     {
        #         "housing_unit_characteristics": "HH5 (More than $120,000)",
        #         "housing_unit_dislocation": 131,
        #         "housing_unit_in_total": 1887
        #     },
        #     {
        #         "housing_unit_characteristics": "Unknown",
        #         "housing_unit_dislocation": 422,
        #         "housing_unit_in_total": 4210
        #     },
        #     {
        #         "housing_unit_characteristics": "total",
        #         "housing_unit_dislocation": 1999,
        #         "housing_unit_in_total": 23261
        #     }
        # ]

        return pd_by_race_json, pd_by_income_json, pd_by_tenure_json, pd_total_json

    @staticmethod
    def get_hua_result(hua_result):
        """Calculate results from the output files of the Joplin HUA and PD analyses and convert the results
        to json format.

        Args:
            hua_result (obj): A result of House unit allocation analysis.

        Returns:
            obj: HUA by race json: A JSON of hua by race results ordered by cluster and category.
            obj: HUA by income json. A JSON of the hua by income results ordered by cluster and category.
            obj: HUA by tenure. A JSON of the hua by tenure ordered by cluster and category.
            obj: HUA total. A JSON of the hua total results ordered by cluster and category.

        """
        hua_res = hua_result.get_dataframe_from_csv()

        hua_by_race_json = hua_res.to_json
        hua_by_income_json = hua_res.to_json
        hua_by_tenure_json = hua_res.to_json
        hua_total_json = hua_res.to_json

        return hua_by_race_json, hua_by_income_json, hua_by_tenure_json, hua_total_json


