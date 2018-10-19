#!/usr/bin/env python3

"""Structure Damage
Assign the probability of building damage by either 1) merging the damage intervals from the hazard service
or by 2) calculating them from mean damage factors and standard deviation.

1) Assign, merge with the building inventory, the probability of building damage by calling fragility
service and hazard service. Probability of four damage states are returned from the hazard service based
on the hazard id and fragility mapping.
2) Probability of four damage states is used to determine probability of dislocation Value loss (damage).
It is based on Table 9 in Bai, Jong-Wha, Mary Beth D. Hueste, and Paolo Gardoni.
"Probabilistic assessment of structural damage due to earthquakes for buildings in Mid-America."
Journal of Structural Engineering 135.10 (2009): 1155-1163.
"""
import os
import numpy as np
import pandas as pd


class StructureDamage:
    """
    Assign the probability of building damage by calling fragility service and hazard service.
    Calculate the probability of building damage by calling the mean damage factors
    and standard deviation.
    """
    def __init__(self, output_file_path: str):
        """
            Args:
                output_file_path (str): Output file path.

            Returns:
        """
        # four building damage states
        self.damage_states = ["insignific", "moderate", "heavy", "complete"]

        self.output_file_path = output_file_path

    def merge_building_damage(self, building_inv_path: str, damage_probabilities: list):
        """Merge building damage probabilities with building inventory by guid .

            Args:
                building_inv_path (str): Path and filename. Building inventory file from
                    the probabilistic analysis.
                damage_probabilities: (list of Ordered dictionaries): Damage probabilities
                    from the actual hazard service

            Returns:
                output_file_name (str): String of file name
        """
        # Building inventory from hazard service (shape file)
        building_hazard = pd.DataFrame.from_records(damage_probabilities)

        # Building inventory from the csv file
        building_inv = pd.DataFrame()
        if os.path.isfile(building_inv_path):
            building_inv = pd.read_csv(building_inv_path, header="infer")

        sorted_hzd_0 = building_hazard.sort_values(by=["guid"])
        sorted_bld_0 = building_inv.sort_values(by=["guid"])
        if set(self.damage_states).issubset(sorted_bld_0.columns):
            sorted_bld_0 = sorted_bld_0.drop(columns=self.damage_states)

        merged_building_inv = pd.merge(sorted_bld_0, sorted_hzd_0,
                                       how="outer", on="guid",
                                       left_index=True, right_index=True,
                                       sort=True, copy=True, indicator=True,
                                       validate="1:1")

        merged_building_inv = merged_building_inv.drop(columns=["immocc", "lifesfty",
                                                                "collprev", "hazardtype",
                                                                "hazardval", "meandamage",
                                                                "mdamagedev", "_merge"])
        return merged_building_inv

    def calculate_building_damage(self, seed_i: int, building_inv_path: str):
        """Assign building damage in four states using numpy array ('all at once').

            Args:
                seed_i (int): seed for random normal to ensure replication
                building_inv_path (str): path to the building inventory set

            Returns:
                building_inv (pd.DataFrame):
        """
        # Building Inventory
        building_inv = pd.DataFrame()
        if os.path.isfile(building_inv_path):
            building_inv = pd.read_csv(building_inv_path, header="infer")

        size_row, size_col = building_inv.shape

        damage_factors = pd.DataFrame({"label": self.damage_states,
                                       "meandmgfactor": [0.005, 0.155, 0.555, 0.9],
                                       "stddmgfactor": [0.002, 0.058, 0.1, 0.04]})
        try:
            mean_damage_insig = float(damage_factors["meandmgfactor"][0])
            mean_damage_moder = float(damage_factors["meandmgfactor"][1])
            mean_damage_heavy = float(damage_factors["meandmgfactor"][2])
            mean_damage_compl = float(damage_factors["meandmgfactor"][3])
            std_damage_insig = float(damage_factors["stddmgfactor"][0])
            std_damage_moder = float(damage_factors["stddmgfactor"][1])
            std_damage_heavy = float(damage_factors["stddmgfactor"][2])
            std_damage_compl = float(damage_factors["stddmgfactor"][3])

            np.random.seed(seed_i)

            # Create np array with probability of loss based on the mean and standard deviation
            # of the damage factors and add it to the building inventory's pd.DataFrame.
            p_insig_loss = np.random.normal(mean_damage_insig, std_damage_insig, size_row)
            p_moder_loss = np.random.normal(mean_damage_moder, std_damage_moder, size_row)
            p_heavy_loss = np.random.normal(mean_damage_heavy, std_damage_heavy, size_row)
            p_compl_loss = np.random.normal(mean_damage_compl, std_damage_compl, size_row)

            # A[A==val1]=val2, A==val1 produces a boolean array that can be used as an index for A
            p_insig_loss[p_insig_loss < 0] = 0.0
            p_insig_loss[p_insig_loss > 1] = 1.0

            p_moder_loss[p_moder_loss < 0] = 0.0
            p_moder_loss[p_moder_loss > 1] = 1.0

            p_heavy_loss[p_heavy_loss < 0] = 0.0
            p_heavy_loss[p_heavy_loss > 1] = 1.0

            p_compl_loss[p_insig_loss < 0] = 0.0
            p_compl_loss[p_insig_loss > 1] = 1.0

            # sort by unique strctid key to get reproducible random
            # hazard assignment, for debugging mostly
            building_inv = building_inv.sort_values(by=["strctid"])

            decimal = 4
            building_inv["insignific"] = np.around(p_insig_loss, decimals=decimal)
            building_inv["moderate"] = np.around(p_moder_loss, decimals=decimal)
            building_inv["heavy"] = np.around(p_heavy_loss, decimals=decimal)
            building_inv["complete"] = np.around(p_compl_loss, decimals=decimal)

        except Exception as e:
            building_inv["insignific"] = np.nan
            building_inv["moderate"] = np.nan
            building_inv["heavy"] = np.nan
            building_inv["complete"] = np.nan
            # raise e

        return building_inv

    @staticmethod
    def set_value_loss(mean_damage: str, std_damage: str):
        """Calculate a value loss and compute the probability of dislocation for the household and population.

            Args:
                mean_damage (str):          Mean damage coefficient.
                std_damage (str):           Standard deviation of the mean damage.

            Returns:
                value_loss (float)          Value loss (building damage)
        """
        try:
            # Randomly assign probability of loss based on the mean and standard deviation of the damage factors.
            value_loss = np.random.normal(float(mean_damage), float(std_damage), None)
            if value_loss < 0:
                value_loss = 0.0
            elif value_loss > 1:
                value_loss = 1.0

        except Exception as e:
            # raise e
            value_loss = np.nan

        return value_loss

    def save_building_inventory(self, seed_i: int, building_inv: pd.DataFrame):
        """Save building inventory file as a csv.

            Args:
                self: for chaining
                seed_i (int):                   Seed, for random reproducibility.
                building_inv (pd.DataFrame):    Building inventory.

            Returns:

        """
        cols = ["strctid", "insignific", "moderate", "heavy", "complete"]
        building_inv = building_inv[cols]
        # building_inv = building_inv.sort_values(by=["insignific"], ascending=[True])

        output_filename = "building_inventory"
        if seed_i:
            building_inv.to_csv(self.output_file_path + output_filename + "_" + str(seed_i) + ".csv", sep=",")
        else:
            building_inv.to_csv(self.output_file_path + output_filename + ".csv", sep=",")
