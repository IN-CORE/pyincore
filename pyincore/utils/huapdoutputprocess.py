# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import json
import numpy as np
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
            self.hua_count = pd.read_csv(hua_count_path, low_memory=False)
        else:
            self.hua_count = hua_count_path.get_dataframe_from_csv(low_memory=False)
        if pd_count_path:
            self.pd_count = pd.read_csv(pd_count_path, low_memory=False)
        else:
            self.pd_count = pd_count_path.get_dataframe_from_csv(low_memory=False)

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
        # Race categories
        # The numbering follows the Community description notebook
        # 0 - Vacant HU No Race Ethnicity Data, 1 - White alone, Not Hispanic, 2 - Black alone, Not Hispanic
        # 3 - Other race, Not Hispanic, 4 - Any race, Hispanic, 5 - No race Ethnicity Data
        race_categories = ["White alone, Not Hispanic",
                           "Black alone, Not Hispanic",
                           "Other race, Not Hispanic",
                           "Any race, Hispanic",
                           "No race Ethnicity Data",
                           "Total"]

        # Allocated by race and ethnicity
        hua = self.hua_count
        hua["hua_re"] = "0"
        hua.loc[(hua["race"] == 1) & (hua["hispan"] == 0), "hua_re"] = "1"
        hua.loc[(hua["race"] == 2) & (hua["hispan"] == 0), "hua_re"] = "2"
        hua.loc[(hua["race"].isin([3, 4, 5, 6, 7])) & (hua["hispan"] == 0), "hua_re"] = "3"
        hua.loc[(hua["hispan"] == 1), "hua_re"] = "4"
        hua.loc[(hua["gqtype"] >= 1), "hua_re"] = "5"
        hua_vals = hua["hua_re"].value_counts()
        hua_tot = []
        for i in range(len(race_categories)):
            hua_tot.append(int(hua_vals[str(i)]))
        hua_tot.append(int(sum(hua_tot[1:])))
        print(hua_tot)

        pop_tot = []
        pop_tot.append(int(hua["numprec"].where(hua["hua_re"] == "0").sum()))
        pop_tot.append(int(hua["numprec"].where(hua["hua_re"] == "1").sum()))
        pop_tot.append(int(hua["numprec"].where(hua["hua_re"] == "2").sum()))
        pop_tot.append(int(hua["numprec"].where(hua["hua_re"] == "3").sum()))
        pop_tot.append(int(hua["numprec"].where(hua["hua_re"] == "4").sum()))
        pop_tot.append(int(hua["numprec"].where(hua["hua_re"] == "5").sum()))
        pop_tot.append(int(sum(pop_tot[1:])))
        print(pop_tot)

        # Dislocated by race and ethnicity  
        hud = self.pd_count
        hud["hud_re"] = "0"
        hud.loc[(hud["race"] == 1) & (hud["hispan"] == 0) & hud["dislocated"], "hud_re"] = "1"
        hud.loc[(hud["race"] == 2) & (hud["hispan"] == 0) & hud["dislocated"], "hud_re"] = "2"
        hud.loc[(hud["race"].isin([3, 4, 5, 6, 7])) & (hud["hispan"] == 0) & hud["dislocated"], "hud_re"] = "3"
        hud.loc[(hud["hispan"] == 1) & hud["dislocated"], "hud_re"] = "4"
        hud.loc[(hud["gqtype"] >= 1) & hud["dislocated"], "hud_re"] = "5"
        hud_vals = hud["hud_re"].value_counts()
        hua_disl = []
        for i in range(len(race_categories)):
            hua_disl.append(int(hud_vals[str(i)]))
        hua_disl.append(int(sum(hua_disl[1:])))
        print(hua_disl)

        pd_disl = []
        pd_disl.append(int(hud["numprec"].where(hud["hud_re"] == "0").sum()))
        pd_disl.append(int(hud["numprec"].where(hud["hud_re"] == "1").sum()))
        pd_disl.append(int(hud["numprec"].where(hud["hud_re"] == "2").sum()))
        pd_disl.append(int(hud["numprec"].where(hud["hud_re"] == "3").sum()))
        pd_disl.append(int(hud["numprec"].where(hud["hud_re"] == "4").sum()))
        pd_disl.append(int(hud["numprec"].where(hud["hud_re"] == "5").sum()))
        pd_disl.append(int(sum(pd_disl[1:])))
        print(pd_disl)

        # hua_disl = [1521, 76, 92, 41, 269, 1999]
        # hua_tot = [18507, 606, 1110, 556, 2482, 23261]
        # pd_disl = [2.14 * x for x in hua_disl]
        # pop_tot = [2.14 * x for x in hua_tot]

        pd_by_race_json = []
        for i in range(len(race_categories)):
            huapd_race = {}
            huapd_race[self.HUPD_CATEGORIES[0]] = race_categories[i]
            huapd_race[self.HUPD_CATEGORIES[1]] = hua_disl[i + 1]
            huapd_race[self.HUPD_CATEGORIES[2]] = hua_tot[i + 1]
            huapd_race[self.HUPD_CATEGORIES[3]] = pd_disl[i + 1]
            huapd_race[self.HUPD_CATEGORIES[4]] = pop_tot[i + 1]
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
        income_categories = ["HH1 (less than $15,000)",
                             "HH2 ($15,000 to $35,000)",
                             "HH3 ($35,000 to $70,000)",
                             "HH4 ($70,000 to $120,000)",
                             "HH5 (More than $120,000)",
                             "Unknown",
                             "Total"]
        
        # Allocated by income
        hua = self.hua_count
        hua_tot = []
        for i in range (1, 6):
            hua_tot.append((hua["hhinc"] == i).sum())
        hua_tot.append(pd.isna(hua["hhinc"]).sum())
        hua_tot.append(int(sum(hua_tot)))
        print(hua_tot)

        pop_tot = []
        for i in range(1, 6):
            pop_tot.append(int(hua["numprec"].where(hua["hhinc"] == i).sum()))
        pop_tot.append(int(hua["numprec"].where(pd.isna(hua["hhinc"])).sum()))
        pop_tot.append(int(sum(pop_tot)))
        print(pop_tot)

        # Dislocated by income
        hua_income = hua[["guid", "hhinc"]]
        pd_dislocated = self.pd_count[["guid", "dislocated"]]
        print(hua_income)
        print(pd_dislocated)
        # hud= self.pd_count
        pd_dislocated.set_index("guid", inplace=True)
        hua_income.set_index("guid", inplace=True)
        hud = pd_dislocated.head(100).set_index("guid").join(hua_income.head(100).set_index("guid"), how='left')
        # hud = pd.merge(pd_dislocated, hua_income, how="left", on="guid")
        print(hud)
        hud["hud_inc"] = "0"
        hud.loc[(hud["race"] == 1) & (hud["hispan"] == 0) & hud["dislocated"], "hud_inc"] = "1"
        hud.loc[(hud["race"] == 2) & (hud["hispan"] == 0) & hud["dislocated"], "hud_inc"] = "2"
        hud.loc[(hud["race"].isin([3, 4, 5, 6, 7])) & (hud["hispan"] == 0) & hud["dislocated"], "hud_inc"] = "3"
        hud.loc[(hud["hispan"] == 1) & hud["dislocated"], "hud_inc"] = "4"
        hud.loc[(hud["gqtype"] >= 1) & hud["dislocated"], "hud_inc"] = "5"
        hud_vals = hud["hud_inc"].value_counts()
        hua_disl = []
        for i in range(len(income_categories)):
            hua_disl.append(int(hud_vals[str(i)]))
        hua_disl.append(int(sum(hua_disl[0:])))
        print(hua_disl)

        pd_disl = []
        pd_disl.append(int(hud["numprec"].where(hud["hud_inc"] == "0").sum()))
        pd_disl.append(int(hud["numprec"].where(hud["hud_inc"] == "1").sum()))
        pd_disl.append(int(hud["numprec"].where(hud["hud_inc"] == "2").sum()))
        pd_disl.append(int(hud["numprec"].where(hud["hud_inc"] == "3").sum()))
        pd_disl.append(int(hud["numprec"].where(hud["hud_inc"] == "4").sum()))
        pd_disl.append(int(hud["numprec"].where(hud["hud_inc"] == "5").sum()))
        pd_disl.append(int(sum(pd_disl[1:])))
        print(pd_disl)

        hu_disl = [311, 280, 741, 741, 131, 422, 1999]
        hu_disl_tot = [3252, 3133, 9272, 9252, 1887, 4210, 23261]
        pd_disl = [2.14 * x for x in hu_disl]
        pd_disl_tot = [2.14 * x for x in hu_disl_tot]

        # before_values = self.hua_count["HH0"]
        # after_values = self.hua_count["HHL"]
        # before_values = self.pd_count["HH0"]
        # after_values = self.pd_count["HHL"]

        pd_by_income_json = []
        for i in range(len(income_categories)):
            huapd_income = {}
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
        # Tenure categories
        # The numbering follows the Community description notebook
        # 0 - Vacant HU No Tenure Data, 1 - Owner occupied, 2 - Renter occupied,
        # 3 - Nursing facilities, 4 - Other group quarters, 5 - Vacant for rent
        # 6 - Vacant for sale, 7 - Vacant other
        tenure_categories = ["Owner occupied",
                             "Renter occupied",
                             "Nursing facilities",
                             "Other group quarters",
                             "Vacant for rent",
                             "Vacant for sale",
                             "Vacant other"
                             "Total"]

        # Allocated by tenure
        hua = self.hua_count
        hua["hua_tnr"] = "0"
        hua.loc[hua["ownershp"] == 1.0, "hua_tnr"] = "1"
        hua.loc[hua["ownershp"] == 2.0, "hua_tnr"] = "2"
        hua.loc[hua["gqtype"] == 3, "hua_tnr"] = "3"
        hua.loc[hua["gqtype"].isin([1,2,4,5,6,7,8]), "hua_tnr"] = "4"
        hua.loc[hua["vacancy"].isin([1,2]), "hua_tnr"] = "5"
        hua.loc[hua["vacancy"].isin([3,4]), "hua_tnr"] = "6"
        hua.loc[hua["vacancy"].isin([5,6,7]), "hua_tnr"] = "7"
        hua_vals = hua["hua_tnr"].value_counts()
        hua_tot = []
        for i in range(len(tenure_categories)):
            hua_tot.append(int(hua_vals[str(i)]))
        hua_tot.append(int(sum(hua_tot[1:])))
        print(hua_tot)

        pop_tot = []
        pop_tot.append(int(hua["numprec"].where(hua["hua_tnr"] == "0").sum()))
        pop_tot.append(int(hua["numprec"].where(hua["hua_tnr"] == "1").sum()))
        pop_tot.append(int(hua["numprec"].where(hua["hua_tnr"] == "2").sum()))
        pop_tot.append(int(hua["numprec"].where(hua["hua_tnr"] == "3").sum()))
        pop_tot.append(int(hua["numprec"].where(hua["hua_tnr"] == "4").sum()))
        pop_tot.append(int(hua["numprec"].where(hua["hua_tnr"] == "5").sum()))
        pop_tot.append(int(hua["numprec"].where(hua["hua_tnr"] == "6").sum()))
        pop_tot.append(int(hua["numprec"].where(hua["hua_tnr"] == "7").sum()))
        pop_tot.append(int(sum(pop_tot[1:])))
        print(pop_tot)

        # hua["tenure_status"] = "0"
        # hua.loc[(hua["ownershp"] == 1), "tenure_status"] = "1"
        # hua.loc[(hua["ownershp"] == 2), "tenure_status"] = "2"
        # hua_hist = hua["tenure_status"].value_counts()
        # print(hua_hist)
        #
        # table = pd.pivot_table(hua, values="numprec", index=["hua_re"],
        #                        margins=True, margins_name='Total',
        #                        columns=["tenure_status"], aggfunc=[np.sum])
        # print(table)

        # Dislocated by race and ethnicity
        hud = self.pd_count
        hud["hud_tnr"] = "0"
        hud.loc[hud["ownershp"] == 1.0, "hud_tnr"] = "1"
        hud.loc[hud["ownershp"] == 2.0, "hud_tnr"] = "2"
        hud.loc[hud["gqtype"] == 3, "hud_tnr"] = "3"
        hud.loc[hud["gqtype"].isin([1,2,4,5,6,7,8]), "hud_tnr"] = "4"
        hud.loc[hud["vacancy"].isin([1,2]), "hud_tnr"] = "5"
        hud.loc[hud["vacancy"].isin([3,4]), "hud_tnr"] = "6"
        hud.loc[hud["vacancy"].isin([5,6,7]), "hud_tnr"] = "7"
        hud_vals = hud["hud_tnr"].value_counts()
        hua_disl = []
        for i in range(len(tenure_categories)):
            hua_disl.append(int(hud_vals[str(i)]))
        hua_disl.append(int(sum(hua_disl[1:])))
        print(hua_disl)

        pd_disl = []
        pd_disl.append(int(hud["numprec"].where(hud["hud_tnr"] == "0").sum()))
        pd_disl.append(int(hud["numprec"].where(hud["hud_tnr"] == "1").sum()))
        pd_disl.append(int(hud["numprec"].where(hud["hud_tnr"] == "2").sum()))
        pd_disl.append(int(hud["numprec"].where(hud["hud_tnr"] == "3").sum()))
        pd_disl.append(int(hud["numprec"].where(hud["hud_tnr"] == "4").sum()))
        pd_disl.append(int(hud["numprec"].where(hud["hud_tnr"] == "5").sum()))
        pd_disl.append(int(hud["numprec"].where(hud["hud_tnr"] == "6").sum()))
        pd_disl.append(int(hud["numprec"].where(hud["hud_tnr"] == "7").sum()))
        pd_disl.append(int(sum(pd_disl[1:])))
        print(pd_disl)

        # hua_disl = [1018, 712, 0, 3, 75, 60, 131, 1999]
        # hua_tot = [11344, 9435, 9, 18, 984, 573, 898, 23261]
        # pd_disl = [2.14 * x for x in hua_disl]
        # pop_tot = [2.14 * x for x in hua_tot]

        pd_by_tenure_json = []
        for i in range(len(tenure_categories)):
            huapd_tenure = {}
            huapd_tenure[self.HUPD_CATEGORIES[0]] = tenure_categories[i]
            huapd_tenure[self.HUPD_CATEGORIES[1]] = hua_disl[i + 1]
            huapd_tenure[self.HUPD_CATEGORIES[2]] = hua_tot[i + 1]
            huapd_tenure[self.HUPD_CATEGORIES[3]] = pd_disl[i + 1]
            huapd_tenure[self.HUPD_CATEGORIES[4]] = pop_tot[i + 1]
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

        # before_values = self.hua_count["HH0"]
        # after_values = self.hua_count["HHL"]
        # before_values = self.pd_count["HH0"]
        # after_values = self.pd_count["HHL"]

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
        # Dislocated by race and ethnicity
        hud = self.pd_count
        hud_vals = hud["dislocated"].value_counts()
        hua_disl = [hud_vals[False], hud_vals[True]]
        print(hua_disl)

        pd_disl = []
        pd_disl.append(int(hud["numprec"].where(hud["dislocated"] == 0).sum()))
        pd_disl.append(int(hud["numprec"].where(hud["dislocated"] == 1).sum()))
        print(pd_disl)

        # hu_dislocated = 1999
        # hu_tot = 23261
        # pop_dislocated = 4197
        # pop_tot = 23261

        hu_dislocated = int(hua_disl[1])
        hu_tot = int(hua_disl[0]) + int(hua_disl[1])
        pop_dislocated = int(pd_disl[1])
        pop_tot = int(pd_disl[0]) + int(pd_disl[1])
        print(hu_dislocated, hu_tot, pop_dislocated, pop_tot)

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

        pd_total_json = {"housing_unit_dislocation": hu_disl, "population_dislocation": pop_disl}

        print(pd_total_json)

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(pd_total_json, outfile)
        # Serializing json
        return json.dumps(pd_total_json)
