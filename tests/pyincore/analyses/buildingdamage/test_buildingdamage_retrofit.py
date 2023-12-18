import os

from pyincore import IncoreClient, MappingSet, Tornado, Dataset, HazardService
from pyincore.analyses.buildingdamage import BuildingDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient()
    hazardsvc = HazardService(client)

    # dfr3 mapping
    fragility_mapping_set_definition = {
        "id": "N/A",
        "name": "local joplin tornado fragility mapping object",
        "hazardType": "tornado",
        "inventoryType": "building",
        'retrofitDefinitions': [
            {
                "name": "retrofit_method",
                "description": "Retrofitting strategies to enhance residential wood-frame buildings from high "
                               "wind-related hazards, such as tornadoes, hurricanes",
                "PaperReference": {
                    "name": "Restoration and functionality assessment of a community subjected to tornado hazard",
                    "doi": "10.1080/15732479.2017.1354030",
                    "yearPublished": "2018"
                },
                "unit": None,
                "type": "string",
                "allowedValues": ["1", "2", "3"],
                "allowedNames": [
                    "roof covering with asphalt shingles, and roof sheathing with 8d C6/12, and roof-to-wall "
                    "connection type with two 16d toe nails",
                    "roof covering with asphalt shingles, and roof sheathing with 8d C6/6, and roof-to-wall "
                    "connection  type with two H2.5 clips",
                    "roof covering with clay tiles, and roof sheathing with 8d C6/6, and roof-to-wall connection type "
                    "with two H2.5 clips"
                ]
            }
        ],
        'mappings': [
            {
                "legacyEntry": {},
                "entry": {
                    "Non-Retrofit Fragility ID Code": "5e4ca22b9578290001e59005",
                },
                "rules": {
                    "AND": [
                        "int archetype EQUALS 1",
                    ]
                }
            },
            {
                "legacyEntry": {},
                "entry": {
                    "retrofit_method": "5e4ca29e1eb25200014abc29",
                },
                "rules": {
                    "AND": [
                        "int archetype EQUALS 1",
                        "str retrofit_method EQUALS '1'"
                    ]
                }
            },
            {
                "legacyEntry": {},
                "entry": {
                    "retrofit_method": "5e4ca2f51eb25200014abc9d",
                },
                "rules": {
                    "AND": [
                        "int archetype EQUALS 1",
                        "str retrofit_method EQUALS '2'"
                    ]
                }
            },
        ],
        "mappingType": "fragility"
    }

    fragility_mapping_set = MappingSet(fragility_mapping_set_definition)

    # Building Damage
    # Create building damage
    bldg_dmg = BuildingDamage(client)

    # Load input dataset
    bldg_dataset_id = "5dbc8478b9219c06dd242c0d"  # joplin building v6 prod
    bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)
    retrofit_strategy_plan1 = Dataset.from_file(os.path.join(pyglobals.TEST_DATA_DIR, "retrofit/retrofit_plan1.csv"),
                                                data_type="incore:retrofitStrategy")
    bldg_dmg.set_input_dataset("retrofit_strategy", retrofit_strategy_plan1)

    tornado = Tornado.from_hazard_service("608c5b17150b5e17064030df", hazardsvc)
    bldg_dmg.set_input_hazard("hazard", tornado)

    # Load fragility mapping
    bldg_dmg.set_input_dataset("dfr3_mapping_set", fragility_mapping_set)

    # Set hazard
    bldg_dmg.set_input_hazard("hazard", tornado)

    # Set analysis parameters
    result_folder = "retrofit"
    if not os.path.exists(result_folder):
        os.mkdir(result_folder)
    result_name = os.path.join(result_folder, "joplin_tornado_commerical_bldg_dmg_retrofitted")
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("num_cpu", 2)
    bldg_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
