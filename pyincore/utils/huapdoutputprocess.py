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
    def pd_by_race(hua_result):
        """ Calculate race results from the output files of the Joplin Population Dislocation analysis
        and convert the results to json format.

        Args:
            pd_result (obj): A result of House unit allocation and Popilation dislocation analyses.

        Returns:
            obj: PD by race json. A JSON of the hua and population dislocation race results by category.

        """
        race_categories = ["White alone, Not Hispanic",
                           "Black alone, Not Hispanic",
                           "Other race, Not Hispanic",
                           "Any race, Hispanic",
                           "No race Ethnicity Data",
                           "Total"]
        hu_disl = [1521, 76, 92, 41, 269, 1999]
        hu_disl_tot = [18507, 606, 1110, 556, 2482, 23261]

        hua_race = {}
        pd_by_race_json = []
        for i in range(len(race_categories)):
            hua_race[HUADislOutputProcess.HU_CATEGORIES[0]] = race_categories[i]
            hua_race[HUADislOutputProcess.HU_CATEGORIES[1]] = hu_disl[i]
            hua_race[HUADislOutputProcess.HU_CATEGORIES[2]] = hu_disl_tot[i]
            pd_by_race_json.append(hua_race)

        print(pd_by_race_json)
        # [
        #     {
        #         "housing_unit_characterstics": "White alone, Not Hispanic",
        #         "housing_unit_dislocation": 1521,
        #         "housing_unit_in_total": 18507
        #     },
        #     {
        #         "housing_unit_characterstics": "Black alone, Not Hispanic",
        #         "housing_unit_dislocation": 76,
        #         "housing_unit_in_total": 606
        #     },
        #     {
        #         "housing_unit_characterstics": "Other race, Not Hispanic",
        #         "housing_unit_dislocation": 92,
        #         "housing_unit_in_total": 1110
        #     },
        #     {
        #         "housing_unit_characterstics": "Any race, Hispanic",
        #         "housing_unit_dislocation": 41,
        #         "housing_unit_in_total": 556
        #     },
        #     {
        #         "housing_unit_characterstics": "No race Ethnicity Data",
        #         "housing_unit_dislocation": 269,
        #         "housing_unit_in_total": 2482
        #     },
        #     {
        #         "housing_unit_characterstics": "Total",
        #         "housing_unit_dislocation": 1999,
        #         "housing_unit_in_total": 23261
        #     },
        # ]
        return pd_by_race_json

        hua_res = hua_result.get_dataframe_from_csv()

        hua_by_race_json = hua_res.to_json
        hua_by_income_json = hua_res.to_json
        hua_by_tenure_json = hua_res.to_json
        hua_total_json = hua_res.to_json

        return hua_by_race_json, hua_by_income_json, hua_by_tenure_json, hua_total_json

    @staticmethod
    def pd_by_income(hua_result):
        """Calculate income results from the output files of the Joplin Population Dislocation analysis
        and convert the results to json format.

        Args:
            hua_result (obj): A result of House unit allocation and Population dislocation analyses.

        Returns:
            obj: PD by income json. A JSON of the hua and population dislocation income results by category.

        """
        income_categories = ["HH1 (less than $15,000)",
                             "HH2 ($15,000 to $35,000)",
                             "HH3 ($35,000 to $70,000)",
                             "HH4 ($70,000 to $120,000)",
                             "HH5 (More than $120,000)",
                             "Unknown",
                             "Total"]
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
        return pd_by_income_json

    @staticmethod
    def pd_by_tenure(hua_result):
        """ Calculate tenure results from the output files of the Joplin Population Dislocation analysis
        and convert the results to json format.

        Args:
            pd_result (obj): A result of House unit allocation and Popilation dislocation analyses.

        Returns:
            obj: PD by tenure json. A JSON of the hua and population dislocation tenure results by category.

        """
        tenure_categories = ["Owner occupied",
                             "Renter occupied",
                             "Nursing facilities",
                             "Other group quarters",
                             "Vacant for rent",
                             "Vacant for sale",
                             "Vacant other"
                             "Total"]
        hu_disl = [1018, 712, 0, 3, 75, 60, 131, 1999]
        hu_disl_tot = [11344, 9435, 9, 18, 984, 573, 898, 23261]
        hua_tenure = {}
        pd_by_tenure_json = []
        for i in range(len(tenure_categories)):
            hua_tenure[HUADislOutputProcess.HU_CATEGORIES[0]] = tenure_categories[i]
            hua_tenure[HUADislOutputProcess.HU_CATEGORIES[1]] = hu_disl[i]
            hua_tenure[HUADislOutputProcess.HU_CATEGORIES[2]] = hu_disl_tot[i]
            pd_by_tenure_json.append(hua_tenure)

        print(pd_by_tenure_json)
        # [
        #     {
        #         "housing_unit_characteristics": "Owner occupied",
        #         "housing_unit_dislocation": 1018,
        #         "housing_unit_in_total": 11344
        #     },
        #     {
        #         "housing_unit_characteristics": "Renter occupied",
        #         "housing_unit_dislocation": 712,
        #         "housing_unit_in_total": 9435
        #     },
        #     {
        #         "housing_unit_characteristics": "Nursing facilities",
        #         "housing_unit_dislocation": 0,
        #         "housing_unit_in_total": 9
        #     },
        #     {
        #         "housing_unit_characteristics": "Other group quarters",
        #         "housing_unit_dislocation": 3,
        #         "housing_unit_in_total": 18
        #     },
        #     {
        #         "housing_unit_characteristics": "Vacant for rent",
        #         "housing_unit_dislocation": 75,
        #         "housing_unit_in_total": 984
        #     },
        #     {
        #         "housing_unit_characteristics": "Vacant for sale",
        #         "housing_unit_dislocation": 60,
        #         "housing_unit_in_total": 573
        #     },
        #     {
        #         "housing_unit_characteristics": "Vacant Other",
        #         "housing_unit_dislocation": 131,
        #         "housing_unit_in_total": 898
        #     },
        #     {
        #         "housing_unit_characteristics": "total",
        #         "housing_unit_dislocation": 1999,
        #         "housing_unit_in_total": 23261
        #     }
        # ]
        return pd_by_tenure_json

    @staticmethod
    def pd_by_housing(hua_result):
        """ Calculate total results from the output files of the Joplin Population Dislocation analysis
        and convert the results to json format.

        Args:
            pd_result (obj): A result of House unit allocation analysis.

        Returns:
            obj: PD housing. A JSON of the hua and population dislocation total results by category.

        """
        hu_dislocated = 1999
        hu_tot = 23261
        pop_dislocated = 4197
        pop_tot = 23261

        hu_disl = {}
        hu_disl["dislocated"] = {"number": hu_dislocated, "percentage": hu_dislocated/hu_tot}
        hu_disl["not_dislocated"] = {"number": hu_tot - hu_dislocated,
                                     "percentage": (hu_tot - hu_dislocated)/hu_tot}
        hu_disl["total"] = {"number": hu_tot, "percentage": 1}

        pop_disl = {}
        pop_disl["dislocated"] = {"number": pop_dislocated, "percentage": pop_dislocated/pop_tot}
        pop_disl["not_dislocated"] = {"number": pop_tot - pop_dislocated,
                                     "percentage": (pop_tot - pop_dislocated)/pop_tot}
        pop_disl["total"] = {"number": pop_tot, "percentage": 1}

        pd_total_json = {"housing_unit_dslocation": hu_disl, "population_dislocation": pop_disl}

        print(pd_total_json)
        # [
        #     {
        #         "housing_unit_characterstics": "Single Family",
        #         "housing_unit_dislocation": 1162,
        #         "housing_unit_in_total": 837
        #     },
        #     {
        #         "housing_unit_characterstics": "Multi Family",
        #         "housing_unit_dislocation": 14317,
        #         "housing_unit_in_total": 8944
        #     },
        #     {
        #         "housing_unit_characterstics": "Total",
        #         "housing_unit_dislocation": 1999,
        #         "housing_unit_in_total": 23261
        #     }
        # ]
        return pd_total_json

    @staticmethod
    def pd_total(hua_result):
        """ Calculate total results from the output files of the Joplin Population Dislocation analysis
        and convert the results to json format.

        Args:
            pd_result (obj): A result of House unit allocation analysis.

        Returns:
            obj: PD total. A JSON of the hua and population dislocation total results by category.

        """
        hu_dislocated = 1999
        hu_tot = 23261
        pop_dislocated = 4197
        pop_tot = 23261

        hu_disl = {}
        hu_disl["dislocated"] = {"number": hu_dislocated, "percentage": hu_dislocated/hu_tot}
        hu_disl["not_dislocated"] = {"number": hu_tot - hu_dislocated,
                                     "percentage": (hu_tot - hu_dislocated)/hu_tot}
        hu_disl["total"] = {"number": hu_tot, "percentage": 1}

        pop_disl = {}
        pop_disl["dislocated"] = {"number": pop_dislocated, "percentage": pop_dislocated/pop_tot}
        pop_disl["not_dislocated"] = {"number": pop_tot - pop_dislocated,
                                     "percentage": (pop_tot - pop_dislocated)/pop_tot}
        pop_disl["total"] = {"number": pop_tot, "percentage": 1}

        pd_total_json = {"housing_unit_dslocation": hu_disl, "population_dislocation": pop_disl}

        print(pd_total_json)
        # {
        #     "housing_unit_dslocation": {
        #         "dislocated": {
        #             "number": 1999,
        #             "percentage": 0.085
        #         },
        #         "not_dislocated": {
        #             "number": 21262,
        #             "percentage": 0.914
        #         },
        #         "total": {
        #             "number": 23261,
        #             "percentage": 1
        #         }
        #     },
        #     "population_dislocation": {
        #         "dislocated": {
        #             "number": 4197,
        #             "percentage": 0.085
        #         },
        #         "not_dislocated": {
        #             "number": 45613,
        #             "percentage": 0.914
        #         },
        #         "total": {
        #             "number": 23261,
        #             "percentage": 1
        #         }
        #     }
        # }
        return pd_total_json


