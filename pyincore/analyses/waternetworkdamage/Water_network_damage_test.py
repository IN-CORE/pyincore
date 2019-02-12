# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


# In[1]:


from pyincore import InsecureIncoreClient
from pyincore.analyses.waternetworkdamage import WaterNetworkDamage
from pyincore.dataset import Dataset


# In[2]:


client = InsecureIncoreClient("http://incore2-services:8888/", 'incrtest')
wn_dmg = WaterNetworkDamage(client)


# In[3]:


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


# In[ ]:


wn_dmg.run_analysis()


# In[ ]:


wn_dmg.get_output_datasets()


# In[ ]:




