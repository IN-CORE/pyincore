# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import json
import pandas as pd


class HUADislOutputProcess:
    """This class converts csv results outputs of Joplin Housing unit allocation and population dislocation
     analysis to json format.

    Args:
        hua_count (obj): IN-CORE dataset for Joplin Housing Unit Allocation (HUS) results.
        pd_count (obj): IN-CORE dataset for Joplin Population Dislocation (PD) results.
        hua_count_path (obj): A fallback for the case that Joplin HUA object is not provided.
            For example a user wants to directly pass in csv files, a path to HUA result.
        pd_count_path (obj): A fallback for the case that Joplin PD object is not provided.
            For example a user wants to directly pass in csv files, a path to PD results.

    """
    HUPD_CATEGORIES = ["housing_unit_characteristics",
                       "housing_unit_dislocations",
                       "housing_unit_in_total",
                       "population_dislocations",
                       "population_in_total"
                       ]

    def __init__(self, hua_count, pd_count, hua_count_path=None, pd_count_path=None):
        if hua_count_path:
            self.hua_count = pd.read_csv(hua_count_path)
        else:
            self.hua_count = hua_count_path.get_dataframe_from_csv()
        if pd_count_path:
            self.pd_count = pd.read_csv(pd_count_path)
        else:
            self.pd_count = pd_count_path.get_dataframe_from_csv()
        self.numprec = 11.64

    def pd_by_race(self, filename_json=None):
        """ Calculate race results from the output files of the Joplin Population Dislocation analysis
        and convert the results to json format.
        [
            {"housing_unit_characteristics": "White alone, Not Hispanic",
             "housing_unit_dislocation": 1521,
             "housing_unit_in_total": 18507
            },{"housing_unit_characteristics": "Black alone, Not Hispanic",..,..},{},{},{"No race Ethnicity Data"},{"Total"}
        ]

        Args:
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
        pd_disl = [self.numprec * x for x in hu_disl]
        pd_disl_tot = [self.numprec * x for x in hu_disl_tot]

        # before_values = self.hua_count["HH0"]
        # after_values = self.hua_count["HHL"]
        # before_values = self.pd_count["HH0"]
        # after_values = self.pd_count["HHL"]

        huapd_race = {}
        pd_by_race_json = []
        for i in range(len(race_categories)):
            huapd_race[self.HUPD_CATEGORIES[0]] = race_categories[i]
            huapd_race[self.HUPD_CATEGORIES[1]] = hu_disl[i]
            huapd_race[self.HUPD_CATEGORIES[2]] = hu_disl_tot[i]
            huapd_race[self.HUPD_CATEGORIES[3]] = pd_disl[i]
            huapd_race[self.HUPD_CATEGORIES[4]] = pd_disl_tot[i]
            pd_by_race_json.append(huapd_race)

        print(pd_by_race_json)

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(pd_by_race_json, outfile)
        # Serializing json
        return json.dumps(pd_by_race_json)

    def pd_by_income(self, filename_json=None):
        """ Calculate income results from the output files of the Joplin Population Dislocation analysis
        and convert the results to json format.
        [
            {"housing_unit_characteristics": "HH1 (less than $15,000)",
             "housing_unit_dislocation": 311,
             "housing_unit_in_total": 3252,
             "population_dislocation": 311,
             "population_in_total": 3252
             },
             {"HH2 ($15,000 to $35,000)",..,..,..,..},{},{},{},{},
             {"Unknown",..,..,..,..}
        ]

        Args:
            filename_json (str): Path and name to save json output file in. E.g "pd_income_count.json"

        Returns:
            obj: PD total count by income. A JSON of the hua and population dislocation income results by category.

        """
        # [
        # 	{
        # 		"housing_unit_characteristics": "HH1 (less than $15,000)",
        # 		"housing_unit_dislocation":311,
        # 		"housing_unit_in_total":3252,
        # 		"population_dislocation": 311,
        # 		"population_in_total": 3252
        # 	},
        # 	{
        # 		"housing_unit_characteristics": "HH2 ($15,000 to $35,000)",
        # 		"housing_unit_dislocation": 280,
        # 		"housing_unit_in_total": 3133,
        #       "population_dislocation": 311,
        #       "population_in_total": 3252
        # 	},
        # 	{
        # 		"housing_unit_characteristics": "HH3 ($35,000 to $70,000)",
        # 		"housing_unit_dislocation": 741,
        # 		"housing_unit_in_total": 9272,
        #       "population_dislocation": 311,
        #       "population_in_total": 3252
        # 	},
        # 	{
        # 		"housing_unit_characteristics": "HH4 ($70,000 to $120,000)",
        # 		"housing_unit_dislocation": 741,
        # 		"housing_unit_in_total": 9252,
        #       "population_dislocation": 311,
        #       "population_in_total": 3252
        # 	},
        # 	{
        # 		"housing_unit_characteristics": "HH5 (More than $120,000)",
        # 		"housing_unit_dislocation": 131,
        # 		"housing_unit_in_total": 1887,
        # 		"population_dislocation": 311,
        # 		"population_in_total": 3252
        # 	},
        # 	{
        # 		"housing_unit_characteristics":"Unknown",
        # 		"housing_unit_dislocation": 422,
        # 		"housing_unit_in_total": 4210,
        # 		"population_dislocation": 311,
        # 		"population_in_total": 3252
        # 	},
        # 	{
        # 		"housing_unit_characteristics":"total",
        # 		"housing_unit_dislocation": 1999,
        # 		"housing_unit_in_total": 23261,
        # 		"population_dislocation": 311,
        # 		"population_in_total": 3252
        # 	}
        # ]
        income_categories = ["HH1 (less than $15,000)",
                             "HH2 ($15,000 to $35,000)",
                             "HH3 ($35,000 to $70,000)",
                             "HH4 ($70,000 to $120,000)",
                             "HH5 (More than $120,000)",
                             "Unknown",
                             "Total"]

        hu_disl = [311, 280, 741, 741, 131, 422, 1999]
        hu_disl_tot = [3252, 3133, 9272, 9252, 1887, 4210, 23261]
        pd_disl = [self.numprec * x for x in hu_disl]
        pd_disl_tot = [self.numprec * x for x in hu_disl_tot]

        # before_values = self.hua_count["HH0"]
        # after_values = self.hua_count["HHL"]
        # before_values = self.pd_count["HH0"]
        # after_values = self.pd_count["HHL"]

        huapd_income = {}
        pd_by_income_json = []
        for i in range(len(income_categories)):
            huapd_income[self.HUPD_CATEGORIES[0]] = income_categories[i]
            huapd_income[self.HUPD_CATEGORIES[1]] = hu_disl[i]
            huapd_income[self.HUPD_CATEGORIES[2]] = hu_disl_tot[i]
            huapd_income[self.HUPD_CATEGORIES[3]] = pd_disl[i]
            huapd_income[self.HUPD_CATEGORIES[4]] = pd_disl_tot[i]
            pd_by_income_json.append(huapd_income)

        print(pd_by_income_json)

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(pd_by_income_json, outfile)
        # Serializing json
        return json.dumps(pd_by_income_json)

    def pd_by_tenure(self, filename_json=None):
        """ Calculate tenure results from the output files of the Joplin Population Dislocation analysis
        and convert the results to json format.
        [
            {"housing_unit_characteristics": "Owner occupied",
             "housing_unit_dislocation": 1018,
             "housing_unit_in_total": 11344,
             "population_dislocation": 1018,
             "population_in_total": 11344
            },
            {"housing_unit_characteristics": "Renter occupied",..,..,..,..},{},{},{},{},{},
            {"total",..,..,..,..}
        ]

        Args:
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
        pd_disl = [self.numprec * x for x in hu_disl]
        pd_disl_tot = [self.numprec * x for x in hu_disl_tot]

        # before_values = self.hua_count["HH0"]
        # after_values = self.hua_count["HHL"]
        # before_values = self.pd_count["HH0"]
        # after_values = self.pd_count["HHL"]

        huapd_tenure = {}
        pd_by_tenure_json = []
        for i in range(len(tenure_categories)):
            huapd_tenure[self.HUPD_CATEGORIES[0]] = tenure_categories[i]
            huapd_tenure[self.HUPD_CATEGORIES[1]] = hu_disl[i]
            huapd_tenure[self.HUPD_CATEGORIES[2]] = hu_disl_tot[i]
            huapd_tenure[self.HUPD_CATEGORIES[3]] = pd_disl[i]
            huapd_tenure[self.HUPD_CATEGORIES[4]] = pd_disl_tot[i]
            pd_by_tenure_json.append(huapd_tenure)

        print(pd_by_tenure_json)

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(pd_by_tenure_json, outfile)
        # Serializing json
        return json.dumps(pd_by_tenure_json)

    def pd_by_housing(self, filename_json=None):
        """ Calculate housing results from the output files of the Joplin Population Dislocation analysis
        and convert the results to json format.
        [
            {"housing_unit_characteristics": "Single Family",
             "housing_unit_dislocation": 1162,
             "housing_unit_in_total": 837,
             "population_dislocation": 1162,
             "population_in_total": 837
             },{},{"Total",..,..,..,..}
        ]

        Args:
            filename_json (str): Path and name to save json output file in. E.g "pd_housing_count.json"

        Returns:
            obj: PD total count by housing. A JSON of the hua and population dislocation housing results by category.

        """
        # [
        # 	{
        # 		"housing_unit_characterstics": "Single Family",
        # 		"housing_unit_dislocation": 1162,
        # 		"housing_unit_in_total":837
        # 	},
        # 	{
        # 		"housing_unit_characterstics": "Multi Family",
        # 		"housing_unit_dislocation": 14317,
        # 		"housing_unit_in_total": 8944
        # 	},
        # 	{
        # 		"housing_unit_characterstics": "Total",
        # 		"housing_unit_dislocation": 1999,
        # 		"housing_unit_in_total": 23261
        # 	}
        # ]
        hu_dislocated = 1999
        hu_tot = 23261
        pop_dislocated = 4197
        pop_tot = 23261

        before_values = self.hua_count["HH0"]
        after_values = self.hua_count["HHL"]
        before_values = self.pd_count["HH0"]
        after_values = self.pd_count["HHL"]

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

        pd_by_housing_json = {"housing_unit_dislocation": hu_disl, "population_dislocation": pop_disl}

        print(pd_by_housing_json)

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(pd_by_housing_json, outfile)
        # Serializing json
        return json.dumps(pd_by_housing_json)

    def pd_total(self, filename_json=None):
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
            filename_json (str): Path and name to save json output file in. E.g "pd_total_count.json"

        Returns:
            obj: PD total count. A JSON of the hua and population dislocation total results by category.

        """
        hu_dislocated = 1999
        hu_tot = 23261
        pop_dislocated = 4197
        pop_tot = 23261

        before_values = self.hua_count["HH0"]
        after_values = self.hua_count["HHL"]
        before_values = self.pd_count["HH0"]
        after_values = self.pd_count["HHL"]

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
