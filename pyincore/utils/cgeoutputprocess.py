# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import json
import pandas as pd


class CGEOutputProcess:
    """This class converts csv results outputs of Joplin CGE analysis to json format."""

    @staticmethod
    def get_cge_household_count(household_count, household_count_path=None, filename_json=None):
        """Calculate income results from the output files of the Joplin CGE analysis and convert the results
        to json format.
        {
            "beforeEvent": {"HH1": 3611, "HH2": 5997.0, "HH3": 7544.1, "HH4": 2394.1, "HH5": 793.0},
            "afterEvent": {"HH1": 3588, "HH2": 5929.8, "HH3": 7324.1, "HH4": 2207.5, "HH5": 766.4},
            "%_change": {"HH1": -0.6369, "HH2": -1.1, "HH3": -2.92, "HH4": -7.8, "HH5": -3.35}
        }

        Args:
            household_count (obj): IN-CORE dataset for CGE household count result.
            household_count_path (obj): A fallback for the case that household count object of CGE is not provided.
                 For example a user wants to directly pass in csv files, a path to CGE household count result.
            filename_json (str): Path and name to save json output file in. E.g "cge_total_household_count.json"

        Returns:
            obj: CGE total household count. A JSON of the total household count results ordered by category.

        """
        income_categories = ["HH1", "HH2", "HH3", "HH4", "HH5"]

        if household_count_path:
            household_group_count = pd.read_csv(household_count_path)
        else:
            household_group_count = household_count.get_dataframe_from_csv()

        before_values = household_group_count["HH0"]
        after_values = household_group_count["HHL"]

        before_event = {}
        after_event = {}
        pct_change = {}
        for i in range(len(income_categories)):
            before_event[income_categories[i]] = before_values[i]
            after_event[income_categories[i]] = after_values[i]
            if before_values[i]:
                pct_change[income_categories[i]] = 100 * ((after_values[i] - before_values[i]) / abs(before_values[i]))
            else:
                pct_change[income_categories[i]] = None

        cge_total_household_count = {"beforeEvent": before_event, "afterEvent": after_event, "%_change": pct_change}

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(cge_total_household_count, outfile)
        # Serializing json
        return json.dumps(cge_total_household_count)

    @staticmethod
    def get_cge_gross_income(gross_income, gross_income_path=None, filename_json=None):
        """Calculate household gross income results from the output files of the Joplin CGE analysis
        and convert the results to json format.
        {
            "beforeEvent": {"HH1": 13, "HH2": 153.5, "HH3": 453.1, "HH4": 438.9, "HH5": 125.0},
            "afterEvent": {"HH1": 13, "HH2": 152.5, "HH3": 445.6, "HH4": 432.9, "HH5": 124.5},
            "%_change": {"HH1": -0, "HH2": -x.x, "HH3": -x.x, "HH4": -x.x, "HH5": -x.x}
        }

        Args:
            gross_income (obj): IN-CORE dataset for CGE household gross income result.
            gross_income_path (obj): A fallback for the case that gross_income object of CGE is not provided.
                 For example a user wants to directly pass in csv files, a path to CGE gross income result.
            filename_json (str): Path and name to save json output file in. E.g "cge_total_house_income.json"

        Returns:
            obj: CGE total house income. A JSON of the total household income results ordered by category.

        """
        income_categories = ["HH1", "HH2", "HH3", "HH4", "HH5"]

        if gross_income_path:
            household_income = pd.read_csv(gross_income_path)
        else:
            household_income = gross_income.get_dataframe_from_csv()

        before_values = household_income["Y0"]
        after_values = household_income["YL"]

        before_event = {}
        after_event = {}
        pct_change = {}
        for i in range(len(income_categories)):
            before_event[income_categories[i]] = before_values[i]
            after_event[income_categories[i]] = after_values[i]
            if before_values[i]:
                pct_change[income_categories[i]] = 100 * ((after_values[i] - before_values[i]) / abs(before_values[i]))
            else:
                pct_change[income_categories[i]] = None

        cge_total_household_income = {"beforeEvent": before_event, "afterEvent": after_event, "%_change": pct_change}

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(cge_total_household_income, outfile)
        # Serializing json
        return json.dumps(cge_total_household_income)

    @staticmethod
    def get_cge_employment(pre_demand, post_demand,
                           pre_demand_path=None, post_demand_path=None,
                           filename_json=None):
        """Calculate employment results from the output files of the Joplin CGE analysis and convert the results
        to json format. The value is a sum of L1, L2 and L3 Labor groups numbers.
        {
            "afterEvent": {
                "Goods": 6680,
                "Trade": 8876,
                "Other": 23767
            },
            "beforeEvent": {"Goods": 6744, "Trade": 8940, "Other": 24147},
            "%_change": {"Goods": -0, "Trade": -x.x, "Other": -x.x}
        }

        Args:
            pre_demand (obj): IN-CORE dataset for CGE household Pre disaster factor demand result.
            post_demand (obj): IN-CORE dataset for CGE household Post disaster factor demand result.
            pre_demand_path (obj): A fallback for the case that pre_disaster_demand_factor_path object
                of CGE is not provided. For example a user wants to directly pass in csv files, a path to CGE
                household count result.
            post_demand_path (obj): A fallback for the case that post_disaster_demand_factor_path object
                of CGE is not provided. For example a user wants to directly pass in csv files, a path to CGE
                household count result.
            filename_json (str): Path and name to save json output file in. E.g "cge_employment.json"

        Returns:
            obj: CGE total employment. A JSON of the employment results ordered by category.

        """
        demand_categories = ["Goods", "Trade", "Other"]

        if pre_demand_path and post_demand_path:
            pre_disaster_demand = pd.read_csv(pre_demand_path)
            post_disaster_demand = pd.read_csv(post_demand_path)
        else:
            pre_disaster_demand = pre_demand.get_dataframe_from_csv()
            post_disaster_demand = post_demand.get_dataframe_from_csv()

        before_values = [pre_disaster_demand["GOODS"].sum(),
                         pre_disaster_demand["TRADE"].sum(),
                         pre_disaster_demand["OTHER"].sum()]
        after_values = [post_disaster_demand["GOODS"].sum(),
                        post_disaster_demand["TRADE"].sum(),
                        post_disaster_demand["OTHER"].sum()]

        before_event = {}
        after_event = {}
        pct_change = {}
        for i in range(len(demand_categories)):
            before_event[demand_categories[i]] = before_values[i]
            after_event[demand_categories[i]] = after_values[i]
            if before_values[i]:
                pct_change[demand_categories[i]] = 100 * ((after_values[i] - before_values[i]) / abs(before_values[i]))
            else:
                pct_change[demand_categories[i]] = None

        cge_employment = {"beforeEvent": before_event, "afterEvent": after_event, "%_change": pct_change}

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(cge_employment, outfile)
        # Serializing json
        return json.dumps(cge_employment)

    @staticmethod
    def get_cge_domestic_supply(domestic_supply, domestic_supply_path=None, filename_json=None):
        """Calculate domestic supply results from the output files of the Joplin CGE analysis and convert the results
        to json format.
        {
            "afterEvent": {"Goods": 662.3, "Trade": 209.0, "Other": 254.1,
                           "HS1": 22.0, "HS2": 1337.1, "HS3": 466.2},
            "beforeEvent": {"Goods": 662.3, "Trade": 209.0, "Other": 254.1,
                            "HS1": 22.0, "HS2": 1337.1, "HS3": 466.2},
            "%_change": {"Goods": -1.1, "Trade":  -1.1, "Other":  -1.1,
                            "HS1":  -1.1, "HS2":  -1.1, "HS3":  -1.1}
        }

        Args:
            domestic_supply (obj): IN-CORE dataset for CGE domestic supply result.
            domestic_supply_path (obj): A fallback for the case that domestic supply object of CGE is not provided.
                 For example a user wants to directly pass in csv files, a path to CGE household count result.
            filename_json (str): Path and name to save json output file in. E.g "cge_domestic_supply"

        Returns:
            obj: CGE total domestic supply. A JSON of the total domestic supply results ordered by category.

        """
        supply_categories = ["Goods", "Trade", "Other", "HS1", "HS2", "HS3"]
        if domestic_supply_path:
            sector_supply = pd.read_csv(domestic_supply_path)
        else:
            sector_supply = domestic_supply.get_dataframe_from_csv()

        before_values = sector_supply["DS0"]
        after_values = sector_supply["DSL"]

        before_event = {}
        after_event = {}
        pct_change = {}
        for i in range(len(supply_categories)):
            before_event[supply_categories[i]] = before_values[i]
            after_event[supply_categories[i]] = after_values[i]
            if before_values[i]:
                pct_change[supply_categories[i]] = 100 * ((after_values[i] - before_values[i]) / abs(before_values[i]))
            else:
                pct_change[supply_categories[i]] = None

        cge_domestic_supply = {"beforeEvent": before_event, "afterEvent": after_event, "%_change": pct_change}

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(cge_domestic_supply, outfile)
        # Serializing json
        return json.dumps(cge_domestic_supply)
