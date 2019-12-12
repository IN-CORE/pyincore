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