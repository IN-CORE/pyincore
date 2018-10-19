from pyincore import InsecureIncoreClient, InventoryDataset, HazardService
from pyincore.analyses.waterfacilitydamage import WaterFacilityDamage
import traceback

if __name__ == "__main__":
    cred = None
    try:
        client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", "incrtest")

        facility_dmg = WaterFacilityDamage(client)
        hazard_id = "earthquake/5b902cb273c3371e1236b36b"
        output = WaterFacilityDamage.get_output_metadata()

        # This is the Memphis Water Facility dataset from the Ergo repository
        facilities_dataset = InventoryDataset("/Users/vnarah2/PycharmProjects/pyincore/pyincore/analyses/waterfacilitydamage/waterfacilities")
        facilities = facilities_dataset.inventory_set

        # pipeline mapping
        mapping_id = "5b47c3b1337d4a387e85564b" #Hazus Potable Water Facility Fragility Mapping - Only PGA
        #mapping_id = "5b47c383337d4a387669d592" #Potable Water Facility Fragility Mapping for INA - Has PGD
        liq_geology_dataset_id = None
        #liq_geology_dataset_id =  "5a284f53c7d30d13bc08249c" #"5ad506f5ec23094e887f4760"
        num_threads = 1
        uncertainity = False

        #result = facility_dmg.waterfacilityset_damage_analysis(facilities, mapping_id, facility_dmg.hazardsvc,
            # hazard_service.split("/")[1], liq_geology_dataset_id, uncertainity)


        facility_dmg.get_damage(facilities, mapping_id, hazard_id, liq_geology_dataset_id, uncertainity, num_threads)

    except EnvironmentError:
        print("exception")
        traceback.print_exc()
