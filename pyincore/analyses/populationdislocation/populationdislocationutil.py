# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import pandas as pd
import numpy as np


class PopulationDislocationUtil:

    @staticmethod
    def merge_damage_housing_block(building_dmg_file, housing_allocation_file, block_data_file):
        """Load CSV files to pandas Dataframes, merge them and drop unused columns.

        Args:
            building_dmg_file: A building damage file in csv format.
            housing_allocation_file: A housing unit allocation inventory file in csv format.
            block_data_file: A block data file in csv format.

        Returns:
            pd.DataFrame: A merged table of all three inputs.

        """
        # load csv to DataFrame
        building_dmg = pd.read_csv(building_dmg_file)
        housing_allocation_inventory = pd.read_csv(housing_allocation_file)
        block_data = pd.read_csv(block_data_file)

        damage_states = ["insignific", "moderate", "heavy", "complete"]

        if set(damage_states).issubset(housing_allocation_inventory.columns):
            housing_allocation_inventory = housing_allocation_inventory.drop(columns=damage_states)

        # first merge hazard with population allocation inventory on "guid"
        # note guid can be duplicated in housing unit allocation inventory
        df = pd.merge(building_dmg, housing_allocation_inventory,
                      how="right", on="guid", validate="1:m")

        # drop columns in building damage that is not used
        df = df.drop(columns=["immocc", "lifesfty", "collprev", "hazardtype",
                              "hazardval", "meandamage",
                              "mdamagedev"])

        # further add block data information to the dataframe
        df["bgid"] = df["blockid"].astype(str)
        block_data["bgid"] = block_data["bgid"].astype(str)

        # outer merge on bgid
        final_df = pd.merge(df, block_data, how="outer", on="bgid",
                            validate="m:1")

        return final_df

    @staticmethod
    def get_disl_probability(value_loss: np.array, d_sf: np.array,
                             percent_black_bg: np.array, percent_hisp_bg: np.array):
        """
        Calculate dislocation, the probability of dislocation for the household and population.
        Probability of dislocation Damage factor,
        based on current IN-COREv1 algorithm and Bai et al. 2009 damage factors.

        The following variables are need to predict dislocation using logistic model
        see detailed explanation https://opensource.ncsa.illinois.edu/confluence/
        display/INCORE1/Household+and+Population+Dislocation?
        preview=%2F66224473%2F68289561%2FAlgorithm+3+Logistic.pdf

        Args:
            value_loss (np.array): Value loss.
            d_sf (np.array): 'Dummy' parameter.
            percent_black_bg (np.array): Block group data, percentage of black minority.
            percent_hisp_bg (np.array): Block group data, percentage of hispanic minority.

        Returns:
            numpy.array: Dislocation probability for the household and population.

        """
        # coefficients for the Logistic regression model
        coefficient = {"beta0": -0.42523,
                       "beta1": 0.02480,
                       "beta2": -0.50166,  # single family coefficient
                       "beta3": -0.01826,  # black block group coefficient
                       "beta4": -0.01198}  # hispanic block group coefficient

        disl_prob = np.zeros_like(d_sf)
        try:
            disl_prob = 1.0 / (1 + np.exp(-1.0 * (coefficient["beta0"] * 1 +
                                                  coefficient["beta1"] * (value_loss * 100) +
                                                  coefficient["beta2"] * d_sf +
                                                  coefficient["beta3"] * percent_black_bg +
                                                  coefficient["beta4"] * percent_hisp_bg)))
        except Exception as e:
            print()
            # raise e

        return disl_prob