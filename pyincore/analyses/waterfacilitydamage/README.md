# Water Facility Damage

##Parameters for get_damage(): 
facilities, mapping_id, hazard_id, liq_geology_dataset_id, uncertainity, num_threads

##Example Parameters:

* facilities: Copy "Memphis Water Facility dataset from the Ergo repository" in a folder and get facilities from it.

* mapping_id: "5aa9858d949f232724db474b" #Hazus Potable Water Facility Fragility Mapping - Only PGA
             "5aa9858d949f232724db4786" #Potable Water Facility Fragility Mapping for INA - Has PGD
             
* hazard_id: "earthquake/59f3315ec7d30d4d6741b0bb" # An Earthquake in memphis region

* liq_geology_dataset_id: "5ad506f5ec23094e887f4760" #Memphis soil geology dataset for Liquefaction 

* uncertainity: True/False

* num_threads: Provide a positive int. Use -1 to ignore paralellization.

##Output:
Calculates limit state probabilites and damage intervals and creates an output file named dmg-results-dmg.csv

##NOTES

1. The code only covers Normal and LogNormal fragilities.

2. Code only covers the fragilities with 4 limit states (slight, moderate, extensive and complete)

3. Uncertainity is not implemnted. They will be fetched from API eventually.

4. Parallelization errors in MacOS Debug mode from Pycharm that uses 'pydevd' as Debugger (Needs testing on multiple environments)

