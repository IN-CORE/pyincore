# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import PopDislOutputProcess
from pyincore import IncoreClient, DataService, SpaceService
from pyincore.analyses.populationdislocation import PopulationDislocation
import pyincore.globals as pyglobals
import os


def upload_shapefile_to_services(client):
    # Upload to incore services and put under commresilience space
    # It assumes the shapefile is in the utils directory
    datasvc = DataService(client)
    dataset_prop = {
        "title": "Joplin Population Dislocation For Heatmap Plotting",
        "description": "Contains only dislocated numprec for Joplin playbook plotting usage",
        "contributors": [],
        "dataType": "incore:popdislocationShp",
        "storedUrl": "",
        "format": "shapefile"
    }
    response = datasvc.create_dataset(dataset_prop)
    dataset_id = response['id']
    files = ['joplin-pop-disl-numprec.shp',
             'joplin-pop-disl-numprec.dbf',
             'joplin-pop-disl-numprec.shx',
             'joplin-pop-disl-numprec.prj']
    datasvc.add_files_to_dataset(dataset_id, files)

    # add to space
    spacesvc = SpaceService(client)
    spacesvc.add_dataset_to_space("5f99ba8b0ace240b22a82e00", dataset_id=dataset_id)  # commresilience
    print(dataset_id + " successfully uploaded and move to commresilience space!")


def run_convert_pd_json_chained(client):
    # Joplin population dislocation
    # incore-dev
    building_dmg = "602d96e4b1db9c28aeeebdce"  # dev Joplin
    # building_dmg = "602d975db1db9c28aeeebe35" # 15 guids test - dev Joplin
    housing_unit_alloc = "61563545483ecb19e4304c2a"  # dev Joplin 2ev3
    bg_data = "5df7cb0b425e0b00092c9464"  # Joplin 2ev2
    value_loss = "602d508fb1db9c28aeedb2a5"

    result_name = "joplin-pop-disl-results"
    seed = 1111

    pop_dis = PopulationDislocation(client)

    pop_dis.load_remote_input_dataset("building_dmg", building_dmg)
    pop_dis.load_remote_input_dataset("housing_unit_allocation", housing_unit_alloc)
    pop_dis.load_remote_input_dataset("block_group_data", bg_data)
    pop_dis.load_remote_input_dataset("value_poss_param", value_loss)

    pop_dis.set_parameter("result_name", result_name)
    pop_dis.set_parameter("seed", seed)

    pop_dis.run_analysis()
    pd_result = pop_dis.get_output_dataset("result")

    return pd_result


if __name__ == '__main__':
    # test chaining with population dislocation
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    pd_result = run_convert_pd_json_chained(client)

    pd_process = PopDislOutputProcess(pd_result)

    pd_process.pd_by_race("PD_by_race.json")
    pd_process.pd_by_income("PD_by_income.json")
    pd_process.pd_by_tenure("PD_by_tenure.json")
    pd_process.pd_by_housing("PD_by_housing.json")
    pd_process.pd_total("PD_by_total.json")

    filename = pd_process.get_heatmap_shp("joplin-pop-disl-numprec.shp")
    print("Test chaining", filename)
    # upload_shapefile_to_services(client)

    # test the external file with a path
    testpath = ""
    # testpath = "/Users/<user>/<path_to_pyincore>/pyincore/tests/pyincore/utils"
    if testpath:
        pd_process = PopDislOutputProcess(None, os.path.join(testpath, "joplin-pop-disl-results.csv"))

        pd_process.pd_by_race("PD_by_race.json")
        pd_process.pd_by_income("PD_by_income.json")
        pd_process.pd_by_tenure("PD_by_tenure.json")
        pd_process.pd_by_housing("PD_by_housing.json")
        pd_process.pd_total("PD_by_total.json")

        filename = pd_process.get_heatmap_shp("joplin-pop-disl-numprec.shp")
        print("Test path", filename)
    print("DONE")
