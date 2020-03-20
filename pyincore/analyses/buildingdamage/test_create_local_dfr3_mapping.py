from pyincore import DFR3CurveSet, MappingSet, Mapping, IncoreClient, PeriodStandardFragilityCurve
from pyincore.analyses.buildingdamage import BuildingDamage

"""
Structure:
DFR3Curve
DFR3CurveSet contains [DFR3Curve]
Mapping contains [{rules:[[...]], entry:{"fragility_key": DFR3CurveSet }]
MappingSet contains [ Mapping ]
"""

# 0. create DFR3Curve (if you want to do everything from the very very scratch)
fragility_curve_1_1 = PeriodStandardFragilityCurve({
    "description": "Moderate",
    "alpha":-0.453,
    "beta": 0.794,
    "alphaType":"lambda",
    "curveType":"LogNormal",
    "periodParam2":0,
    "periodParam1":0,
    "periodParam0":0.75,
    "periodEqnType":1
})
fragility_curve_1_2 = PeriodStandardFragilityCurve({
    "description": "Extensive",
    "alpha": 0.372,
    "beta": 0.794,
    "alphaType": "lambda",
    "curveType": "LogNormal",
    "periodParam2": 0,
    "periodParam1": 0,
    "periodParam0": 0.75,
    "periodEqnType": 1
})
fragility_curve_1_3 = PeriodStandardFragilityCurve({
    "description": "Complete",
    "alpha":1.198,
    "beta": 0.794,
    "alphaType":"lambda",
    "curveType":"LogNormal",
    "periodParam2":0,
    "periodParam1":0,
    "periodParam0":0.75,
    "periodEqnType":1
})
dfr3curveset_metadata_1 = {
    "id":"local_fragility_curve_set_1",
    "demandType": "PGA",
    "demandUnits": "g",
    "resultType":"Limit State",
    "hazardType":"earthquake",
    "inventoryType":"building",
    "fragilityCurves":[
        fragility_curve_1_1,
        fragility_curve_1_2,
        fragility_curve_1_3,
    ]
}
fragility_curve_set_1 = DFR3CurveSet(dfr3curveset_metadata_1)

# 1. Alternatively, you can create DFR3CurveSet objects directly from a json
fragility_curve_set_2 = DFR3CurveSet.from_json_file('5b47b34f337d4a3629076470.json')

# 2. then create Mapping objects and put DFR3CurveSet into them
entry_1 = {"Non-Retrofit Fragility ID Code": fragility_curve_set_1}
rules_1 = [[
    "int no_stories GE 4",
    "int no_stories LE 7"
]]
mapping_1 = Mapping(entry_1, rules_1)

entry_2 = {"Non-Retrofit Fragility ID Code": fragility_curve_set_2}
rules_2 = [["int no_stories GE 1", "int no_stories LE 3"]]
mapping_2 = Mapping(entry_2, rules_2)

# 3. last create Mapping object that put multiple mapping entries into them
mappingset_metadata = {
    'id': 'local placeholder',
    'name': 'testing local mapping object creation',
    'hazardType': 'earthquake',
    'inventoryType': 'building',
    'mappings': [
        mapping_1,
        mapping_2,
    ],
    'mappingType': 'fragility'
}
local_mapping_set = MappingSet(mappingset_metadata)

# connect to building damage analysis
client = IncoreClient()
bldg_dmg = BuildingDamage(client)
bldg_dmg.load_remote_input_dataset("buildings", '5a284f0bc7d30d13bc081a28')
bldg_dmg.set_parameter("result_name", 'local_mapping_fragility_memphis_eq_bldg_dmg_result')

# Load local dfr3 mapping from file
local_mapping = MappingSet.from_json_file('local_mapping.json')
bldg_dmg.set_input_dfr3_mapping_set(local_mapping)

# Load locally created dfr3 mapping
bldg_dmg.set_input_dfr3_mapping_set(local_mapping_set)

# Load remote dfr3 mapping
bldg_dmg.load_remote_dfr3_mapping("5b47b350337d4a3629076f2c")

bldg_dmg.set_parameter("hazard_type", 'earthquake')
bldg_dmg.set_parameter("hazard_id", '5b902cb273c3371e1236b36b')
bldg_dmg.set_parameter("num_cpu", 4)

# Run Analysis
bldg_dmg.run_analysis()