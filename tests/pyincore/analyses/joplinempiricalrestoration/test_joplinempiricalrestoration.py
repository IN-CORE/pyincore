#!/usr/bin/env python3

from pyincore import IncoreClient
from pyincore.analyses.joplinempiricalrestoration import JoplinEmpiricalRestoration
import pyincore.globals as pyglobals

def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # incore-dev
    building_dmg = "602d96e4b1db9c28aeeebdce"  # dev Joplin
    # Funcionality level dataset
    # func_level_id = ""

    restoration = JoplinEmpiricalRestoration(client)
    restoration.load_remote_input_dataset("building_dmg", building_dmg)
    # restoration.load_remote_input_dataset("functionality_level", func_level_id)

    result_name = "Joplin_empirical_restoration_result"
    restoration.set_parameter("result_name", result_name)
    restoration.set_parameter("target_functionality_level", 0)
    restoration.set_parameter("seed", 1234)

    # Run Analysis
    restoration.run_analysis()


if __name__ == '__main__':
    run_with_base_class()