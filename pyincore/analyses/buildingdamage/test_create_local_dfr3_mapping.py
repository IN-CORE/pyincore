from pyincore import DFR3Curve, MappingEntry, Mapping, IncoreClient
from pyincore.analyses.buildingdamage import BuildingDamage

# 1. create DFR3curve objects
fragility_curve_1 = DFR3Curve.from_json_file('5b47b34f337d4a3629076470.json')
fragility_curve_2 = DFR3Curve.from_json_file('5b47b34f337d4a3629075de9.json')

# 2. then create MappingEntry objects and put DFR3curve into them
entry_1 = {"Non-Retrofit Fragility ID Code": fragility_curve_1}
rules_1 = [[
    "int no_stories GE 4",
    "int no_stories LE 7"
]]
mapping_entry_1 = MappingEntry(entry_1, rules_1)

entry_2 = {"Non-Retrofit Fragility ID Code": fragility_curve_2}
rules_2 = [["int no_stories GE 1", "int no_stories LE 3"]]
mapping_entry_2 = MappingEntry(entry_2, rules_2)

# 3. last create Mapping object that put multiple mapping entries into them
metadata = {
    'id': 'local placeholder',
    'name': 'testing local mapping object creation',
    'hazardType': 'earthquake',
    'inventoryType': 'building',
    'mappings': [
        mapping_entry_1,
        mapping_entry_2,
    ],
    'mappingType': 'fragility'
}
local_mapping_object = Mapping(metadata)

# connect to building damage analysis
client = IncoreClient()
bldg_dmg = BuildingDamage(client)
bldg_dmg.load_remote_input_dataset("buildings", '5a284f0bc7d30d13bc081a28')
bldg_dmg.set_parameter("result_name", 'memphis_eq_bldg_dmg_result')

# Load local dfr3 mapping from file
local_mapping = Mapping.from_json_file('local_mapping.json')
bldg_dmg.set_input_dfr3_mapping(local_mapping)

# Load locally created dfr3 mapping
bldg_dmg.set_input_dfr3_mapping(local_mapping_object)

# Load remote dfr3 mapping
bldg_dmg.load_remote_dfr3_mapping("5b47b350337d4a3629076f2c")

bldg_dmg.set_parameter("hazard_type", 'earthquake')
bldg_dmg.set_parameter("hazard_id", '5b902cb273c3371e1236b36b')
bldg_dmg.set_parameter("num_cpu", 4)

# Run Analysis
bldg_dmg.run_analysis()