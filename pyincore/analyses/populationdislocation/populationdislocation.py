# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import numpy as np
import pandas as pd
import warnings
from pyincore import BaseAnalysis
from pyincore.analyses.populationdislocation.populationdislocationutil import (
    PopulationDislocationUtil,
)


class PopulationDislocation(BaseAnalysis):
    """Population Dislocation Analysis computes dislocation for each residential structure based on the direct
    economic damage. The dislocation is calculated from four probabilities of dislocation based on a random normal
    distribution of the four damage factors presented by Bai, Hueste, Gardoni 2009.

    These four damage factors correspond to value loss. The sum of the four probabilities multiplied
    by the four probabilities of damage states was used as the probability for dislocation.

    This is different from Lin 2008
    http://hrrc.arch.tamu.edu/publications/research%20reports/08-05R%20Dislocation%20Algorithm%203.pdf
    which calculates a value loss which is the sum of the four damage factors times the four probabilities
    of damage. The two approaches produce different results.

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        super(PopulationDislocation, self).__init__(incore_client)

    def get_spec(self):
        return {
            "name": "population-dislocation",
            "description": "Population Dislocation Analysis",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": True,
                    "description": "Result CSV dataset name",
                    "type": str,
                },
                {
                    "id": "seed",
                    "required": True,
                    "description": "Seed to ensure replication if run as part of a probabilistic analysis, "
                    "for example in connection with Housing Unit Allocation analysis.",
                    "type": int,
                },
                {
                    "id": "choice_dislocation",
                    "required": False,
                    "description": "Flag to calculate choice dislocation",
                    "type": bool,
                },
                {
                    "id": "choice_dislocation_cutoff",
                    "required": False,
                    "description": "Choice dislocation cutoff",
                    "type": float,
                },
                {
                    "id": "choice_dislocation_ds",
                    "required": False,
                    "description": "Damage state to use for choice dislocation ",
                    "type": str,
                },
                {
                    "id": "unsafe_occupancy",
                    "required": False,
                    "description": "Flag to calculate unsafe occupancy",
                    "type": bool,
                },
                {
                    "id": "unsafe_occupancy_cutoff",
                    "required": False,
                    "description": "Unsafe occupancy cutoff",
                    "type": float,
                },
                {
                    "id": "unsafe_occupancy_ds",
                    "required": False,
                    "description": "Damage state to use for unsafe occupancy ",
                    "type": str,
                },
            ],
            "input_datasets": [
                {
                    "id": "building_dmg",
                    "required": True,
                    "description": "Building damage results CSV file",
                    "type": [
                        "ergo:buildingInventoryVer4",
                        "ergo:buildingDamageVer5",
                        "ergo:buildingDamageVer6",
                        "ergo:buildingInventory",
                    ],
                },
                {
                    "id": "housing_unit_allocation",
                    "required": True,
                    "description": "A csv file with the merged dataset of the inputs, aka Probabilistic"
                    "House Unit Allocation",
                    "type": ["incore:housingUnitAllocation"],
                },
                {
                    "id": "block_group_data",
                    "required": True,
                    "description": "Block group racial distribution census CSV data",
                    "type": ["incore:blockGroupData"],
                },
                {
                    "id": "value_loss_param",
                    "required": True,
                    "description": "A table with value loss beta distribution parameters based on Bai et al. 2009",
                    "type": ["incore:valuLossParam"],
                },
            ],
            "output_datasets": [
                {
                    "id": "result",
                    "parent_type": "population_block",
                    "description": "A csv file with population dislocation result "
                    "aggregated to the block group level",
                    "type": "incore:popDislocation",
                }
            ],
        }

    def run(self):
        """Executes the Population dislocation analysis.

        Returns:
            bool: True if successful, False otherwise.

        """
        # Get seed
        seed_i = self.get_parameter("seed")

        result_name = self.get_parameter("result_name")

        # Building damage dataset
        building_dmg = self.get_input_dataset("building_dmg").get_dataframe_from_csv(
            low_memory=False
        )

        # Housing unit allocation dataset
        housing_unit_alloc = self.get_input_dataset(
            "housing_unit_allocation"
        ).get_dataframe_from_csv(low_memory=False)

        # Block group dataset
        bg_data = self.get_input_dataset("block_group_data").get_dataframe_from_csv(
            low_memory=False
        )

        # Get value loss parameters
        value_loss = self.get_input_dataset("value_loss_param").get_dataframe_from_csv(
            low_memory=False
        )
        value_loss.set_index("damagestate", inplace=True)

        # Get choice_dislocation and unsafe_occupancy variables
        choice_dislocation = self.get_parameter("choice_dislocation")
        unsafe_occupancy = self.get_parameter("unsafe_occupancy")

        merged_block_inv = PopulationDislocationUtil.merge_damage_housing_block(
            building_dmg, housing_unit_alloc, bg_data
        )

        # Returns dataframe
        merged_final_inv = self.get_dislocation(seed_i, merged_block_inv, value_loss)

        # Choice dislocation and unsafe occupancy calculations
        merged_final_inv["choice_dis"] = None
        merged_final_inv["unsafe_occ"] = None
        if choice_dislocation:
            choice_dislocation_cutoff = (
                self.get_parameter("choice_dislocation_cutoff") or 0.5
            )
            choice_dislocation_ds = (
                self.get_parameter("choice_dislocation_ds") or "DS_0"
            )
            PopulationDislocationUtil.get_choice_dislocation(
                merged_final_inv, choice_dislocation_cutoff, choice_dislocation_ds
            )

        if unsafe_occupancy:
            unsafe_occupancy_cutoff = (
                self.get_parameter("unsafe_occupancy_cutoff") or 0.5
            )
            unsafe_occupancy_ds = self.get_parameter("unsafe_occupancy_ds") or "DS_3"
            PopulationDislocationUtil.get_unsafe_occupancy(
                merged_final_inv, unsafe_occupancy_cutoff, unsafe_occupancy_ds
            )

        self.set_result_csv_data("result", merged_final_inv, result_name, "dataframe")

        return True

    def get_dislocation(
        self, seed_i: int, inventory: pd.DataFrame, value_loss: pd.DataFrame
    ):
        """Calculates dislocation probability.

        Probability of dislocation, a binary variable based on the logistic probability of dislocation.
        A random number between 0 and 1 was assigned to each household.
        If the random number was less than the probability of dislocation
        then the household was determined to dislocate. This follows the logic
        that households with a greater chance of dislocated were more likely
        to have a random number less than the probability predicted.

        Args:
            seed_i (int): Seed for random number generator to ensure replication if run as part
            of a stochastic analysis, for example in connection with housing unit allocation analysis.
            inventory (pd.DataFrame): Merged building, housing unit allocation and block group inventories
            value_loss (pd.DataFrame): Table used for value loss estimates, beta distribution

        Returns:
            pd.DataFrame: An inventory with probabilities of dislocation in a separate column

        """
        # pd.Series to np.array
        # creats d_sf column it if it does not exist, overwrites d_sf values if it does
        if "huestimate" in inventory.columns:
            inventory["d_sf"] = (inventory["huestimate"] == 1).astype(int)
        elif "huestimate_x" in inventory.columns:
            inventory = PopulationDislocationUtil.compare_columns(
                inventory, "huestimate_x", "huestimate_y", True
            )
            if "huestimate_x-huestimate_y" in inventory.columns:
                exit("Column huestimate is ambiguous, check the input datasets!")
            else:
                inventory["d_sf"] = (inventory["huestimate"] == 1).astype(int)

        # drop d_sf_x, d_sf_y if they exist
        if "d_sf_x" in inventory.columns:
            inventory = inventory.drop(columns=["d_sf_x"])
        if "d_sf_y" in inventory.columns:
            inventory = inventory.drop(columns=["d_sf_y"])
        dsf = inventory["d_sf"].values
        pbd = inventory["pblackbg"].values
        phd = inventory["phispbg"].values

        prob0 = inventory["DS_0"].values
        prob1 = inventory["DS_1"].values
        prob2 = inventory["DS_2"].values
        prob3 = inventory["DS_3"].values

        # include random value loss by damage state
        rploss0 = PopulationDislocationUtil.get_random_loss(
            seed_i, value_loss, "DS_0", dsf.size
        )
        rploss1 = PopulationDislocationUtil.get_random_loss(
            seed_i, value_loss, "DS_1", dsf.size
        )
        rploss2 = PopulationDislocationUtil.get_random_loss(
            seed_i, value_loss, "DS_2", dsf.size
        )
        rploss3 = PopulationDislocationUtil.get_random_loss(
            seed_i, value_loss, "DS_3", dsf.size
        )

        inventory["rploss_0"] = rploss0
        inventory["rploss_1"] = rploss1
        inventory["rploss_2"] = rploss2
        inventory["rploss_3"] = rploss3

        prob0_disl = PopulationDislocationUtil.get_disl_probability(
            rploss0, dsf, pbd, phd
        )
        prob1_disl = PopulationDislocationUtil.get_disl_probability(
            rploss1, dsf, pbd, phd
        )
        prob2_disl = PopulationDislocationUtil.get_disl_probability(
            rploss2, dsf, pbd, phd
        )
        prob3_disl = PopulationDislocationUtil.get_disl_probability(
            rploss3, dsf, pbd, phd
        )

        #  dislocation probability is 0 if the damage is set to 100% probability (insignificant, DS_0 = 1).
        #  DS_0 bulding does not distinguish between in and out hazard boundaries. All DS_0 = 1 are set to
        #  zero dislocation probability.
        prob0_disl = np.where(prob0 == 1, 0, prob0_disl)

        # total_prob_disl is the sum of the probability of dislocation at four damage states
        # times the probability of being in that damage state.
        total_prob_disl = (
            prob0_disl * prob0
            + prob1_disl * prob1
            + prob2_disl * prob2
            + prob3_disl * prob3
        )

        inventory["prdis"] = total_prob_disl

        # Randomly assign dislocation based on probability of dislocation
        random_generator = np.random.RandomState(seed_i)
        randomdis = random_generator.uniform(0, 1, total_prob_disl.size)

        # Probability of dislocation, a binary variable based on the logistic probability of dislocation.
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        # comparisons involving np.nan outputs False, supress RuntimeWarning above
        dislocated = np.less_equal(randomdis, total_prob_disl)

        inventory["dislocated"] = dislocated

        return inventory
