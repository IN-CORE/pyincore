from pyincore.analyses.buildingportfolio.recovery.BuildingPortfolioRecoveryAnalysis import  BuildingPortfolioRecoveryAnalysis
from pyincore import Dataset
from pyincore import InsecureIncoreClient

client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", "incrtest")


bldg_damage_file = "./data/DamageAnalysisResults.csv"
bldg_damage_dataset = Dataset.from_file(bldg_damage_file, "ergo:buildingDamageVer4")

bldg_data_file = "./data/Building_data.csv"
bldg_data_dataset = Dataset.from_file(bldg_data_file, "ergo:buildingDamageVer4")

utility_file = "./data/utility.csv"
utility_dataset = Dataset.from_file(utility_file, "ergo:utilityAvailability")

utility_file2 = "./data/utility2.csv"
utility_dataset2 = Dataset.from_file(utility_file2, "ergo:utilityAvailability")

mean_repair_file = "./data/Mean_Repair.csv"
mean_repair_dataset = Dataset.from_file(mean_repair_file, "ergo:buildingDamageRatios")

coefFL_file = "./data/coefFL.csv"
coefFL_dataset = Dataset.from_file(coefFL_file, "ergo:coefFL")

occupancy_mapping = "./data/Occupancy_Code_Mapping.csv"
occupancy_dataset = Dataset.from_file(occupancy_mapping, "ergo:mapping")


bldg_portfolio_recovery = BuildingPortfolioRecoveryAnalysis(client)
bldg_portfolio_recovery.set_parameter("result_name", "building_portfolio_recovery_nov7")
bldg_portfolio_recovery.set_parameter("uncertainty", True)
bldg_portfolio_recovery.set_parameter("sample_size", 1000)
bldg_portfolio_recovery.set_parameter("number_of_iterations", 500)
bldg_portfolio_recovery.set_parameter("num_cpu", 4)

bldg_portfolio_recovery.set_input_dataset("building_damage", bldg_damage_dataset)
bldg_portfolio_recovery.set_input_dataset("occupancy_mapping", occupancy_dataset )
bldg_portfolio_recovery.set_input_dataset("building_data", bldg_data_dataset)
bldg_portfolio_recovery.set_input_dataset("utility", utility_dataset)
bldg_portfolio_recovery.set_input_dataset("utility_partial", utility_dataset2)
bldg_portfolio_recovery.set_input_dataset("dmg_ratios", mean_repair_dataset)
bldg_portfolio_recovery.set_input_dataset("coefFL", coefFL_dataset)

bldg_portfolio_recovery.run_analysis()