# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import pandas as pd
import numpy as np


class PopulationDislocationUtil:

    @staticmethod
    def merge_damage_housing_block(building_dmg: pd.DataFrame, hua_inventory: pd.DataFrame,
                                   block_data: pd.DataFrame):
        """Load CSV files to pandas Dataframes, merge them and drop unused columns.

        Args:
            building_dmg (pd.DataFrame): A building damage file in csv format.
            hua_inventory (pd.DataFrame): A housing unit allocation inventory file in csv format.
            block_data (pd.DataFrame): A block data file in csv format.

        Returns:
            pd.DataFrame: A merged table of all three inputs.

        """
        # sometimes HUA inventory has (empty) damage state columns, drop them
        damage_states = ["DS_0", "DS_1", "DS_2", "DS_3"]
        if set(damage_states).issubset(hua_inventory.columns):
            hua_inventory = hua_inventory.drop(columns=damage_states)

        # first merge hazard with house unit allocation inventory on "guid"
        # note guid can be duplicated in housing unit allocation inventory
        df = pd.merge(building_dmg, hua_inventory, how="right", on="guid", validate="1:m")

        # drop columns in building damage that are not used
        col_drops = ["LS_0", "LS_1", "LS_2", "hazardtype", "meandamage", "mdamagedev"]
        for col_drop in col_drops:
            if col_drop in df.columns:
                df = df.drop(columns=[col_drop])

        # further add block data information to the dataframe. BTW astype("Int64") converts floats to int
        # and keeps NaN. We need the conversions for a merge.
        if "bgid" in df.columns:
            df["bgid"] = df["bgid"].astype("Int64")
        elif "blockid" in df.columns:
            df["bgid"] = df["blockid"].astype("Int64")
        elif "blockid_x" in df.columns:
            df = PopulationDislocationUtil.compare_columns(df, "blockid_x", "blockid_y", True)
            if "blockid_x-blockid_y" in df.columns:
                exit("Column bgid is ambiguous, check the input datasets!")
            else:
                df["bgid"] = df["blockid"].astype("Int64")
        block_data["bgid"] = block_data["bgid"].astype("Int64")

        # outer merge on bgid
        final_df = pd.merge(df, block_data, how="left", on="bgid", validate="m:1")

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
            np.array: Dislocation probability for the household and population.

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

    @staticmethod
    def get_random_loss(seed_i: int, df: pd.DataFrame, damage_state: str, size: int):
        """
        Calculates value loss for each structure based on random beta distribution
        Value loss based on damage state is an input to the population dislocation model.

        Args:
            seed_i (int): Seed for random normal to ensure replication if run as part of a stochastic analysis,
                for example in connection with housing unit allocation analysis.
            df (pd.DataFrame): Sata frame that includes the alpha, beta, lower bound, upper bound
                for each required damage state
            damage_state (str): Damage state to calculate value loss for.
            size (int): Size of array to be generated.

        Returns:
            np.array: random distribution of value loss for each structure

        """
        # select upper bound and lower bound from input table
        alpha = df.loc[damage_state, 'alpha']
        beta = df.loc[damage_state, 'beta']
        ub = df.loc[damage_state, 'ub']
        lb = df.loc[damage_state, 'lb']

        # Generate array of random values that follow beta distribution for damage state
        random_generator = np.random.RandomState(seed_i)
        rploss = random_generator.beta(alpha, beta, size) * (ub - lb) + lb

        return rploss

    @staticmethod
    def compare_merges(table1_cols, table2_cols, table_merged):
        """ Compare two lists of columns and run compare columns on columns in both lists.
        It assumes that suffixes are _x and _y

        Args:
            table1_cols (list): columns in table 1
            table2_cols (list): columns in table 2
            table_merged (pd.DataFrame): merged table

            Returns:
                pd.DataFrame: Merged table

        """
        match_column = set(table1_cols).intersection(table2_cols)
        for col in match_column:
            # Compare two columns and marked similarity or rename and drop
            if col + "_x" in table_merged.columns and col + "_y" in table_merged.columns:
                table_merged = PopulationDislocationUtil.compare_columns(table_merged,
                                                                         col + "_x",
                                                                         col + "_y", True)
        return table_merged

    @staticmethod
    def compare_columns(table, col1, col2, drop):
        """Compare two columns. If not equal create Tru/False column, if equal rename one of them
        with the base name and drop the other.

        Args:
            table (pd.DataFrame): Data Frame table
            col1 (str): name of column 1
            col2 (str): name of column 2
            drop (bool): rename and drop column

        Returns:
            pd.DataFrame: Table with True/False column

        """
        # Values in columns match or not, add True/False column
        table.loc[table[col1] == table[col2], col1 + "-" + col2] = True
        table.loc[table[col1] != table[col2], col1 + "-" + col2] = False

        if table[col1].equals(table[col2]):
            col1_base = col1.rsplit("_", 1)[0]
            col2_base = col1.rsplit("_", 1)[0]
            if col1_base == col2_base and drop:
                table[col1_base] = table[col1]
                table = table.drop(columns=[col1, col2, col1 + "-" + col2])

        return table
