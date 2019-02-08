"""

Copyright (c) 2019 University of Illinois and others.  All rights reserved.
This program and the accompanying materials are made available under the
terms of the Mozilla Public License v2.0 which accompanies this distribution,
and is available at https://www.mozilla.org/en-US/MPL/2.0/

"""

# # Water Network Analysis

# In[1]:


import logging
import warnings
import pandas as pd
import json
import csv
from matplotlib import animation, rc
from IPython.display import HTML
from collections import OrderedDict

from pyincore import InsecureIncoreClient
from pyincore.analyses.waternetworkdamage import WaterNetworkDamage
from pyincore.analyses.waternetworkrecovery import WaterNetworkRecovery, WaterNetworkRecoveryUtil
from pyincore.analyses.stochasticpopulation import StochasticPopulationAllocation
from pyincore.analyses.populationdislocation import PopulationDislocation, PopulationDislocationUtil
from pyincore.analyses.buildingdamage import BuildingDamage
from pyincore import InventoryDataset, Dataset


# #### embed interactive graphs in the notebook

# In[2]:


from plotly.offline import init_notebook_mode
init_notebook_mode()


# #### supress warning and info logging

# In[3]:


warnings.filterwarnings('ignore')
logger = logging.getLogger()
logger.setLevel(logging.CRITICAL)


# #### set client

# In[4]:


client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", "incrtest")


# ## Preparation work
#  - extract and save demand node
#  - use QGIS to generate voronoi cell
#  - use QGIS to do clipping
#  - use QGIS to calculate the cell area (unit: acres)
#  - use that voronoi cell shapefile and building inventory, find the mapping relationship of those two

# In[5]:


pd.read_csv('cache_data/waternode_building_relations.csv')


# ### run stochastic allocation model 

# In[6]:


seed_i = 1111
addres_inv_path = "cache_data/IN-CORE_01av3_SetupSeaside_FourInventories_2018-08-29_addresspointinventory.csv"
blding_inv_path = "cache_data/IN-CORE_01av3_SetupSeaside_FourInventories_2018-08-29_buildinginventory.csv"
infras_inv_path = "cache_data/IN-CORE_01av3_SetupSeaside_FourInventories_2018-08-29_waterinventory.csv"
popula_inv_path = "cache_data/IN-CORE_01av3_SetupSeaside_FourInventories_2018-08-29_popinventory.csv"
intermediate_files = True
stal = StochasticPopulationAllocation(addres_inv_path, blding_inv_path,
                                     infras_inv_path, popula_inv_path,
                                     "pop_allocation", "./cache_data/",
                                     1111, 1,
                                     intermediate_files)
stal.get_stochastic_population_allocation()


# ### calculate inital water demand based on stochastic allocation model  $unit = m^3/s$

# In[7]:


waternode_population = WaterNetworkRecoveryUtil.calc_waternode_population('cache_data/waternode_building_relations.csv','cache_data/pop_allocation_1111.csv')
demand0 = WaterNetworkRecoveryUtil.calc_waternode_demand('cache_data/waternode_building_relations.csv', waternode_population)
with open('cache_data/demand0.json', 'w') as f:
    json.dump(demand0, f)


# ### calculate water demand after hazard based on population dislocation model  $unit = m^3/s$

# #### calculate building damage
# seaside building inventory
bldg_dataset_id = "5bcf2fcbf242fe047ce79dad"
hazard_type = "earthquake"
hazard_id = "5ba92505ec23090435209071"
dmg_ratio_id = "5a284f2ec7d30d13bc08209a"
mapping_id = "5b47b350337d4a3629076f2c"

# set parameters and dataset
bldg_dmg = BuildingDamage(client)
bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)
bldg_dmg.load_remote_input_dataset("dmg_ratios", dmg_ratio_id)

result_name = "seaside_bldg_dmg_result"
bldg_dmg.set_parameter("result_name", result_name)
bldg_dmg.set_parameter("mapping_id", mapping_id)
bldg_dmg.set_parameter("hazard_type", hazard_type)
bldg_dmg.set_parameter("hazard_id", hazard_id)
bldg_dmg.set_parameter("num_cpu", 1)

# Run Analysis
bldg_dmg.run_analysis()       
# #### Start of the Stochastic Population Allocation

# In[8]:


output_file_path = "cache_data/"

# Population Dislocation
podi = PopulationDislocation(client, output_file_path, False)
merged_block_inv = PopulationDislocationUtil.merge_damage_population_block(
    building_dmg_file='cache_data/seaside_bldg_dmg_result.csv',
    population_allocation_file='cache_data/pop_allocation_1111.csv',
    block_data_file='cache_data/IN-CORE_01av3_SetupSeaside_FourInventories_2018-08-29_bgdata.csv')
merged_final_inv = podi.get_dislocation(seed_i, merged_block_inv)

# save to csv
merged_final_inv.to_csv(output_file_path + "final_inventory_" + str(seed_i) + ".csv", sep=",")


# ### calculate the change of demand

# In[9]:


waternode_population1 = WaterNetworkRecoveryUtil.calc_waternode_population('cache_data/waternode_building_relations.csv', 
                                                   'cache_data/final_inventory_1111.csv')
demand1 = WaterNetworkRecoveryUtil.calc_waternode_demand('cache_data/waternode_building_relations.csv',
                                                         waternode_population1)
with open("cache_data/demand1.json", 'w') as f:
    json.dump(demand1, f)


# ## Water Network Damage
wn_dmg = WaterNetworkDamage(client)
water_pipelines_file = 'cache_data/Pipeline_Skeletonized.shp'
water_pipelines = Dataset.from_file(water_pipelines_file,"pipelineSkeletonized")
wn_dmg.set_input_dataset("water_pipelines", water_pipelines)

water_facility_file = 'cache_data/Facility_Skeletonized.shp'
water_facilities = Dataset.from_file(water_facility_file,"facilitySkeletonized")
wn_dmg.set_input_dataset("water_facilities", water_facilities)

wn_dmg.set_parameter("earthquake_id", '5ba92505ec23090435209071')
wn_dmg.set_parameter("water_facility_mapping_id", '5b47c3b1337d4a387e85564a')
wn_dmg.set_parameter("water_pipeline_mapping_id",'5ba55a2aec2309043530887c')
wn_dmg.set_parameter("num_cpu", 4)
wn_dmg.run_analysis()
# ## Water Network Recovery (without additional dislocation)

# In[18]:


wn_recovery = WaterNetworkRecovery(client)

wn_inp_file = Dataset.from_file('cache_data/Seaside_Skeletonized_WN.inp',"waterNetworkEpanetInp")
wn_recovery.set_input_dataset("wn_inp_file", wn_inp_file)

demand_initial = Dataset.from_file('cache_data/demand0.json', "waterNetworkDemand")
wn_recovery.set_input_dataset("demand_initial", demand_initial)

pipe_dmg = Dataset.from_file('cache_data/pipeline_dmg.csv', "pipelineDamage")
wn_recovery.set_input_dataset("pipe_dmg", pipe_dmg)
pump_dmg = Dataset.from_file('cache_data/pump_dmg.csv', "pumpDamage")
wn_recovery.set_input_dataset("pump_dmg", pump_dmg)
tank_dmg = Dataset.from_file('cache_data/tank_dmg.csv', "tankDamage")
wn_recovery.set_input_dataset("tank_dmg", tank_dmg)

demand = Dataset.from_file('cache_data/demand1.json', "waterNetworkDemand")
wn_recovery.set_input_dataset("demand", demand)

pipe_zone = Dataset.from_file('cache_data/original_PipeZones_seaside_skeleton.csv', "pipeZoning")
wn_recovery.set_input_dataset("pipe_zone", pipe_zone)

wn_recovery.set_parameter("n_days", 3)
wn_recovery.set_parameter("seed", 2)
wn_recovery.set_parameter("result_name", "3_day_recovery")

wn_recovery.run_analysis()
wn_recovery.get_output_datasets()


# In[19]:


pressure_3d = pd.read_csv('3_day_recovery_water_node_pressure.csv', index_col=0)
pressure_3d.head()    


# ## Demand after additional dislocation

# In[20]:


waternode_population2 = WaterNetworkRecoveryUtil.additional_waternode_population_dislocation(timestep=7*3600, 
                                                                        resultsNday_pressure = pressure_3d,
                                                                       prev_waternode_population=waternode_population1)
demand2 = WaterNetworkRecoveryUtil.calc_waternode_demand('cache_data/waternode_building_relations.csv', 
                                                         waternode_population2)
with open("cache_data/demand2.json", 'w') as f:
    json.dump(demand2, f)


# ## Water Network Recovery (with additional dislocation)

# In[21]:


wn_recovery = WaterNetworkRecovery(client)

wn_inp_file = Dataset.from_file('cache_data/Seaside_Skeletonized_WN.inp',"waterNetworkEpanetInp")
wn_recovery.set_input_dataset("wn_inp_file", wn_inp_file)

demand_initial = Dataset.from_file('cache_data/demand0.json', "waterNetworkDemand")
wn_recovery.set_input_dataset("demand_initial", demand_initial)

pipe_dmg = Dataset.from_file('cache_data/pipeline_dmg.csv', "pipelineDamage")
wn_recovery.set_input_dataset("pipe_dmg", pipe_dmg)
pump_dmg = Dataset.from_file('cache_data/pump_dmg.csv', "pumpDamage")
wn_recovery.set_input_dataset("pump_dmg", pump_dmg)
tank_dmg = Dataset.from_file('cache_data/tank_dmg.csv', "tankDamage")
wn_recovery.set_input_dataset("tank_dmg", tank_dmg)

demand = Dataset.from_file('cache_data/demand1.json', "waterNetworkDemand")
wn_recovery.set_input_dataset("demand", demand)

pipe_zone = Dataset.from_file('cache_data/original_PipeZones_seaside_skeleton.csv', "pipeZoning")
wn_recovery.set_input_dataset("pipe_zone", pipe_zone)

demand_additional = Dataset.from_file('cache_data/demand2.json', "waterNetworkDemand")
wn_recovery.set_input_dataset("demand_additional", demand_additional)

wn_recovery.set_parameter("n_days", 5)
wn_recovery.set_parameter("result_name", "5_day_recovery")
wn_recovery.set_parameter("seed", 2)
wn_recovery.set_parameter("intrp_day", 3)

wn_recovery.run_analysis()
wn_recovery.get_output_datasets()


# In[23]:


pressure_5d = pd.read_csv('5_day_recovery_water_node_pressure.csv', index_col=0)
pressure_5d.head()  


# ### Use utility function to plot the network

# In[35]:


import pickle
with open('3_day_recovery_wn.pickle', 'rb') as f:
    wn3day = pickle.load(f)


# ### Frist day

# In[47]:


timestamp = 3600 * 17
WaterNetworkRecoveryUtil.output_water_network(pressure_3d, wn3day, timestamp=timestamp, 
                                              plotly_options={'title': '34th_hours',
                                                 'figsize':[800, 450],
                                             })


# ### Second Day

# In[42]:


timestamp = 3600 * (24+17)
WaterNetworkRecoveryUtil.output_water_network(pressure_3d, wn3day, timestamp=timestamp, 
                                              plotly_options={'title': '34th_hours',
                                                 'figsize':[800, 450],
                                             })


# ### Last Day

# In[43]:


timestamp = 3600 * (48+17)
WaterNetworkRecoveryUtil.output_water_network(pressure_3d, wn3day, timestamp=timestamp, 
                                              plotly_options={'title': '34th_hours',
                                                 'figsize':[800, 450],
                                             })

