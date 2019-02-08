"""

Copyright (c) 2019 University of Illinois and others.  All rights reserved.
This program and the accompanying materials are made available under the
terms of the Mozilla Public License v2.0 which accompanies this distribution,
and is available at https://www.mozilla.org/en-US/MPL/2.0/

"""

import csv
import pandas as pd

from pyincore import GeoUtil, InventoryDataset


class TransportationRecoveryUtil:

    @staticmethod
    def NBI_coordinate_mapping(NBI_file):
        """
        coordinate in NBI is in format of xx(degree)xx(minutes)xx.xx(seconds)
        map it to traditional xx.xxxx in order to create shapefile
        :param NBI_file:
        :return:
        """
        NBI = pd.read_csv(NBI_file)
        NBI['LONG_017'] = NBI['LONG_017'].apply(lambda x: -1 *(GeoUtil.degree_to_decimal(x)))
        NBI['LAT_016'] = NBI['LAT_016'].apply(lambda x: GeoUtil.degree_to_decimal(x))

        return NBI

    @staticmethod
    def get_average_daily_traffic(bridges, NBI_shapefile):
        NBI = InventoryDataset(NBI_shapefile)
        NBI_features = list(NBI.inventory_set)

        ADT = {}
        for bridge in bridges:
            # convert lon and lat to the right format
            bridge_coord = GeoUtil.get_location(bridge)
            nearest_feature, distance = GeoUtil.find_nearest_feature(NBI_features, bridge_coord)

            ADT[bridge['properties']['guid']] = nearest_feature['properties']['ADT_029']

        return ADT

    @staticmethod
    def convert_dmg_prob2state(dmg_results_filename):
        """
        upstream bridge damage analysis will generate a dmg result file with the probability
        of each damage state; here determine what state using the maximum probability
        :param dmg_results_filename:
        :return: bridge_damage_value, unrepaired_bridge
        """

        bridge_damage_value = {}
        unrepaired_bridge = []

        with open(dmg_results_filename, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                id = row[0]
                mean_damage = float(row[10])

                if mean_damage > 0 and mean_damage < 0.25:
                    bridge_damage_value[id] = 1
                elif mean_damage >= 0.25 and mean_damage <0.5:
                    bridge_damage_value[id] = 2
                elif mean_damage >=0.5 and mean_damage <0.75:
                    bridge_damage_value[id] = 3
                elif mean_damage >=0.75 and mean_damage <=1:
                    bridge_damage_value[id] = 4
                else:
                    raise ValueError('mean damage should not larger than 1!')

            unrepaired_bridge = list(bridge_damage_value.keys())

        return bridge_damage_value, unrepaired_bridge

    @staticmethod
    def write_output(output, fname):
        """
        output the result
        :param output: the data set of output
        :param path: the relative path of output file
        :return: path and path length
        """

        # create Output folder if it does not exist
        output.to_csv(fname, index=False)
        print(fname + ' saved!')
        return None
