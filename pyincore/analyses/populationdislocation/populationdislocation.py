#!/usr/bin/env python3

"""Population Dislocation Analysis
This analysis computes the approximate dislocation for each residential structure based on the direct
economic damage. The results of this analysis are aggregated to the block group level.

The dislocation is calculated from four probabilites of dislocation based on a random normal
distribution of the four damage factors presented by Bai, Hueste, Gardoni 2009.

These four damage factors correspond to value loss. The sum of the four probabilities multiplied
by the four probabilities of damage states was used as the probability for dislocation.

This is different from Lin 2008
http://hrrc.arch.tamu.edu/publications/research%20reports/08-05R%20Dislocation%20Algorithm%203.pdf
which calculates a value loss which is the sum of the four damage factors times the four probabilities
of damage. The two approaches produce different results.

Usage:
    populationdislocation.py

Options:

"""
import os
import numpy as np
import pandas as pd
import datetime
import warnings
from pyincore import BaseAnalysis
from pyincore.analyses.populationdislocation.populationdislocationutil import PopulationDislocationUtil

class PopulationDislocation(BaseAnalysis):
    """Main Population dislocation class.
    """

    #TODO: Can we get rid of output_file_path and assume user wants to save in
    # the analysis location. Consistent with other analyses.
    def __init__(self, incore_client, output_file_path: str):
        """Constructor.

            Args:
                client:                     Used for Service (such as Hazard) Authentication.
                output_file_path (str):     Path to the output file.

            Returns:
        """
        # coefficients for the Logistic Regression Method
        self.coefficient = {"beta0": -0.42523,  # contstant
                            "beta1": 0.02480,   # percent
                            "beta2": -0.50166,  # single Family
                            "beta3": -0.01826,  # percent black block group
                            "beta4": -0.01198   # percent hispanic block group
                            }
        self.output_file_path = output_file_path

        super(PopulationDislocation, self).__init__(incore_client)


    def get_spec(self):
        return {
            'name': 'population-dislocation',
            'description': 'Population Dislocation Analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': False,
                    'description': 'Result CSV dataset name',
                    'type': str
                },
                {
                    'id': 'seed',
                    'required': True,
                    'description': 'Seed from the Stochastic Population Allocation',
                    'type': int
                }
            ],
            'input_datasets': [
                {
                    'id': 'building_dmg',
                    'required': True,
                    'description': 'Building damage results CSV file from hazard service',
                    'type': ['ergo:buildingDamageVer4']
                },
                {
                    'id': 'population_allocation',
                    'required': True,
                    'description': 'Stochastic Population Allocation CSV data',
                    'type': ['ergo:PopAllocation']
                },
                {
                    'id': 'block_group_data',
                    'required': True,
                    'description': 'Block group racial distribution census CSV data',
                    'type': ['ergo:blockGroupData']
                }
            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'population_block',
                    'description': 'A csv file with population dislocation result '
                                   'aggregated to the block group level',
                    'type': 'csv'
                }
            ]
        }

    def run(self):
        """Computes the approximate dislocation for each residential structure based on the direct
        economic damage. The results of this analysis are aggregated to the block group level

        Returns:
            bool: True if successful, False otherwise
        """
        # Get seed
        seed_i = self.get_parameter("seed")

        # Get desired result name
        result_name = self.get_parameter("result_name")

        #Building Damage Dataset
        building_dmg = self.get_input_dataset("building_dmg").get_file_path('csv')

        #Population Allocation Dataset
        sto_pop_alloc = self.get_input_dataset("population_allocation").get_file_path('csv')

        #Block Group data
        bg_data = self.get_input_dataset("block_group_data").get_file_path('csv')

        merged_block_inv = PopulationDislocationUtil.merge_damage_population_block(
            building_dmg, sto_pop_alloc, bg_data
        )

        #Returns dataframe
        merged_final_inv = self.get_dislocation(seed_i, merged_block_inv)

        csv_source = "dataframe"
        self.set_result_csv_data("result", merged_final_inv, result_name, csv_source)

        return True


    # coefficients setter
    def set_coefficients(self, coefficient: dict):
            self.coefficient = coefficient

    @staticmethod
    def get_output_metadata():
        output = {"dataType": "", "format": "table"}

        return output

    @staticmethod
    def set_provenance(author: str, filename: str, source: str):
        """ From STATA model
        What is the output file name? What program is needed to replicate results?
        """
        now = datetime.datetime.now()
        provenance = "Provenance: " + filename + now.isoformat()

        return provenance

    @staticmethod
    def merge_bld_inventory(merged_inventory: pd.DataFrame, building_inv: pd.DataFrame):
        """Merge Stochastic inventory and new building inventory.

            Args:
                merged_inventory (pd.DataFrame):  Stochastich inventory which includes Building inventory
                    (no or not updated hazard), Address point inventory and Critical (Water) Infrastrucutre,
                    Population inventory and Block data
                building_inv (pd.DataFrame):   New building inventory with probability of damage.

            Returns:
                sorted_fin_inv (pd.DataFrame): Sorted final merge
        """
        sorted_mrg = merged_inventory.sort_values(by=["strctid"])
        sorted_bld = building_inv.sort_values(by=["strctid"])

        final_inv = pd.merge(sorted_mrg, sorted_bld[["strctid", "insignific", "moderate", "heavy", "complete"]],
                             how="outer", on="strctid", left_index=False, right_index=False,
                             sort=True, copy=True, indicator=True,
                             validate="m:1")

        sorted_fin_inv = final_inv.sort_values(by=["lvtypuntid"])
        return sorted_fin_inv

    @staticmethod
    def merge_block_data(inventory_data: pd.DataFrame, block_data_path: str):
        """Merge a master dataset with block group data, a distribution of hispanic
        and black population based on the building id.

            Args:
                inventory_data (pd.DataFrame):  Merged inventory file.
                block_data_path (str):          Path and filename. Block data file, a distribution
                                                of hispanic and black population.

            Returns: merged_table(pd.DataFrame)
        """
        block_group_data = pd.DataFrame()
        if os.path.isfile(block_data_path) and block_data_path.endswith(".csv"):
            block_group_data = pd.read_csv(block_data_path, header="infer")

        merged_table = pd.DataFrame()
        # make a new column bgid which extracts the first 12 digits of column blockid
        try:
            inventory_data["bgid"] = inventory_data["blockid"].astype(str)
            inventory_data["bgid"] = inventory_data["bgid"].str[0:12].astype(int)

            # outer merge on bgid
            merged_table = pd.merge(inventory_data, block_group_data,
                                    how="outer",
                                    on="bgid",
                                    copy=True,
                                    validate="m:1")
        except Exception as e:
            print()
            # raise e

        return merged_table

    @staticmethod
    def get_block_data_value(building_inventory, block_data_path: str):
        """Get values for minorities from block group data, a distribution of hispanic
        and black population.

            Args:
                building_inventory:     Building inventory file.
                block_data_path (str):  Path and filename. Block data file.

            Returns: values (dict)
        """
        block_group_data = pd.DataFrame()
        if os.path.isfile(block_data_path) and block_data_path.endswith(".csv"):
            block_group_data = pd.read_csv(block_data_path, header="infer")

        values = []
        for building in building_inventory:
            for group in block_group_data:
                if building["blockid"].str[0:12] in group.values():
                    block_id = building["blockid"]
                    building_id = group["bgid"]
                    percent_hisp_data = group["phispbg"]
                    percent_black_data = group["pblackbg"]

                    values[block_id] = (building_id, percent_black_data, percent_hisp_data)

        return values

    def get_dislocation(self, seed_i: int, inventory: pd.DataFrame):
        """Calculate dislocation probability.

        Probability of dislocation, a binary variable based on the logistic probability of dislocation.
        A random number between 0 and 1 was assigned to each household.
        If the random number was less than the probability of dislocation
        then the household was determined to dislocate. This follows the logic
        that households with a greater chance of dislocated were more likely
        to have a random number less than the probability predicted.

            Args:
                self: for chaining
                seed_i (int): seed for random normal to ensure replication
                inventory (pd.DataFrame): final merged inventory

            Returns:
                inventory (pd.DataFrame)
        """
        # pd.Series to np.array
        dsf = inventory["d_sf"].values
        pbd = inventory["pblackbg"].values
        phd = inventory["phispbg"].values

        prob_ins = inventory["insignific"].values
        prob_mod = inventory["moderate"].values
        prob_hvy = inventory["heavy"].values
        prob_cmp = inventory["complete"].values

        prob_disl_ins = self.get_disl_probability(prob_ins, dsf, pbd, phd)
        prob_disl_mod = self.get_disl_probability(prob_mod, dsf, pbd, phd)
        prob_disl_hvy = self.get_disl_probability(prob_hvy, dsf, pbd, phd)
        prob_disl_cmp = self.get_disl_probability(prob_cmp, dsf, pbd, phd)

        # total_prob_disl is the sum of the probability of dislocation at four damage states
        # times the probability of being in that damage state.
        total_prob_disl = prob_disl_ins * prob_ins + prob_disl_mod * prob_mod + prob_disl_hvy * prob_hvy + \
            prob_disl_cmp * prob_cmp

        inventory["prdis"] = total_prob_disl

        # Randomly assign dislocation based on probability of dislocation
        np.random.seed(seed_i)
        randomdis = np.random.uniform(0, 1, total_prob_disl.size)

        # Probability of dislocation, a binary variable based on the logistic probability of dislocation.
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        # comparisons involving np.nan outputs False, supress RuntimeWarning above
        dislocated = np.less_equal(randomdis, total_prob_disl)

        inventory["dislocated"] = dislocated

        return inventory

    def aggregate_disl_value(self, seed_i: int, inventory: pd.DataFrame):
        """Calculate dislocation probability

            Args:
                self: for chaining
                seed_i (int): seed for random normal to ensure replication
                inventory (pd.DataFrame): final merged inventory

            Returns:
                values (dict): Total dislocation probabilities
        """
        # total dislocation
        # numprec: Number of persons in Structure from the popinventory
        noperson = inventory["numprec"].values
        ownership = inventory["ownershp"].values
        # non-missing values True, missing False.
        dislocated = inventory["dislocated"].values

        # generate total number of persons dislocated
        numprec = noperson
        disnumprec = numprec * dislocated

        numprec = np.sum(numprec)
        totdisnumprec = np.sum(disnumprec)

        # generate number of persons dislocated by tenure
        # water infrastructure exists
        infrastructure = inventory["wtrdnd1"].notna()
        # ownershp == 1
        numprecown = noperson * (ownership == 1) * (infrastructure == True)
        disnumprecown = numprecown * dislocated

        numprecown = np.sum(numprecown)
        totdisnumprecown = np.sum(disnumprecown)

        # ownershp == 2:
        numprecrent = noperson * (ownership == 2) * (infrastructure == True)
        disnumprecrent = numprecrent * dislocated

        numprecrent = np.sum(numprecrent)
        totdisnumprecrent = np.sum(disnumprecrent)

        # generate number of persons missing infrastructure data by tenure
        # water infrastructure does not exist
        noinfrastructure = inventory["wtrdnd1"].isna()
        # ownershp == 1
        numprecowninf = noperson * (ownership == 1) * (noinfrastructure == True)
        disnumprecowninf = numprecowninf * dislocated

        numprecowninf = np.sum(numprecowninf)
        disnumprecowninf = np.sum(disnumprecowninf)

        # ownershp == 2:
        numprecrentinf = noperson * (ownership == 2) * (noinfrastructure == True)
        disnumprecrentinf = numprecrentinf * dislocated

        numprecrentinf = np.sum(numprecrentinf)
        disnumprecrentinf = np.sum(disnumprecrentinf)

        mc_out_iter = [seed_i,
                       numprec, totdisnumprec,
                       numprecown, totdisnumprecown,
                       numprecrent, totdisnumprecrent,
                       numprecowninf, disnumprecowninf,
                       numprecrentinf, disnumprecrentinf]

        return mc_out_iter

    def get_disl_probability(self, value_loss: np.array, d_sf: np.array,
                             percent_black_bg: np.array, percent_hisp_bg: np.array):
        """
        Calculate dislocation, the probability of dislocation for the household and population.
        Probability of dislocation Damage Factor,
        based on current IN-COREv1 algorithm and Bai et al 2009 damage factors

        The following variables are need to predict dislocation using logistic model
        see detailed explanation https://opensource.ncsa.illinois.edu/confluence/
        display/INCORE1/Household+and+Population+Dislocation?
        preview=%2F66224473%2F68289561%2FAlgorithm+3+Logistic.pdf

            Args:
                self:                           for chaining
                value_loss (np.array):          Value loss.
                d_sf (np.array):                'Dummy' parameter.
                percent_black_bg (np.array):    Block group data, percentage of black minority.
                percent_hisp_bg (np.array):     Block group data, percentage of hispanic minority.

            Returns:
                disl_prob (np.array)               Dislocation probability
        """
        disl_prob = np.zeros_like(d_sf)
        try:
            disl_prob = 1.0 / (1 + np.exp(-1.0 * (self.coefficient["beta0"] * 1 +
                                                  self.coefficient["beta1"] * (value_loss * 100) +
                                                  self.coefficient["beta2"] * d_sf +
                                                  self.coefficient["beta3"] * percent_black_bg +
                                                  self.coefficient["beta4"] * percent_hisp_bg)))
        except Exception as e:
            print()
            # raise e

        return disl_prob

    def get_disl_probability_val(self, value_loss: float, d_sf: int,
                                 percent_black_bg: float, percent_hisp_bg: float):
        """Calculate dislocation, for a single value

            Args:
                self:                       for chaining
                value_loss (float):         Value loss.
                d_sf (int):                 'Dummy' parameter.
                percent_black_bg (float):   Block group data, percentage of black minority.
                percent_hisp_bg (float):    Block group data, percentage of hispanic minority.

            Returns:
                disl_prob (float)               Dislocation probability
        """
        disl_prob = np.nan
        try:
            disl_prob = 1.0 / (1 + np.exp(-1.0 * (self.coefficient["beta0"] * 1 +
                                                  self.coefficient["beta1"] * (float(value_loss) * 100) +
                                                  self.coefficient["beta2"] * float(d_sf) +
                                                  self.coefficient["beta3"] * float(percent_black_bg) +
                                                  self.coefficient["beta4"] * float(percent_hisp_bg))))
        except Exception as e:
            print()
            # raise e

        return disl_prob
