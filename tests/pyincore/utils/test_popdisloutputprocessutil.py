# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import IncoreClient, DataService, SpaceService
from pyincore.analyses.populationdislocation import PopulationDislocation
import pyincore.globals as pyglobals
from pyincore import PopdislOutputProcessUtil


def run_with_base_class():

    # run population dislocation first
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # Joplin population dislocation
    building_dmg = "602d96e4b1db9c28aeeebdce"  # dev Joplin
    housing_unit_alloc = "5df7c989425e0b00092c5eb4"  # dev Joplin
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

    #######################################################
    # get result
    pop_dislocation_result = pop_dis.get_output_dataset("result")
    filename = PopdislOutputProcessUtil.get_heatmap_shp(pop_dislocation_result, filter_on=True,
                                                        filename="joplin-pop-disl-numprec.shp")

    # upload to incore services and put under commresilience space
    datasvc = DataService(client)
    dataset_prop = {
        "title": "Joplin Population Dislocation For Heatmap Plotting",
        "description": "only contain dislocated numprec for joplin playbook plotting usage",
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


if __name__ == '__main__':
    run_with_base_class()
