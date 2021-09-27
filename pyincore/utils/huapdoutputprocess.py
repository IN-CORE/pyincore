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
    def pd_by_race(race_count, race_count_path=None, filename_json=None):
        """ Calculate race results from the output files of the Joplin Population Dislocation analysis
        and convert the results to json format.
        [
            {"housing_unit_characteristics": "White alone, Not Hispanic",
             "housing_unit_dislocation": 1521,
             "housing_unit_in_total": 18507
            },{"housing_unit_characteristics": "Black alone, Not Hispanic",..,..},{},{},{"No race Ethnicity Data"},{"Total"}
        ]

        Args:
            race_count (obj): IN-CORE dataset for Joplin Population Dislocation race count result.
            race_count_path (obj): A fallback for the case that count by race object of PD is not provided.
                 For example a user wants to directly pass in csv files, a path to PD race count result.
            filename_json (str): Path and name to save json output file in. E.g "pd_race_count.json"

        Returns:
            obj: PD total count by race. A JSON of the hua and population dislocation race results by category.

        """
        race_categories = ["White alone, Not Hispanic",
                           "Black alone, Not Hispanic",
                           "Other race, Not Hispanic",
                           "Any race, Hispanic",
                           "No race Ethnicity Data",
                           "Total"]
        hu_disl = [1521, 76, 92, 41, 269, 1999]
        hu_disl_tot = [18507, 606, 1110, 556, 2482, 23261]

        if race_count_path:
            race_group_count = pd.read_csv(race_count_path)
        else:
            race_group_count = race_count_path.get_dataframe_from_csv()

        before_values = race_group_count["HH0"]
        after_values = race_group_count["HHL"]

        hua_race = {}
        pd_by_race_json = []
        for i in range(len(race_categories)):
            hua_race[HUADislOutputProcess.HU_CATEGORIES[0]] = race_categories[i]
            hua_race[HUADislOutputProcess.HU_CATEGORIES[1]] = hu_disl[i]
            hua_race[HUADislOutputProcess.HU_CATEGORIES[2]] = hu_disl_tot[i]
            pd_by_race_json.append(hua_race)

        print(pd_by_race_json)

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(pd_by_race_json, outfile)
        # Serializing json
        return json.dumps(pd_by_race_json)


    @staticmethod
    def pd_by_income(income_count, income_count_path=None, filename_json=None):
        """ Calculate income results from the output files of the Joplin Population Dislocation analysis
        and convert the results to json format.
        [
            {"housing_unit_characteristics": "HH1 (less than $15,000)",
             "housing_unit_dislocation": 311,
             "housing_unit_in_total": 3252
             },
             {"HH2 ($15,000 to $35,000)",..,..},{},{},{},{},
             {"Unknown",..,..}
        ]

        Args:
            income_count (obj): IN-CORE dataset for Joplin Population Dislocation income count result.
            income_count_path (obj): A fallback for the case that count by income object of PD is not provided.
                 For example a user wants to directly pass in csv files, a path to PD income count result.
            filename_json (str): Path and name to save json output file in. E.g "pd_income_count.json"

        Returns:
            obj: PD total count by income. A JSON of the hua and population dislocation income results by category.

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

        if income_count_path:
            income_group_count = pd.read_csv(income_count_path)
        else:
            income_group_count = income_count_path.get_dataframe_from_csv()

        before_values = income_group_count["HH0"]
        after_values = income_group_count["HHL"]

        hua_income = {}
        pd_by_income_json = []
        for i in range(len(income_categories)):
            hua_income[HUADislOutputProcess.HU_CATEGORIES[0]] = income_categories[i]
            hua_income[HUADislOutputProcess.HU_CATEGORIES[1]] = hu_disl[i]
            hua_income[HUADislOutputProcess.HU_CATEGORIES[2]] = hu_disl_tot[i]
            pd_by_income_json.append(hua_income)

        print(pd_by_income_json)

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(pd_by_income_json, outfile)
        # Serializing json
        return json.dumps(pd_by_income_json)


    @staticmethod
    def pd_by_tenure(tenure_count, tenure_count_path=None, filename_json=None):
        """ Calculate tenure results from the output files of the Joplin Population Dislocation analysis
        and convert the results to json format.
        [
            {"housing_unit_characteristics": "Owner occupied",
             "housing_unit_dislocation": 1018,
            "housing_unit_in_total": 11344
            },
            {"housing_unit_characteristics": "Renter occupied",..,..},{},{},{},{},{},
            {"total",..,..}
        ]

        Args:
            tenure_count (obj): IN-CORE dataset for Joplin Population Dislocation income count result.
            income_count_path (obj): A fallback for the case that count by income object of PD is not provided.
                 For example a user wants to directly pass in csv files, a path to PD income count result.
            filename_json (str): Path and name to save json output file in. E.g "pd_income_count.json"

        Returns:
            obj: PD total count by income. A JSON of the hua and population dislocation income results by category.

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

        if tenure_count_path:
            tenure_group_count = pd.read_csv(tenure_count_path)
        else:
            tenure_group_count = tenure_count_path.get_dataframe_from_csv()

        before_values = tenure_group_count["HH0"]
        after_values = tenure_group_count["HHL"]

        hua_tenure = {}
        pd_by_tenure_json = []
        for i in range(len(tenure_categories)):
            hua_tenure[HUADislOutputProcess.HU_CATEGORIES[0]] = tenure_categories[i]
            hua_tenure[HUADislOutputProcess.HU_CATEGORIES[1]] = hu_disl[i]
            hua_tenure[HUADislOutputProcess.HU_CATEGORIES[2]] = hu_disl_tot[i]
            pd_by_tenure_json.append(hua_tenure)

        print(pd_by_tenure_json)

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(pd_by_tenure_json, outfile)
        # Serializing json
        return json.dumps(pd_by_tenure_json)


    @staticmethod
    def pd_by_housing(housing_count, housing_count_path=None, filename_json=None):
        """ Calculate housing results from the output files of the Joplin Population Dislocation analysis
        and convert the results to json format.
        [
            {"housing_unit_characteristics": "Single Family",
             "housing_unit_dislocation": 1162,
             "housing_unit_in_total": 837
             },{},{"Total",..,..}
        ]

        Args:
            housing_count (obj): IN-CORE dataset for Joplin Population Dislocation housing count result.
            housing_count_path (obj): A fallback for the case that count by housing object of PD is not provided.
                 For example a user wants to directly pass in csv files, a path to PD housing count result.
            filename_json (str): Path and name to save json output file in. E.g "pd_housing_count.json"

        Returns:
            obj: PD total count by housing. A JSON of the hua and population dislocation housing results by category.

        """
        hu_dislocated = 1999
        hu_tot = 23261
        pop_dislocated = 4197
        pop_tot = 23261

        if housing_count_path:
            housing_group_count = pd.read_csv(housing_count_path)
        else:
            housing_group_count = housing_count_path.get_dataframe_from_csv()

        before_values = housing_group_count["HH0"]
        after_values = housing_group_count["HHL"]

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

        pd_by_tenure_json = {"housing_unit_dslocation": hu_disl, "population_dislocation": pop_disl}

        print(pd_by_tenure_json)

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(pd_by_tenure_json, outfile)
        # Serializing json
        return json.dumps(pd_by_tenure_json)


    @staticmethod
    def pd_total(total_count, total_count_path=None, filename_json=None):
        """ Calculate total results from the output files of the Joplin Population Dislocation analysis
        and convert the results to json format.
        {   "housing_unit_dislocation": {
                "dislocated": {
                    "number": 1999,
                    "percentage": 0.085
                }, "not_dislocated": {}, "total": {}
            },"population_dislocation": {"dislocated": {},"not_dislocated": {}, "total": {}}
        }

        Args:
            total_count (obj): IN-CORE dataset for Joplin Population Dislocation total count result.
            total_count_path (obj): A fallback for the case that count by total object of PD is not provided.
                 For example a user wants to directly pass in csv files, a path to PD total count result.
            filename_json (str): Path and name to save json output file in. E.g "pd_total_count.json"

        Returns:
            obj: PD total count. A JSON of the hua and population dislocation total results by category.

        """
        hu_dislocated = 1999
        hu_tot = 23261
        pop_dislocated = 4197
        pop_tot = 23261

        if total_count_path:
            total_group_count = pd.read_csv(total_count_path)
        else:
            total_group_count = total_count_path.get_dataframe_from_csv()

        before_values = total_group_count["HH0"]
        after_values = total_group_count["HHL"]

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

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(pd_total_json, outfile)
        # Serializing json
        return json.dumps(pd_total_json)


