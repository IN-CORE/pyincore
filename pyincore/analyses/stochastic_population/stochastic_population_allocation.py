import os
import pandas as pd
import random
import numpy as np


class StochasticPopulationAllocation:
    def __init__(self, address_point_inventory, building_inventory, critical_infrastructure_inventory,
                 population_inventory, output_name, output_directory, seed, iterations, intermediate_files):
        self.output_name = output_name
        self.output_directory = output_directory
        self.seed = seed
        self.iterations = iterations
        self.intermediate_files = intermediate_files
        if os.path.isfile(address_point_inventory):
            self.address_point_inventory = self.load_csv_file(address_point_inventory)

        if os.path.isfile(building_inventory):
            self.building_inventory = self.load_csv_file(building_inventory)

        if os.path.isfile(critical_infrastructure_inventory):
            self.critical_infrastructure_inventory = self.load_csv_file(critical_infrastructure_inventory)

        if os.path.isfile(population_inventory):
            self.population_inventory = self.load_csv_file(population_inventory)

    def prepare_population_inventory(self, seed):
        random.seed(seed)
        sorted_population0 = self.population_inventory.sort_values(by=['Live Type Unit ID'])

        # Create Random merge order for population inventory
        n = len(self.population_inventory)
        random_order_population = random.sample(range(n), n)
        sorted_population0['Random Order Population'] = random_order_population

        #  gsort BlockID -LiveTypeUnit Tenure randomaorderpop
        sorted_population1 = sorted_population0.sort_values(by=['Block ID', 'Live Type Unit ID', 'Tenure',
                                                                'Random Order Population'],
                                                            ascending=[True, False, True, True])

        # by BlockID: gen RandomMergeOrder = _n
        sorted_population1['Random Merge Order'] = sorted_population1.groupby(['Block ID']).cumcount()

        sorted_population2 = sorted_population1.sort_values(by=['Block ID', 'Random Merge Order'],
                                                            ascending=[True, False])
        return sorted_population2

    def merge_inventories(self, seed, sorted_population, building_inventory):
        addresspt_building_inventory = pd.merge(building_inventory, self.address_point_inventory, how='outer',
                                                on="Structure ID", left_index=False, right_index=False, sort=True,
                                                suffixes=('_x', '_y'), copy=True, indicator=True,
                                                validate="one_to_many")
        # Merge Critical Infrastructure Inventory
        critical_building_inventory = pd.merge(self.critical_infrastructure_inventory, addresspt_building_inventory,
                                               how='outer', on="Structure ID", left_index=False, right_index=False,
                                               sort=True, suffixes=('_x', '_y'), copy=True, indicator='exists',
                                               validate="one_to_many")

        # Create Random Merge Order for Address Point Inventory
        critical_building_inventory['Block ID'] = critical_building_inventory['Block ID_x']
        # Match Block ID indicates if the block id from critical infrastructure inventory and address point building
        # inventory match or not
        critical_building_inventory.loc[critical_building_inventory['Block ID_x'] ==
                                        critical_building_inventory['Block ID_y'], 'Match Block ID'] = True
        critical_building_inventory.loc[critical_building_inventory['Block ID_x'] !=
                                        critical_building_inventory['Block ID_y'], 'Match Block ID'] = False

        critical_building_inventory_sorted0 = critical_building_inventory.sort_values(by=['Address Point ID'])

        seed_i2 = seed + 1
        random.seed(seed_i2)
        n2 = len(critical_building_inventory)
        random_order_address_point = random.sample(range(n2), n2)
        critical_building_inventory_sorted0["Random Order Address Point"] = random_order_address_point
        critical_building_inventory_sorted1 = critical_building_inventory_sorted0.sort_values(
            by=['Block ID', 'Housing Unit Estimate', 'Random Order Address Point'],
            ascending=[True, True, True]
        )

        critical_building_inventory_sorted1['Random Merge Order'] = critical_building_inventory_sorted1.groupby(
            ['Block ID']).cumcount()

        critical_building_inventory_sorted2 = critical_building_inventory_sorted1.sort_values(
            by=['Block ID', 'Random Merge Order'], ascending=[True, False]
        )

        # Merge population Inventory and Address Point Inventory
        population_address_point_inventory = pd.merge(critical_building_inventory_sorted2, sorted_population,
                                                      how='outer', left_on=['Block ID', 'Random Merge Order'],
                                                      right_on=['Block ID', 'Random Merge Order'],
                                                      sort=True, suffixes=('_x', '_y'),
                                                      copy=True, indicator='exists3', validate="one_to_one")

        sorted_population_address_inventory = population_address_point_inventory.sort_values(
            by=['Live Type Unit ID'])

        output = sorted_population_address_inventory[sorted_population_address_inventory['exists3'] == 'both']
        return output

    def get_iteration_stochastic_allocation(self, seed):
        sorted_population = self.prepare_population_inventory(seed)
        output = self.merge_inventories(seed, sorted_population, self.building_inventory)
        return output

    def get_stochastic_population_allocation(self):
        output_directory = self.output_directory
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        output = pd.DataFrame()
        unique_skeleton_ids = self.critical_infrastructure_inventory['Skeletonized Network Node ID 2'].unique()

        # Avoids error indicating that a DataFrame was updated in place.
        pd.options.mode.chained_assignment = None
        for i in range(self.iterations):
            seed_i = self.seed + i

            sorted_population_address_inventory = self.get_iteration_stochastic_allocation(seed_i)
            output_item = {"i": i, "seed_i": seed_i, "other": 0}

            for skeleton_id in unique_skeleton_ids:
                output_item[skeleton_id] = 0

            for idx, item in sorted_population_address_inventory.iterrows():

                if item['exists3'] == 'both':
                    skeleton_id = item['Skeletonized Network Node ID 2']
                    if np.isnan(skeleton_id):
                        skeleton_id = "other"
                    output_item[skeleton_id] += item["Number of Persons"]

            output = output.append(pd.Series(output_item, name=str(i)))
            if self.intermediate_files:
                temp_output_file = os.path.join(output_directory, self.output_name + "_" + str(seed_i) + ".csv")
                sorted_population_address_inventory.to_csv(temp_output_file, mode="w+", index=False)

            output_file = os.path.join(output_directory, self.output_name + ".csv")
            output.to_csv(output_file, mode="w+", index=False)
        return output

    @staticmethod
    def load_csv_file(file_name):
        read_file = pd.read_csv(file_name, header="infer")
        return read_file
