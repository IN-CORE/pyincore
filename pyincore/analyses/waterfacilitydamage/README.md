# Water Facility Damage

*Parameters:
waterfacilities/ earthquake/59f3315ec7d30d4d6741b0bb 5aa9858d949f232724db474b 0 0

Copy Memphis water facilities into the 'waterfacilities' folder
The earthquake is in Shelby county

*Output:
Calculates limit state probabilites and damage intervals and creates an output file named facility-dmg.csv

*NOTES
1. The PGD limit states needs to be tested. Only one PGD mapping found in the database: 5aa9858d949f232724db4786.
A matching dataset needs to be identified to run the tests on.

2. The code only covers Normal and LogNormal fragilities.

3. Liquefaction and std_dev values are currently hard-coded. They will be fetched from API eventually.

4. Parallelization could be added as needed.

