import pandas as pd

class PopulationDislocationUtil:

    @staticmethod
    def merge_damage_population_block(building_dmg_file,
                                      population_allocation_file,
                                      block_data_file):
        """

        Args:
            building_dmg_file: building damage csv
            population_allocation_file: population inventory intermediate csv
            block_data_file: block_data.csv

        Returns:
            a merged dataframe of all three inputs
        """

        # load csv to dataframe
        building_dmg = pd.read_csv(building_dmg_file)
        population_allocation_inventory = pd.read_csv(population_allocation_file)
        block_data = pd.read_csv(block_data_file)

        # first merge hazard with popluation allocation inventory on "guid"
        # note guid can be duplicated in population allocation inventory
        df = pd.merge(building_dmg, population_allocation_inventory,
                      how="right", on="guid", validate="1:m")

        # drop columns in building damage that is not used
        df = df.drop(columns=["immocc", "lifesfty", "collprev", "hazardtype",
                              "hazardval", "meandamage",
                              "mdamagedev"])

        # further add block data information to the dataframe
        df["bgid"] = df["blockidstr"].str[1:13].astype(str)
        block_data["bgid"] = block_data["bgid"].astype(str)

        # outer merge on bgid
        final_df = pd.merge(df, block_data, how="outer", on="bgid",
                            validate="m:1")

        return final_df