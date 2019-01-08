#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np
from pyincore import BaseAnalysis


class StochasticPopulationAllocation(BaseAnalysis):
    def __init__(self, incore_client):
        super(StochasticPopulationAllocation, self).__init__(incore_client)

    def get_spec(self):
        return {
            'name': 'stochastic-population-allocation',
            'description': 'Stochastic Population Allocation Analysis',
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
                    'description': 'Initial Seed for the Stochastic model',
                    'type': int
                },
                {
                    'id': 'iterations',
                    'required': True,
                    'description': 'No of iterations to perform the stochastic model on',
                    'type': int
                }
            ],
            'input_datasets': [
                {
                    'id': 'population_inventory',
                    'required': True,
                    'description': 'Population Inventory CSV data, aka Census Block data. Corresponds to a possible '
                                   'occupied housing unit, vacant housing unit, or a group quarters',
                    'type': ['ergo:censusBlockPopulation']
                },
                {
                    'id': 'address_point_inventory',
                    'required': True,
                    'description': 'CSV dataset of address locations available in a block. Corresponds to a '
                                   'specific address where a housing unit or group quarters could be assigned',
                    'type': ['ergo:addressPoints']
                },
                {
                    'id': 'building_inventory',
                    'required': True,
                    'description': 'Building Inventory CSV dataset for each building/structure. A structure '
                                   'can have multiple addresses',
                    'type': ['ergo:buildingInventory']
                }
            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'population_block', #TODO: Is parent_type needed?
                    'description': 'A csv file with the merged dataset of the inputs, aka Stochastic'
                                   'Population Allocation',
                    'type': 'csv'
                }
            ]
        }

    def run(self):
        """Merges Population Inventory, Address Point Inventory and Building Inventory.
         The results of this analysis are aggregated per structure/building. Generates
         one csv result per iteration.

        Returns:
               bool: True if successful, False otherwise
        """

        # Get seed
        seed = self.get_parameter("seed")

        # Get Iterations
        iterations = self.get_parameter("iterations")

        # Get desired result name
        result_name = self.get_parameter("result_name")

        # Population Inventory Dataset
        pop_inv = self.get_input_dataset("population_inventory").get_dataframe_from_csv()

        # Address Point Inventory Dataset
        addr_point_inv = self.get_input_dataset("address_point_inventory").get_dataframe_from_csv()

        # Building Inventory dataset
        bg_inv = self.get_input_dataset("building_inventory").get_dataframe_from_csv()

        csv_source = "dataframe"

        for i in range(iterations):
            seed_i = seed + i
            sorted_population_address_inventory = self.get_iteration_stochastic_allocation(
                pop_inv, addr_point_inv, bg_inv, seed_i)
            temp_output_file = result_name + "_" + str(seed_i) + ".csv"

            self.set_result_csv_data("result", sorted_population_address_inventory, temp_output_file, csv_source)

        return True

    def prepare_population_inventory(self,population_inventory, seed):
        size_row, size_col = population_inventory.shape
        np.random.seed(seed)
        sorted_population0 = population_inventory.sort_values(by=["lvtypuntid"])

        # Create Random merge order for population inventory
        random_order_population = np.random.uniform(0, 1, size_row)

        sorted_population0["randomblock"] = random_order_population

        #  gsort BlockID -LiveTypeUnit Tenure randomaorderpop
        sorted_population1 = sorted_population0.sort_values(by=["blockid", "ownershp", "vacancy", "randomblock"],
                                                            ascending=[True, True, True, True])

        # by BlockID: gen RandomMergeOrder = _n
        sorted_population1["mergeorder"] = sorted_population1.groupby(["blockid"]).cumcount()

        sorted_population2 = sorted_population1.sort_values(by=["blockid", "mergeorder"],
                                                            ascending=[True, False])
        return sorted_population2

    def merge_infrastructure_inventory(self, address_point_inventory, building_inventory ):
        """Merge order to Building and Address inventories.

            Args:
                self: for chaining

            Returns:
                output (pd.DataFrame)
        """
        sorted_pnt_0 = address_point_inventory.sort_values(by=["strctid"])
        sorted_bld_0 = building_inventory.sort_values(by=["strctid"])

        addresspt_building_inv = pd.merge(sorted_bld_0, sorted_pnt_0,
                                          how='outer', on="strctid",
                                          left_index=False, right_index=False,
                                          sort=True, copy=True, indicator=True,
                                          validate="1:m")

        addresspt_building_inv = self.compare_merges(sorted_pnt_0.columns, sorted_bld_0.columns,
                                                     addresspt_building_inv)

        return addresspt_building_inv

    def prepare_infrastructure_inventory(self, seed_i: int, critical_bld_inv: pd.DataFrame):
        """Assign Random merge order to Building, Water and Address inventories. Use main
        seed value.

            Args:
                self: for chaining
                seed_i (int):              Seed for reproducibility
                critical_bld_inv (pd.DataFrame): merged inventories

            Returns:
                output (pd.DataFrame)
        """
        size_row, size_col = critical_bld_inv.shape

        sort_critical_bld_0 = critical_bld_inv.sort_values(by=["addrptid"])

        seed_i2: int = seed_i + 1
        np.random.seed(seed_i2)

        randomaparcel = np.random.uniform(0, 1, size_row)
        sort_critical_bld_0["randomaparcel"] = randomaparcel

        sort_critical_bld_1 = sort_critical_bld_0.sort_values(by=["blockid", "huestimate", "randomaparcel"],
                                                              ascending=[True, True, True])
        sort_critical_bld_1["mergeorder"] = sort_critical_bld_1.groupby(["blockid"]).cumcount()

        sort_critical_bld_2 = sort_critical_bld_1.sort_values(by=["blockid", "mergeorder"],
                                                              ascending=[True, False])
        return sort_critical_bld_2

    def merge_inventories(self, sorted_population: pd.DataFrame, sorted_infrastructure: pd.DataFrame):
        """Merge (Sorted) Population Inventory and (Sorted) Infrastrucutre Inventory.

            Args:
                self: for chaining
                sorted_population (pd.DataFrame):  Sorted population inventory
                sorted_infrastructure (pd.DataFrame):  Sorted infrastrucutre inventory. This includes
                    Building inventory, Address point inventory and Critical (Water) Infrastrucutre

            Returns:
                final_merge_inv (pd.DataFrame): final merge of all four inventories
        """
        population_address_point_inventory = pd.merge(sorted_infrastructure, sorted_population,
                                                      how='outer', left_on=["blockid", "mergeorder"],
                                                      right_on=["blockid", "mergeorder"],
                                                      sort=True, suffixes=("_x", "_y"),
                                                      copy=True, indicator="exists3", validate="1:1")

        # check for duplicate columns from merge
        population_address_point_inventory = self.compare_merges(sorted_population.columns,
                                                                 sorted_infrastructure.columns,
                                                                 population_address_point_inventory)

        sorted_population_address_inventory = population_address_point_inventory.sort_values(
            by=["lvtypuntid"])

        output = sorted_population_address_inventory[sorted_population_address_inventory["exists3"] == 'both']
        return output

    def get_iteration_stochastic_allocation(self, population_inventory, address_point_inventory, building_inventory, seed):
        sorted_population = self.prepare_population_inventory(population_inventory, seed)

        critical_building_inv = self.merge_infrastructure_inventory(address_point_inventory, building_inventory)
        sorted_infrastructure = self.prepare_infrastructure_inventory(seed, critical_building_inv)

        output = self.merge_inventories(sorted_population, sorted_infrastructure)
        return output

    # utility functions
    def compare_merges(self, table1_cols, table2_cols, table_merged):
        """Compare two lists of columns and run compare columns on columns in both lists.
        It assumes that suffixes are _x and _y

            Args:
                self:                       for chaining
                table1_cols (list):         columns in table 1
                table2_cols (list):         columns in table 2
                table_merged (pd.DataFrame):merged table

                Returns:
                    table_merged (pd.DataFrame)
        """
        match_column = set(table1_cols).intersection(table2_cols)
        for col in match_column:
            # Compare two columns and marked similarity or rename and drop
            if col+"_x" in table_merged.columns and col+"_y" in table_merged.columns:
                table_merged = self.compare_columns(table_merged, col+"_x", col+"_y", True)

        return table_merged

    def compare_columns(self, table, col1, col2, drop):
        """Compare two columns. If not equal create Tru/False column, if equal rename one of them
        with the base name and drop the other.

            Args:
                self:                      for chaining.
                table (pd.DataFrame):      Data Frame table
                col1 (pd.Series):          Column 1
                col2 (pd.Series):          Column 2
                drop (bool):               rename and drop column

            Returns:
                output (pd.DataFrame)
        """
        # Values in columns match or not, add True/False column
        table.loc[table[col1] == table[col2], col1+"-"+col2] = True
        table.loc[table[col1] != table[col2], col1+"-"+col2] = False

        if table[col1].equals(table[col2]):
            col1_base = col1.rsplit("_", 1)[0]
            col2_base = col1.rsplit("_", 1)[0]
            if col1_base == col2_base and drop:

                table[col1_base] = table[col1]
                table = table.drop(columns=[col1, col2, col1+"-"+col2])

        return table
