# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import json
import pandas as pd


class HUAPDOutputProcess:
    """This class converts csv results outputs of Population dislocation analysis to json format.

    Args:
        pd_count (obj): IN-CORE dataset for Joplin Population Dislocation (PD) results.
        pd_count_path (obj): A fallback for the case that Joplin PD object is not provided.
            For example a user wants to directly pass in csv files, a path to PD results.

    """
    HUPD_CATEGORIES = ["housing_unit_characteristics",
                       "housing_unit_dislocations",
                       "housing_unit_in_total",
                       "population_dislocations",
                       "population_in_total"
                       ]

    def __init__(self, pd_count, pd_count_path=None):
        if pd_count_path:
            self.pd_count = pd.read_csv(pd_count_path, low_memory=False)
        else:
            self.pd_count = pd_count.get_dataframe_from_csv(low_memory=False)

    def pd_by_race(self, filename_json=None):
        """ Calculate race results from the output files of the Joplin Population Dislocation analysis
        and convert the results to json format.
        [
            {"housing_unit_characteristics": "White alone, Not Hispanic",
             "housing_unit_dislocation": 1521,
             "housing_unit_in_total": 18507
            },{"housing_unit_characteristics": "Black alone, Not Hispanic",..,..},{},{},
            {"No race Ethnicity Data"},{"Total"}
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

        huapd = self.pd_count
        # Allocated by race and ethnicity
        huapd["hua_re"] = "0"
        huapd.loc[(huapd["race"] == 1) & (huapd["hispan"] == 0), "hua_re"] = "1"
        huapd.loc[(huapd["race"] == 2) & (huapd["hispan"] == 0), "hua_re"] = "2"
        huapd.loc[(huapd["race"].isin([3, 4, 5, 6, 7])) & (huapd["hispan"] == 0), "hua_re"] = "3"
        huapd.loc[(huapd["hispan"] == 1), "hua_re"] = "4"
        huapd.loc[(huapd["gqtype"] >= 1), "hua_re"] = "5"
        hua_vals = huapd["hua_re"].value_counts()
        hua_tot = []
        for i in range(len(race_categories)):
            hua_tot.append(int(hua_vals[str(i)]))
        hua_tot.append(int(sum(hua_tot[1:])))

        pop_tot = []
        for i in range(len(race_categories)):
            pop_tot.append(int(huapd["numprec"].where(huapd["hua_re"] == str(i)).sum()))
        pop_tot.append(int(sum(pop_tot[1:])))

        # Dislocated by race and ethnicity
        huapd["hud_re"] = "0"
        huapd.loc[(huapd["race"] == 1) & (huapd["hispan"] == 0) & huapd["dislocated"], "hud_re"] = "1"
        huapd.loc[(huapd["race"] == 2) & (huapd["hispan"] == 0) & huapd["dislocated"], "hud_re"] = "2"
        huapd.loc[(huapd["race"].isin([3, 4, 5, 6, 7])) & (huapd["hispan"] == 0) & huapd["dislocated"], "hud_re"] = "3"
        huapd.loc[(huapd["hispan"] == 1) & huapd["dislocated"], "hud_re"] = "4"
        huapd.loc[(huapd["gqtype"] >= 1) & huapd["dislocated"], "hud_re"] = "5"
        hud_vals = huapd["hud_re"].value_counts()
        hua_disl = []
        for i in range(len(race_categories)):
            hua_disl.append(int(hud_vals[str(i)]))
        hua_disl.append(int(sum(hua_disl[1:])))

        pd_disl = []
        for i in range(len(race_categories)):
            pd_disl.append(int(huapd["numprec"].where(huapd["hud_re"] == str(i)).sum()))
        pd_disl.append(int(sum(pd_disl[1:])))

        pd_by_race_json = []
        for i in range(len(race_categories)):
            huapd_race = {}
            huapd_race[self.HUPD_CATEGORIES[0]] = race_categories[i]
            huapd_race[self.HUPD_CATEGORIES[1]] = hua_disl[i + 1]
            huapd_race[self.HUPD_CATEGORIES[2]] = hua_tot[i + 1]
            huapd_race[self.HUPD_CATEGORIES[3]] = pd_disl[i + 1]
            huapd_race[self.HUPD_CATEGORIES[4]] = pop_tot[i + 1]
            pd_by_race_json.append(huapd_race)
        # print(pd_by_race_json)

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

        huapd = self.pd_count
        # Allocated by income
        hua_tot = []
        for i in range(1, 6):
            alloc_inc = (huapd["hhinc"] == i).sum()
            hua_tot.append(int(alloc_inc))
        hua_tot.append(int(pd.isna(huapd["hhinc"]).sum()))
        hua_tot.append(int(sum(hua_tot)))

        pop_tot = []
        for i in range(1, 6):
            alloc = huapd["numprec"].where(huapd["hhinc"] == i).sum()
            pop_tot.append(int(alloc))
        pop_tot.append(int(huapd["numprec"].where(pd.isna(huapd["hhinc"])).sum()))
        pop_tot.append(int(sum(pop_tot)))

        # Dislocated by income
        hua_disl = []
        for i in range(1, 6):
            disl = huapd.loc[(huapd["hhinc"] == i) & huapd["dislocated"], ["dislocated"]].sum()
            hua_disl.append(int(disl))
        disl_unknown = huapd.loc[pd.isna(huapd["hhinc"]) & huapd["dislocated"], ["dislocated"]].sum()
        hua_disl.append(int(disl_unknown))
        hua_disl.append(int(sum(hua_disl)))

        pd_disl = []
        for i in range(1, 6):
            disl = huapd.loc[(huapd["hhinc"] == i) & huapd["dislocated"], ["numprec"]].sum()
            pd_disl.append(int(disl))
        disl_unknown = huapd.loc[pd.isna(huapd["hhinc"]) & huapd["dislocated"], ["numprec"]].sum()
        pd_disl.append(int(disl_unknown))
        pd_disl.append(int(sum(pd_disl)))

        pd_by_income_json = []
        for i in range(len(income_categories)):
            huapd_income = {}
            huapd_income[self.HUPD_CATEGORIES[0]] = income_categories[i]
            huapd_income[self.HUPD_CATEGORIES[1]] = hua_disl[i]
            huapd_income[self.HUPD_CATEGORIES[2]] = hua_tot[i]
            huapd_income[self.HUPD_CATEGORIES[3]] = pd_disl[i]
            huapd_income[self.HUPD_CATEGORIES[4]] = pop_tot[i]
            pd_by_income_json.append(huapd_income)
        # print(pd_by_income_json)

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

        huapd = self.pd_count
        # Allocated by tenure
        huapd["hua_tnr"] = "0"
        huapd.loc[huapd["ownershp"] == 1.0, "hua_tnr"] = "1"
        huapd.loc[huapd["ownershp"] == 2.0, "hua_tnr"] = "2"
        huapd.loc[huapd["gqtype"] == 3, "hua_tnr"] = "3"
        huapd.loc[huapd["gqtype"].isin([1, 2, 4, 5, 6, 7, 8]), "hua_tnr"] = "4"
        huapd.loc[huapd["vacancy"].isin([1, 2]), "hua_tnr"] = "5"
        huapd.loc[huapd["vacancy"].isin([3, 4]), "hua_tnr"] = "6"
        huapd.loc[huapd["vacancy"].isin([5, 6, 7]), "hua_tnr"] = "7"
        hua_vals = huapd["hua_tnr"].value_counts()
        hua_tot = []
        for i in range(len(tenure_categories)):
            hua_tot.append(int(hua_vals[str(i)]))
        hua_tot.append(int(sum(hua_tot[1:])))

        pop_tot = []
        for i in range(len(tenure_categories)):
            pop_tot.append(int(huapd["numprec"].where(huapd["hua_tnr"] == str(i)).sum()))
        pop_tot.append(int(sum(pop_tot[1:])))

        # Dislocated by tenure
        huapd["hud_tnr"] = "0"
        huapd.loc[(huapd["ownershp"] == 1.0) & huapd["dislocated"], "hud_tnr"] = "1"
        huapd.loc[(huapd["ownershp"] == 2.0) & huapd["dislocated"], "hud_tnr"] = "2"
        huapd.loc[(huapd["gqtype"] == 3) & huapd["dislocated"], "hud_tnr"] = "3"
        huapd.loc[huapd["gqtype"].isin([1, 2, 4, 5, 6, 7, 8]) & huapd["dislocated"], "hud_tnr"] = "4"
        huapd.loc[huapd["vacancy"].isin([1, 2]) & huapd["dislocated"], "hud_tnr"] = "5"
        huapd.loc[huapd["vacancy"].isin([3, 4]) & huapd["dislocated"], "hud_tnr"] = "6"
        huapd.loc[huapd["vacancy"].isin([5, 6, 7]) & huapd["dislocated"], "hud_tnr"] = "7"
        hud_vals = huapd["hud_tnr"].value_counts()
        hua_disl = []
        for i in range(len(tenure_categories)):
            hua_disl.append(int(hud_vals[str(i)]))
        hua_disl.append(int(sum(hua_disl[1:])))

        pd_disl = []
        for i in range(len(tenure_categories)):
            pd_disl.append(int(huapd["numprec"].where(huapd["hud_tnr"] == str(i)).sum()))
        pd_disl.append(int(sum(pd_disl[1:])))

        pd_by_tenure_json = []
        for i in range(len(tenure_categories)):
            huapd_tenure = {}
            huapd_tenure[self.HUPD_CATEGORIES[0]] = tenure_categories[i]
            huapd_tenure[self.HUPD_CATEGORIES[1]] = hua_disl[i + 1]
            huapd_tenure[self.HUPD_CATEGORIES[2]] = hua_tot[i + 1]
            huapd_tenure[self.HUPD_CATEGORIES[3]] = pd_disl[i + 1]
            huapd_tenure[self.HUPD_CATEGORIES[4]] = pop_tot[i + 1]
            pd_by_tenure_json.append(huapd_tenure)
        # print(pd_by_tenure_json)

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(pd_by_tenure_json, outfile)
        # Serializing json
        return json.dumps(pd_by_tenure_json)

    def pd_by_housing(self, filename_json=None):
        """ Calculate housing results from the output files of the Joplin Population Dislocation analysis
        using huestimate column (huestimate = 1 is single family, huestimate > 1 means multi family house)
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
        # Household categories
        # 0 - Vacant HU No Tenure Data, 1 - Single Family, 2 - Multi Family
        household_categories = ["Single Family",
                                "Multi Family",
                                "Total"]

        huapd = self.pd_count
        # Allocated by housing
        huapd["hua_house"] = "0"
        huapd.loc[(huapd["huestimate"] == 1.0), "hua_house"] = "1"
        huapd.loc[(huapd["huestimate"] > 1.0), "hua_house"] = "2"
        hua_vals = huapd["hua_house"].value_counts()
        hua_tot = []
        for i in range(len(household_categories)):
            hua_tot.append(int(hua_vals[str(i)]))
        hua_tot.append(int(sum(hua_tot[1:])))

        pop_tot = []
        for i in range(len(household_categories)):
            pop_tot.append(int(huapd["numprec"].where(huapd["hua_house"] == str(i)).sum()))
        pop_tot.append(int(sum(pop_tot[1:])))

        # Dislocated by household
        huapd["hud_house"] = "0"
        huapd.loc[(huapd["huestimate"] == 1.0) & huapd["dislocated"], "hud_house"] = "1"
        huapd.loc[(huapd["huestimate"] > 1.0) & huapd["dislocated"], "hud_house"] = "2"
        hud_vals = huapd["hud_house"].value_counts()
        hua_disl = []
        for i in range(len(household_categories)):
            hua_disl.append(int(hud_vals[str(i)]))
        hua_disl.append(int(sum(hua_disl[1:])))

        pd_disl = []
        for i in range(len(household_categories)):
            pd_disl.append(int(huapd["numprec"].where(huapd["hud_house"] == str(i)).sum()))
        pd_disl.append(int(sum(pd_disl[1:])))

        pd_by_housing_json = []
        for i in range(len(household_categories)):
            huapd_household = {}
            huapd_household[self.HUPD_CATEGORIES[0]] = household_categories[i]
            huapd_household[self.HUPD_CATEGORIES[1]] = hua_disl[i + 1]
            huapd_household[self.HUPD_CATEGORIES[2]] = hua_tot[i + 1]
            huapd_household[self.HUPD_CATEGORIES[3]] = pd_disl[i + 1]
            huapd_household[self.HUPD_CATEGORIES[4]] = pop_tot[i + 1]
            pd_by_housing_json.append(huapd_household)
        # print(pd_by_housing_json)

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(pd_by_housing_json, outfile)
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
        hua_disl = [int(hud_vals[False]), int(hud_vals[True])]

        pd_disl = []
        pd_disl.append(int(hud["numprec"].where(hud["dislocated"] == 0).sum()))
        pd_disl.append(int(hud["numprec"].where(hud["dislocated"] == 1).sum()))

        hua_tot = sum(hua_disl)
        pop_tot = sum(pd_disl)

        hua_disl_tot = {}
        hua_disl_tot["dislocated"] = {"number": hua_disl[1], "percentage": hua_disl[1]/hua_tot}
        hua_disl_tot["not_dislocated"] = {"number": hua_tot - hua_disl[1],
                                          "percentage": (hua_tot - hua_disl[1])/hua_tot}
        hua_disl_tot["total"] = {"number": hua_tot, "percentage": 1}

        pop_disl_tot = {}
        pop_disl_tot["dislocated"] = {"number": pd_disl[1], "percentage": pd_disl[1]/pop_tot}
        pop_disl_tot["not_dislocated"] = {"number": pop_tot - pd_disl[1],
                                          "percentage": (pop_tot - pd_disl[1])/pop_tot}
        pop_disl_tot["total"] = {"number": pop_tot, "percentage": 1}

        pd_total_json = {"housing_unit_dislocation": hua_disl_tot, "population_dislocation": pop_disl_tot}
        # print(pd_total_json)

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(pd_total_json, outfile)
        return json.dumps(pd_total_json)
