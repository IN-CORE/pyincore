# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

class BuildingEconUtil:
    """Utility methods for the building loss analysis."""

    @staticmethod
    def get_appraised_val(occ_type, appraised_val):
        """ Get assessed or appraised value. We assume here that they are the same.

        Args:
            occ_type (str): Occ type.
            appraised_val (int): Appraised value.

        Returns:
            float: Appraised value.

        """
        assessed_val = float(appraised_val)
        appraised_val = assessed_val

        return appraised_val

    @staticmethod
    def get_inflation_mult(inflation_factor, inflation_table):
        """Get inflation multiplier.

        Args:
            inflation_factor (float): Default inflation factor.
            inflation_table (dict): Inflation table.

        Returns:
            float: Inflation multiplier.

        """
        if inflation_table is not None:
            tax_year = 2005
            for i in range(len(inflation_table)):
                row_year = int(inflation_table[i]["properties"]["Year"])
                if row_year == tax_year:
                    old_cpi = float(inflation_table[i]["properties"]["Annual Avg"])
                    # 2019
                    new_cpi = float(inflation_table[-2]["properties"]["Annual Avg"])
                    # debug, to get the Ergo values: year=2007, new_cpi = 207.34
                    # new_cpi = 207.34
                    inflation = (new_cpi - old_cpi) / old_cpi
                    return inflation + 1.0
            return (inflation_factor / 100.0) + 1.0
        else:
            return (inflation_factor / 100.0) + 1.0

    @staticmethod
    def get_multiplier(occ_dmg_mult, occ_type, dmg_type):
        """ Returns multiplier from the Occupation damage multiplier table.

        Args:
            occ_dmg_mult (dict): A table with occupancy damage multipliers.
            occ_type (str): Occupancy class (RES1, RES2, etc).
            dmg_type (int): 0 - Structural damage
                            1 - AS damage
                            2 - DS damage
                            3 - Content damage
        Returns:
            float: Multiplier.

        """
        dmg_types = ["SD Multiplier", "AS Multiplier", "DS Multiplier", "Content Multiplier"]
        for row in occ_dmg_mult:
            occupancy = row["properties"]["Occupancy"]
            if occupancy.lower() == occ_type.lower():
                return float(row["properties"][dmg_types[dmg_type]]) / 100.0
        return 0

    @staticmethod
    def get_econ_loss(multiplier, mean, appraised_val, inflation_mult):
        """Calculates economic loss.

        Args:
            multiplier (float): A multiplier.
            mean (float): A mean damage dev.
            appraised_val (float): A building apraised value.
            inflation_mult (float): An inflation multiplier.

        Returns:
            float: Economic loss.

        """
        return multiplier * mean * appraised_val * inflation_mult

    @staticmethod
    def get_econ_std_loss(multiplier, mean_dev, appraised_val, inflation_mult):
        """Calculates standard deviation economic loss.

        Args:
            multiplier (float): A multiplier.
            mean_dev (float): A mean damage deviation.
            appraised_val (float): A building appraised value.
            inflation_mult (float): An inflation multiplier.

        Returns:
            float: Economic standard deviation loss.

        """
        return multiplier * mean_dev * appraised_val * inflation_mult
