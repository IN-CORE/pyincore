from pyincore import InsecureIncoreClient, IncoreClient
from pyincore.analyses.roaddamage import RoadDamage
#from pyincore import Dataset

def run_with_base_class():
    #client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", "fredrick")
    client = IncoreClient()

    # EQ Road Dataset - Memphis road link with topology
    road_damage_id = "5d25118eb9219c0692cd7527"

    # Shelby County Earthquake
    hazard_type = "earthquake"
    hazard_id = "5ba8f379ec2309043520906f"

    # Road damage ratios
    #dmg_ratio_input = "/Users/mfrdrcks/roadfiles/Roadway_Damage_Ratios-input/converted/Roadway Damage Ratios.csv"
    #dmg_ratio_dataset = Dataset.from_file(dmg_ratio_input, "ergo:roadDamageRatios")
    # Road damage ratios does not have a dataset in the service yet
    dmg_ratio_id = "5d6599deb9219c070d1b1ff6"

    # Earthquake mapping
    mapping_id = "5d545b0bb9219c0689f1f3f4"

    liq_geology_dataset_id = "5a284f53c7d30d13bc08249c"

    uncertainty = False
    liquefaction = False

    # Run Memphis earthquake road damage
    road_dmg = RoadDamage(client)
    road_dmg.load_remote_input_dataset("roads", road_damage_id)
    #road_dmg.set_input_dataset("dmg_ratios", dmg_ratio_dataset)
    road_dmg.load_remote_input_dataset("dmg_ratios", dmg_ratio_id)

    result_name = "memphis_road_dmg_result"
    road_dmg.set_parameter("result_name", result_name)
    road_dmg.set_parameter("mapping_id", mapping_id)
    road_dmg.set_parameter("hazard_type", hazard_type)
    road_dmg.set_parameter("hazard_id", hazard_id)
    road_dmg.set_parameter("fragility_key", "pgd")
    road_dmg.set_parameter("num_cpu", 1)
    road_dmg.set_parameter("use_liquefaction", liquefaction)
    road_dmg.set_parameter("liquefaction_geology_dataset_id", liq_geology_dataset_id)
    road_dmg.set_parameter("use_hazard_uncertainty", uncertainty)

    # Run Analysis
    road_dmg.run_analysis()

if __name__ == '__main__':
    run_with_base_class()
