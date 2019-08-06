# Water Facility Damage

##Parameters for run():
facilities, mapping_id, hazard_type, hazard_id, liq_geology_dataset_id, uncertainty, num_cpus

##Example Parameters:

* facilities: Dataset ID of a water facility. '5a284f2ac7d30d13bc081e52' for memphis water facilities

* mapping_id: "5b47c3b1337d4a387e85564b" #Hazus Potable Water Facility Fragility Mapping - Only PGA
             "5b47c383337d4a387669d592" #Potable Water Facility Fragility Mapping for INA - Has PGD

* hazard_type: "earthquake"             
* hazard_id: "5b902cb273c3371e1236b36b" # An Earthquake in memphis region

* liq_geology_dataset_id: "5ad506f5ec23094e887f4760" #Memphis soil geology dataset for Liquefaction 

* uncertainty: True/False

* num_cpus: Provide a positive integer. If omitted, the progrma calculates optimal cpus that can be used.

##Output:
Calculates limit state probabilites and damage intervals and creates an output csv file

##NOTES

1. The code only covers Normal and LogNormal fragilities.

2. Code only covers the fragilities with 4 limit states (slight, moderate, extensive and complete)

3. Uncertainity is not implemented. They will be fetched from API eventually.
