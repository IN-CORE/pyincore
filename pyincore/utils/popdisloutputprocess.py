# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import json
import pandas as pd
import geopandas as gpd
from shapely import wkt


class PopDislOutputProcess:
    """This class converts csv results outputs of Population dislocation analysis to json format and shapefiles.

    Args:
        pop_disl_result (obj): IN-CORE dataset for Joplin Population Dislocation (PD) results.
        pop_disl_result_path (obj): A fallback for the case that Joplin PD object is not provided.
            For example a user wants to directly pass in csv files, a path to PD results.
        filter_name (str): A string to filter data by name, default empty. Example: filter_name="Joplin" for Joplin
            inventory, other is Duquesne etc. Name must be valid.
        filter_guid (bool): A flag to filter all data, default True counts only Joplin buildings.
        vacant_disl (bool): A flag to include vacant (Vacant for tenure) dislocation

    """

    HUPD_CATEGORIES = [
        "household_characteristics",
        "household_dislocated",
        "total_households",
        "percent_household_dislocated",
        "population_dislocated",
        "total_population",
        "percent_population_dislocated",
    ]

    def __init__(
        self,
        pop_disl_result,
        pop_disl_result_path=None,
        filter_name=None,
        filter_guid=True,
        vacant_disl=True,
    ):
        if pop_disl_result_path:
            pd_result = pd.read_csv(pop_disl_result_path, low_memory=False)
        else:
            pd_result = pop_disl_result.get_dataframe_from_csv(low_memory=False)
        pd_result["geometry"] = pd_result["geometry"].apply(wkt.loads)

        # keep only inventory with guid; filter for Joplin since only Joplin inventory has guids
        if filter_guid:
            if filter_name:
                pd_result_flag = pd_result[
                    (pd_result["guid"].notnull())
                    & (pd_result["numprec"].notnull())
                    & (pd_result["plcname10"] == filter_name)
                ]
                # only keep guid and place
                pd_result_shp = pd_result[
                    (pd_result["guid"].notnull())
                    & (pd_result["numprec"].notnull())
                    & (pd_result["plcname10"] == filter_name)
                ]
            else:
                pd_result_flag = pd_result[
                    (pd_result["guid"].notnull()) & (pd_result["numprec"].notnull())
                ]
                # only keep guid
                pd_result_shp = pd_result[
                    (pd_result["guid"].notnull()) & (pd_result["numprec"].notnull())
                ]
        else:
            if filter_name:
                pd_result_flag = pd_result[
                    (pd_result["numprec"].notnull())
                    & (pd_result["plcname10"] == filter_name)
                ]
                # only keep guid and place
                pd_result_shp = pd_result[
                    (pd_result["numprec"].notnull())
                    & (pd_result["plcname10"] == filter_name)
                ]
            else:
                pd_result_flag = pd_result[(pd_result["numprec"].notnull())]
                # only keep guid
                pd_result_shp = pd_result[(pd_result["numprec"].notnull())]

        self.vacant_disl = vacant_disl
        self.pop_disl_result = pd_result_flag
        self.pop_disl_result_shp = pd_result_shp

    def get_heatmap_shp(self, filename="pop-disl-numprec.shp"):
        """Convert and filter population dislocation output to shapefile that contains only guid and numprec columns

        Args:
            filename (str): Path and name to save shapefile output file in. E.g "heatmap.shp"

        Returns:
            str: full path and filename of the shapefile

        """
        df = self.pop_disl_result_shp

        # save as shapefile
        gdf = gpd.GeoDataFrame(df, crs="epsg:4326")
        gdf = gdf[["guid", "numprec", "geometry", "dislocated"]]

        # keep original dislocated results
        gdf["numprec_dislocated"] = gdf["numprec"].copy()

        # set numprec = 0 if dislocated is False
        gdf.loc[~gdf["dislocated"], "numprec_dislocated"] = 0

        # set numprec numprec_dislocated and  as integer
        gdf["numprec"] = gdf["numprec"].fillna(0).astype(int)
        gdf["numprec_dislocated"] = gdf["numprec_dislocated"].fillna(0).astype(int)
        gdf.to_file(filename)

        return filename

    def pd_by_race(self, filename_json=None):
        """Calculate race results from the output files of the Joplin Population Dislocation analysis
        and convert the results to json format.
        [
            {"household_characteristics": "Not Hispanic/White",
             "household_dislocated": 1521,
             "total_households": 18507,
             "%_household_dislocated": 7.3,
             "population_dislocated",
             "total_population",
             "%_population_dislocated"
            },{"household_characteristics": "Not Hispanic/Black",..,..},{},{},
            {"No race Ethnicity Data"},{"Total"}
        ]

        Args:
            filename_json (str): Path and name to save json output file in. E.g "pd_race_count.json"

        Returns:
            obj: PD total count by race. A JSON of the hua and population dislocation race results by category.

        """
        # Race categories
        # The numbering follows the Community description notebook
        # 0 - Vacant HU No Race Ethnicity Data, 1 - Not Hispanic/White, 2 - Not Hispanic/Black
        # 3 - Not Hispanic/Other race, 4 - Hispanic, 5 - No Race or Ethnicity Data
        race_categories = [
            "Vacant HU No Race or Ethnicity Data",
            "Not Hispanic/White",
            "Not Hispanic/Black",
            "Not Hispanic/Other Race",
            "Hispanic",
            "No Race or Ethnicity Data",
            "Total",
        ]

        huapd = self.pop_disl_result
        # Allocated by race and ethnicity
        huapd["hua_re"] = "0"
        huapd.loc[(huapd["race"] == 1) & (huapd["hispan"] == 0), "hua_re"] = "1"
        huapd.loc[(huapd["race"] == 2) & (huapd["hispan"] == 0), "hua_re"] = "2"
        huapd.loc[
            (huapd["race"].isin([3, 4, 5, 6, 7])) & (huapd["hispan"] == 0), "hua_re"
        ] = "3"
        huapd.loc[(huapd["hispan"] == 1), "hua_re"] = "4"
        huapd.loc[(huapd["gqtype"] >= 1), "hua_re"] = "5"
        hua_vals = huapd["hua_re"].value_counts()

        hua_tot = []
        for i in range(len(race_categories) - 1):
            try:
                hua_tot.append(int(hua_vals[str(i)]))
            except Exception:
                hua_tot.append(0)
        hua_tot.append(int(sum(hua_tot)))

        pop_tot = []
        for i in range(len(race_categories) - 1):
            pop_tot.append(int(huapd["numprec"].where(huapd["hua_re"] == str(i)).sum()))
        pop_tot.append(int(sum(pop_tot)))

        # Dislocated by race and ethnicity
        huapd["hud_re"] = ""
        huapd.loc[huapd["dislocated"], "hud_re"] = "0"
        huapd.loc[
            (huapd["race"] == 1) & (huapd["hispan"] == 0) & huapd["dislocated"],
            "hud_re",
        ] = "1"
        huapd.loc[
            (huapd["race"] == 2) & (huapd["hispan"] == 0) & huapd["dislocated"],
            "hud_re",
        ] = "2"
        huapd.loc[
            (huapd["race"].isin([3, 4, 5, 6, 7]))
            & (huapd["hispan"] == 0)
            & huapd["dislocated"],
            "hud_re",
        ] = "3"
        huapd.loc[(huapd["hispan"] == 1) & huapd["dislocated"], "hud_re"] = "4"
        huapd.loc[(huapd["gqtype"] >= 1) & huapd["dislocated"], "hud_re"] = "5"
        hud_vals = huapd["hud_re"].value_counts()

        hua_disl = []
        for i in range(len(race_categories) - 1):
            try:
                hua_disl.append(int(hud_vals[str(i)]))
            except Exception:
                hua_disl.append(0)
        hua_disl.append(int(sum(hua_disl)))

        pd_disl = []
        for i in range(len(race_categories) - 1):
            pd_disl.append(int(huapd["numprec"].where(huapd["hud_re"] == str(i)).sum()))
        pd_disl.append(int(sum(pd_disl)))

        pd_by_race_json = []
        for i in range(len(race_categories)):
            huapd_race = {}
            huapd_race[self.HUPD_CATEGORIES[0]] = race_categories[i]
            huapd_race[self.HUPD_CATEGORIES[1]] = hua_disl[i]
            huapd_race[self.HUPD_CATEGORIES[2]] = hua_tot[i]
            if hua_tot[i]:
                huapd_race[self.HUPD_CATEGORIES[3]] = 100 * (hua_disl[i] / hua_tot[i])
            else:
                huapd_race[self.HUPD_CATEGORIES[3]] = None
            huapd_race[self.HUPD_CATEGORIES[4]] = pd_disl[i]
            huapd_race[self.HUPD_CATEGORIES[5]] = pop_tot[i]
            if pop_tot[i]:
                huapd_race[self.HUPD_CATEGORIES[6]] = 100 * (pd_disl[i] / pop_tot[i])
            else:
                huapd_race[self.HUPD_CATEGORIES[6]] = None
            pd_by_race_json.append(huapd_race)
        # print(pd_by_race_json)

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(pd_by_race_json, outfile)
        # Serializing json
        return json.dumps(pd_by_race_json)

    def pd_by_income(self, filename_json=None):
        """Calculate income results from the output files of the Joplin Population Dislocation analysis
        and convert the results to json format.
        [
            {"household_characteristics": "HH1 (less than $15,000)",
             "household_dislocated": 311,
             "total_households": 3252,
             "%_household_dislocated": 7.3,
             "population_dislocated": 311,
             "total_population": 3252,
             "%_population_dislocated"
             },
             {"HH2 ($15,000 to $35,000)",..,..,..,..},{},{},{},{},
             {"Unknown",..,..,..,..}
        ]

        Args:
            filename_json (str): Path and name to save json output file in. E.g "pd_income_count.json"

        Returns:
            obj: PD total count by income. A JSON of the hua and population dislocation income results by category.

        """
        income_categories = [
            "HH1 (less than $15,000)",
            "HH2 ($15,000 to $35,000)",
            "HH3 ($35,000 to $70,000)",
            "HH4 ($70,000 to $120,000)",
            "HH5 (More than $120,000)",
            "Unknown",
            "Total",
        ]

        huapd = self.pop_disl_result
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
            disl = huapd.loc[
                (huapd["hhinc"] == i) & huapd["dislocated"], ["dislocated"]
            ].sum()
            hua_disl.append(int(disl))
        disl_unknown = huapd.loc[
            pd.isna(huapd["hhinc"]) & huapd["dislocated"], ["dislocated"]
        ].sum()
        hua_disl.append(int(disl_unknown))
        hua_disl.append(int(sum(hua_disl)))

        pd_disl = []
        for i in range(1, 6):
            disl = huapd.loc[
                (huapd["hhinc"] == i) & huapd["dislocated"], ["numprec"]
            ].sum()
            pd_disl.append(int(disl))
        disl_unknown = huapd.loc[
            pd.isna(huapd["hhinc"]) & huapd["dislocated"], ["numprec"]
        ].sum()
        pd_disl.append(int(disl_unknown))
        pd_disl.append(int(sum(pd_disl)))

        pd_by_income_json = []
        for i in range(len(income_categories)):
            huapd_income = {}
            huapd_income[self.HUPD_CATEGORIES[0]] = income_categories[i]
            huapd_income[self.HUPD_CATEGORIES[1]] = hua_disl[i]
            huapd_income[self.HUPD_CATEGORIES[2]] = hua_tot[i]
            if hua_tot[i]:
                huapd_income[self.HUPD_CATEGORIES[3]] = 100 * (hua_disl[i] / hua_tot[i])
            else:
                huapd_income[self.HUPD_CATEGORIES[3]] = None
            huapd_income[self.HUPD_CATEGORIES[4]] = pd_disl[i]
            huapd_income[self.HUPD_CATEGORIES[5]] = pop_tot[i]
            if pop_tot[i]:
                huapd_income[self.HUPD_CATEGORIES[6]] = 100 * (pd_disl[i] / pop_tot[i])
            else:
                huapd_income[self.HUPD_CATEGORIES[6]] = None
            pd_by_income_json.append(huapd_income)
        # print(pd_by_income_json)

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(pd_by_income_json, outfile)
        # Serializing json
        return json.dumps(pd_by_income_json)

    def pd_by_tenure(self, filename_json=None):
        """Calculate tenure results from the output files of the Joplin Population Dislocation analysis
        and convert the results to json format.
        [
            {"household_characteristics": "Owner occupied",
             "household_dislocated": 1018,
             "total_households": 11344,
             "%_household_dislocated": 7.3,
             "population_dislocated": 1018,
             "total_population": 11344,
             "%_population_dislocated"
            },
            {"household_characteristics": "Renter occupied",..,..,..,..},{},{},{},{},{},
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
        tenure_categories = [
            "Owner occupied",
            "Renter occupied",
            "Nursing facilities",
            "Other group quarters",
            "Vacant for rent",
            "Vacant for sale",
            "Vacant other",
            "Total",
        ]

        huapd = self.pop_disl_result
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
            try:
                hua_tot.append(int(hua_vals[str(i)]))
            except Exception:
                hua_tot.append(0)
        hua_tot.append(int(sum(hua_tot[1:])))

        pop_tot = []
        for i in range(len(tenure_categories)):
            pop_tot.append(
                int(huapd["numprec"].where(huapd["hua_tnr"] == str(i)).sum())
            )
        pop_tot.append(int(sum(pop_tot[1:])))

        # Dislocated by tenure
        huapd["hud_tnr"] = ""
        huapd.loc[huapd["dislocated"], "hud_tnr"] = "0"
        huapd.loc[(huapd["ownershp"] == 1.0) & huapd["dislocated"], "hud_tnr"] = "1"
        huapd.loc[(huapd["ownershp"] == 2.0) & huapd["dislocated"], "hud_tnr"] = "2"
        huapd.loc[(huapd["gqtype"] == 3) & huapd["dislocated"], "hud_tnr"] = "3"
        huapd.loc[
            huapd["gqtype"].isin([1, 2, 4, 5, 6, 7, 8]) & huapd["dislocated"], "hud_tnr"
        ] = "4"
        huapd.loc[huapd["vacancy"].isin([1, 2]) & huapd["dislocated"], "hud_tnr"] = "5"
        huapd.loc[huapd["vacancy"].isin([3, 4]) & huapd["dislocated"], "hud_tnr"] = "6"
        huapd.loc[
            huapd["vacancy"].isin([5, 6, 7]) & huapd["dislocated"], "hud_tnr"
        ] = "7"
        hud_vals = huapd["hud_tnr"].value_counts()
        hua_disl = []
        for i in range(len(tenure_categories)):
            try:
                hua_disl.append(int(hud_vals[str(i)]))
            except Exception:
                hua_disl.append(0)
        # If vacant_disl is False the Vacant places do not dislocate (set to 0).
        for i in range(len(tenure_categories)):
            if not self.vacant_disl and "Vacant" in tenure_categories[i]:
                hua_disl[i + 1] = 0

        hua_disl.append(int(sum(hua_disl[1:])))

        pd_disl = []
        for i in range(len(tenure_categories)):
            pd_disl.append(
                int(huapd["numprec"].where(huapd["hud_tnr"] == str(i)).sum())
            )
        pd_disl.append(int(sum(pd_disl[1:])))

        pd_by_tenure_json = []
        for i in range(len(tenure_categories)):
            huapd_tenure = {}
            huapd_tenure[self.HUPD_CATEGORIES[0]] = tenure_categories[i]
            huapd_tenure[self.HUPD_CATEGORIES[1]] = hua_disl[i + 1]
            huapd_tenure[self.HUPD_CATEGORIES[2]] = hua_tot[i + 1]
            if hua_tot[i + 1]:
                huapd_tenure[self.HUPD_CATEGORIES[3]] = 100 * (
                    hua_disl[i + 1] / hua_tot[i + 1]
                )
            else:
                huapd_tenure[self.HUPD_CATEGORIES[3]] = None
            huapd_tenure[self.HUPD_CATEGORIES[4]] = pd_disl[i + 1]
            huapd_tenure[self.HUPD_CATEGORIES[5]] = pop_tot[i + 1]
            if pop_tot[i + 1]:
                huapd_tenure[self.HUPD_CATEGORIES[6]] = 100 * (
                    pd_disl[i + 1] / pop_tot[i + 1]
                )
            else:
                huapd_tenure[self.HUPD_CATEGORIES[6]] = None
            pd_by_tenure_json.append(huapd_tenure)
        # print(pd_by_tenure_json)

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(pd_by_tenure_json, outfile)
        # Serializing json
        return json.dumps(pd_by_tenure_json)

    def pd_by_housing(self, filename_json=None):
        """Calculate housing results from the output files of the Joplin Population Dislocation analysis
        using huestimate column (huestimate = 1 is single family, huestimate > 1 means multi family house)
        and convert the results to json format.
        [
            {"household_characteristics": "Single Family",
             "household_dislocated": 1162,
             "total_households": 837,
             "%_household_dislocated": 7.3,
             "population_dislocated": 1162,
             "total_population": 837,
             "%_population_dislocated"
             },{},{"Total",..,..,..,..}
        ]

        Args:
            filename_json (str): Path and name to save json output file in. E.g "pd_housing_count.json"

        Returns:
            obj: PD total count by housing. A JSON of the hua and population dislocation housing results by category.

        """
        # Household categories
        # 0 - Vacant HU No Tenure Data, 1 - Single Family, 2 - Multi Family
        household_categories = ["Single Family", "Multi Family", "Total"]

        huapd = self.pop_disl_result
        # Allocated by housing
        huapd["hua_house"] = "0"
        huapd.loc[(huapd["huestimate"] == 1.0), "hua_house"] = "1"
        huapd.loc[(huapd["huestimate"] > 1.0), "hua_house"] = "2"
        hua_vals = huapd["hua_house"].value_counts()
        hua_tot = []
        for i in range(len(household_categories)):
            try:
                hua_tot.append(int(hua_vals[str(i)]))
            except Exception:
                hua_tot.append(0)
        hua_tot.append(int(sum(hua_tot[1:])))

        pop_tot = []
        for i in range(len(household_categories)):
            pop_tot.append(
                int(huapd["numprec"].where(huapd["hua_house"] == str(i)).sum())
            )
        pop_tot.append(int(sum(pop_tot[1:])))

        # Dislocated by household
        huapd["hud_house"] = ""
        huapd.loc[huapd["dislocated"], "hud_house"] = "0"
        huapd.loc[(huapd["huestimate"] == 1.0) & huapd["dislocated"], "hud_house"] = "1"
        huapd.loc[(huapd["huestimate"] > 1.0) & huapd["dislocated"], "hud_house"] = "2"
        hud_vals = huapd["hud_house"].value_counts()
        hua_disl = []
        for i in range(len(household_categories)):
            try:
                hua_disl.append(int(hud_vals[str(i)]))
            except Exception:
                hua_disl.append(0)
        hua_disl.append(int(sum(hua_disl[1:])))

        pd_disl = []
        for i in range(len(household_categories)):
            pd_disl.append(
                int(huapd["numprec"].where(huapd["hud_house"] == str(i)).sum())
            )
        pd_disl.append(int(sum(pd_disl[1:])))

        pd_by_housing_json = []
        for i in range(len(household_categories)):
            huapd_household = {}
            huapd_household[self.HUPD_CATEGORIES[0]] = household_categories[i]
            huapd_household[self.HUPD_CATEGORIES[1]] = hua_disl[i + 1]
            huapd_household[self.HUPD_CATEGORIES[2]] = hua_tot[i + 1]
            if hua_tot[i + 1]:
                huapd_household[self.HUPD_CATEGORIES[3]] = 100 * (
                    hua_disl[i + 1] / hua_tot[i + 1]
                )
            else:
                huapd_household[self.HUPD_CATEGORIES[3]] = None
            huapd_household[self.HUPD_CATEGORIES[4]] = pd_disl[i + 1]
            huapd_household[self.HUPD_CATEGORIES[5]] = pop_tot[i + 1]
            if pop_tot[i + 1]:
                huapd_household[self.HUPD_CATEGORIES[6]] = 100 * (
                    pd_disl[i + 1] / pop_tot[i + 1]
                )
            else:
                huapd_household[self.HUPD_CATEGORIES[6]] = None
            pd_by_housing_json.append(huapd_household)
        # print(pd_by_housing_json)

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(pd_by_housing_json, outfile)
        return json.dumps(pd_by_housing_json)

    def pd_total(self, filename_json=None):
        """Calculate total results from the output files of the Joplin Population Dislocation analysis
        and convert the results to json format.
        {   "household_dislocated": {
                "dislocated": {
                    "number": 1999,
                    "percentage": 0.085
                }, "not_dislocated": {}, "total": {}
            },"population_dislocated": {"dislocated": {},"not_dislocated": {}, "total": {}}
        }

        Args:
            filename_json (str): Path and name to save json output file in. E.g "pd_total_count.json"

        Returns:
            obj: PD total count. A JSON of the hua and population dislocation total results by category.

        """
        # Dislocated by race and ethnicity
        hud = self.pop_disl_result
        hud_vals = hud["dislocated"].value_counts()

        hud_vals_false = 0
        hud_vals_true = 0

        # if there is "False" category, assign the value
        if False in hud_vals.keys().values:
            hud_vals_false = int(hud_vals[False])

        # if there is "True" category, assign the value
        if True in hud_vals.keys().values:
            hud_vals_true = int(hud_vals[True])

        hua_disl = [hud_vals_false, hud_vals_true]

        pd_disl = [
            int(hud["numprec"].where(hud["dislocated"] == 0).sum()),
            int(hud["numprec"].where(hud["dislocated"] == 1).sum()),
        ]

        hua_tot = sum(hua_disl)
        pop_tot = sum(pd_disl)

        no_hua_tot = {"households": None, "percent_of_households": None}
        hua_disl_tot = {}
        hua_disl_tot["dislocated"] = no_hua_tot
        hua_disl_tot["not_dislocated"] = no_hua_tot
        hua_disl_tot["total"] = no_hua_tot
        if hua_tot:
            hua_disl_tot["dislocated"] = {
                "households": hua_disl[1],
                "percent_of_households": 100 * (hua_disl[1] / hua_tot),
            }
            hua_disl_tot["not_dislocated"] = {
                "households": hua_tot - hua_disl[1],
                "percent_of_households": 100 * ((hua_tot - hua_disl[1]) / hua_tot),
            }
            hua_disl_tot["total"] = {
                "households": hua_tot,
                "percent_of_households": 100,
            }

        no_pop_tot = {"population": None, "percent_of_population": None}
        pop_disl_tot = {}
        pop_disl_tot["dislocated"] = no_pop_tot
        pop_disl_tot["not_dislocated"] = no_pop_tot
        pop_disl_tot["total"] = no_pop_tot
        if pop_tot:
            pop_disl_tot["dislocated"] = {
                "population": pd_disl[1],
                "percent_of_population": 100 * (pd_disl[1] / pop_tot),
            }
            pop_disl_tot["not_dislocated"] = {
                "population": pop_tot - pd_disl[1],
                "percent_of_population": 100 * ((pop_tot - pd_disl[1]) / pop_tot),
            }
            pop_disl_tot["total"] = {
                "population": pop_tot,
                "percent_of_population": 100,
            }

        pd_total_json = {
            "household_dislocation_in_total": hua_disl_tot,
            "population_dislocation_in_total": pop_disl_tot,
        }
        # print(pd_total_json)

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(pd_total_json, outfile)
        return json.dumps(pd_total_json)
