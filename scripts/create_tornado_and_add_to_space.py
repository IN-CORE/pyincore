#!/usr/bin/env python
# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
#
# Script: Create a dataset-driven tornado and add it to the "incore" space.
# Adds both the hazard id and the hazard dataset id(s) as space members.
#
# Usage:
#   python create_tornado_and_add_to_space.py
#
# Prerequisites:
#   - IN-CORE credentials (e.g. INCORE_USER, INCORE_PASSWORD or .incore credentials)
#   - Local tornado shapefile files (paths set in TORNADO_FILE_PATHS below)

import json
import os

from pyincore import IncoreClient, HazardService, SpaceService


# Dataset-driven tornado definition (see IN-CORE workshop session 2)
# https://tools.in-core.org/doc/incore/workshops/20231115/session2/session2-remote-and-local-hazards.html#creating-a-dataset-driven-tornado
TORNADO_DATASET_JSON = {
    "name": "Joplin Dataset Tornado - script",
    "description": "Joplin tornado hazard with shapefile",
    "tornadoType": "dataset",
}

# Paths to tornado shapefile components (adjust to your local paths).
# Workshop example: data/hazard/tornado/joplin_path_wgs84.{shp,dbf,prj,shx}
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "tests", "data", "joplin_tornado")
TORNADO_FILE_PATHS = [
    os.path.join(DATA_DIR, "joplin_path_wgs84.shp"),
    os.path.join(DATA_DIR, "joplin_path_wgs84.dbf"),
    os.path.join(DATA_DIR, "joplin_path_wgs84.prj"),
    os.path.join(DATA_DIR, "joplin_path_wgs84.shx"),
]

SPACE_NAME = "incore"
URL = "https://dev.in-core.org"


def create_tornado_and_add_to_space(
    tornado_json_dict=None,
    file_paths=None,
    space_name=SPACE_NAME,
):
    """
    Create a dataset-driven tornado and add the hazard id and hazard dataset
    id(s) to the given space by name.

    Args:
        tornado_json_dict (dict): Tornado definition (name, description, tornadoType).
            Defaults to TORNADO_DATASET_JSON.
        file_paths (list): Paths to shapefile components. Defaults to TORNADO_FILE_PATHS.
        space_name (str): Name of the space to add the tornado to. Default "incore".

    Returns:
        dict: Created tornado response (with "id", and possibly "hazardDatasets").
    """
    tornado_json_dict = tornado_json_dict or TORNADO_DATASET_JSON
    file_paths = file_paths or TORNADO_FILE_PATHS

    # Resolve paths that exist (skip missing for flexible running)
    existing_paths = [p for p in file_paths if os.path.isfile(p)]
    if not existing_paths and file_paths:
        raise FileNotFoundError(
            f"No tornado files found. Tried: {file_paths}. "
            "Adjust DATA_DIR or TORNADO_FILE_PATHS."
        )

    client = IncoreClient(URL)
    hazardsvc = HazardService(client)
    spacesvc = SpaceService(client)

    # 1. Create the dataset-driven tornado
    tornado_json = json.dumps(tornado_json_dict, indent=4)
    print("Creating tornado scenario...")
    create_response = hazardsvc.create_tornado_scenario(tornado_json, existing_paths)
    hazard_id = create_response["id"]
    print(f"Created tornado hazard id: {hazard_id}")

    # 2. Get full metadata to obtain hazard dataset id(s) (datasetId in hazardDatasets)
    metadata = hazardsvc.get_tornado_hazard_metadata(hazard_id)
    dataset_ids_to_add = []

    if "hazardDatasets" in metadata:
        for hd in metadata["hazardDatasets"]:
            if hd.get("datasetId"):
                dataset_ids_to_add.append(hd["datasetId"])
    if not dataset_ids_to_add:
        print(
            "No hazardDatasets[].datasetId in metadata; adding only hazard id to space."
        )

    # 3. Resolve space id by name
    spaces = spacesvc.get_space_by_name(space_name)
    if not spaces:
        raise ValueError(f"Space not found: {space_name}")
    space_id = spaces[0]["id"]
    print(f"Target space: {space_name} (id={space_id})")

    # 4. Add hazard id to space
    try:
        spacesvc.add_dataset_to_space(space_id=space_id, dataset_id=hazard_id)
        print(f"Added hazard id to space: {hazard_id}")
    except Exception as e:
        print(
            f"Note: adding hazard id to space failed (may expect only dataset ids): {e}"
        )

    # 5. Add each hazard dataset id to space
    for ds_id in dataset_ids_to_add:
        try:
            spacesvc.add_dataset_to_space(space_id=space_id, dataset_id=ds_id)
            print(f"Added hazard dataset id to space: {ds_id}")
        except Exception as e:
            print(f"Failed to add dataset {ds_id}: {e}")

    return create_response


if __name__ == "__main__":
    create_tornado_and_add_to_space()
