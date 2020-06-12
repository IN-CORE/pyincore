# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from pyincore import IncoreClient, InventoryDataset
from pyincore.analyses.bridgedamage import BridgeDamage
import traceback
import os

if __name__ == '__main__':
    cred = None
    try:
        with open("/home/cnavarro/git/pyincore/tests/.incorepw", 'r') as f:
            cred = f.read().splitlines()

        client = IncoreClient()

        # local hazard
        hazard_service = "earthquake/5b89921560a0286995e2882d"

        # incore service hazard
        # hazard_service = "earthquake/5b902cb273c3371e1236b36b"

        # Path to bridge data
        bridge_file_path = '/home/cnavarro/git/pyincore/pyincore/analyses/bridgedamage/data/'
        # Path to damage ratio data
        dmg_ratio_dir = '/home/cnavarro/git/pyincore/pyincore/analyses/bridgedamage/data/dmgratio'
        use_hazard_uncertainty = False
        use_liquefaction = False
        output_file_name = "bridge-damage-analysis-results.csv"

        # Default Bridge Fragility Mapping on incore-service
        mapping_id = "5b47bcce337d4a37755e0cb2"

        # Locate the shapefile
        for file in os.listdir(bridge_file_path):
            if file.endswith(".shp"):
                shp_file = os.path.join(bridge_file_path, file)

        # Create an inventory dataset
        bridges = InventoryDataset(os.path.abspath(shp_file))

        # Create bridge damage
        bridge_dmg = BridgeDamage(client, dmg_ratio_dir, hazard_service, output_file_name)

        bridge_dmg.get_damage(bridges.inventory_set, mapping_id, use_liquefaction, use_hazard_uncertainty)

    except EnvironmentError:
        print("exception")
        traceback.print_exc()