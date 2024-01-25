# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

### Changed
- Tornado and Earthquake model [#474](https://github.com/IN-CORE/pyincore/issues/474)

### Fixed
- Fix semantics search pytest by switching to an existing search term 


## [1.15.1] - 2023-12-20 

### Fixed
- Fix NCI Functionality [#463](https://github.com/IN-CORE/pyincore/issues/463)


## [1.15.0] - 2023-12-13

### Added
- Add hazard models to documentation [#448](https://github.com/IN-CORE/pyincore/issues/448)

### Changed
- Upgrade python version from 3.6 to 3.9 [#447](https://github.com/IN-CORE/pyincore/issues/447)
- Enable offline mode for pyincore [#455](https://github.com/IN-CORE/pyincore/issues/455)
- Update MCS analysis to output only required columns for `failure_probability` [#401](https://github.com/IN-CORE/pyincore/issues/401)
- Update CommercialBuildingRecovery to input damage results as a required dataset [#460](https://github.com/IN-CORE/pyincore/issues/460)


## [1.14.0] - 2023-11-08

### Changed
- Properly set the output dataset in Building Portfolio Recovery Analysis [#423](https://github.com/IN-CORE/pyincore/issues/423)
- Dependency clean up [#431](https://github.com/IN-CORE/pyincore/issues/431)

### Added
- Add support for hazard object input from local and remote for building damage analysis [#427](https://github.com/IN-CORE/pyincore/issues/427)

### Fixed
- CGE warning that using series is deprecated and will raise a type error [#357](https://github.com/IN-CORE/pyincore/issues/357)
- Pytest fix in workflow [#425](https://github.com/IN-CORE/pyincore/issues/425)
- Mapping rule to match local repair curve [#438](https://github.com/IN-CORE/pyincore/issues/438)
- Local tornado x and y axis reversed [#439](https://github.com/IN-CORE/pyincore/issues/439)


## [1.13.0] - 2023-10-11

### Changed
- Refactoring the INDP dislocation time mode function to accept different parameters as input [#388](https://github.com/IN-CORE/pyincore/issues/388)

### Added
- Add commercial recovery analysis [#395](https://github.com/IN-CORE/pyincore/issues/395)
- Capability to support for local hazard [#404](https://github.com/IN-CORE/pyincore/issues/404)
- Add support for local hazard with backward compatibility to analyses [#415](https://github.com/IN-CORE/pyincore/issues/415)

### Fixed
- Aggregate hazard exposure column for non-structural building damage analysis to avoid column name cutoff and chaining issue with mean damage [#393](https://github.com/IN-CORE/pyincore/issues/393)


## [1.12.0] - 2023-08-16

### Added
- Add Semantic Module to interact with Semantic service [#361](https://github.com/IN-CORE/pyincore/issues/361)
- Method to get allow Hazard demands from hazard service [#363](https://github.com/IN-CORE/pyincore/issues/363)
- Interdependent Network Design Problem (INDP) [#49](https://github.com/IN-CORE/pyincore/issues/49)

### Fixed
- Post-processing cluster fuction handle empty rows from mcs [#365](https://github.com/IN-CORE/pyincore/issues/365)
- Expose all the incore client parameters [#295](https://github.com/IN-CORE/pyincore/issues/295)
- Fixed testing datasets not being cleaned in the database [#367](https://github.com/IN-CORE/pyincore/issues/367)
- Mismatching spec types in the get_spec method [#383](https://github.com/IN-CORE/pyincore/issues/383)
- Space services methods missing timeout parameters [#375](https://github.com/IN-CORE/pyincore/issues/375)
- Fixed conda dependency issues for Python 3.10 and 3.11 [#343](https://github.com/IN-CORE/pyincore/issues/343)
- Fixed semantic service unit test to handle response object [#386](https://github.com/IN-CORE/pyincore/issues/386)
- Fixed conda publish action [#381](https://github.com/IN-CORE/pyincore/issues/381)

### Changed
- Changed github workflow pytests base from miniconda to micromamba [#378](https://github.com/IN-CORE/pyincore/issues/378)
- Moved `return_http_response` to a single file in utils named `http_util.py` [#384](https://github.com/IN-CORE/pyincore/issues/384)


## [1.11.0] - 2023-06-14

### Added
- Added a name extension for combined wind, wave, surge building damage analysis [#308](https://github.com/IN-CORE/pyincore/issues/308)
- Added error handeling after a request completes in services and the client [#324](https://github.com/IN-CORE/pyincore/issues/324)
- Electric Power Facility Repair Cost Analysis [#345](https://github.com/IN-CORE/pyincore/issues/345)
- Water Facility Repair Cost Analysis [#349](https://github.com/IN-CORE/pyincore/issues/349)
- Water Pipeline Repair Cost Analysis [#351](https://github.com/IN-CORE/pyincore/issues/351)

### Fixed
- TransportationRecovery analysis fails to run with concatentation error [#292](https://github.com/IN-CORE/pyincore/issues/292)
- Fix NCI Functionality float value not iterable error [#291](https://github.com/IN-CORE/pyincore/issues/291)
- Broken analyses related to pandas 2.0 update [#310](https://github.com/IN-CORE/pyincore/issues/310)
- Mean damage should handle buildings that don't have damage probabilities [#131](https://github.com/IN-CORE/pyincore/issues/131)
- Updated check to see if string is float cos outputs where all NaN [#347](https://github.com/IN-CORE/pyincore/issues/347)

## [1.10.0] - 2023-04-21

### Added
- Added Galveston Capital Shock and CGE models as a submodule[#239](https://github.com/IN-CORE/pyincore/issues/239)

### Fixed
- CGE output post process util function [#298](https://github.com/IN-CORE/pyincore/issues/298)
- Population Dislocation utility function arbitrarily assumes there will be dislocated and non-dislocated [#301](https://github.com/IN-CORE/pyincore/issues/301)
- Seaside & Joplin cge uses a fixed location for temporary files [#312](https://github.com/IN-CORE/pyincore/issues/312)
- Functional vs non-functional calculation based of failure sample now [#300](https://github.com/IN-CORE/pyincore/issues/300)
- Exposed timeout and kwargs parameter for incore client methods [#295](https://github.com/IN-CORE/pyincore/issues/295)

## [1.9.0] - 2023-03-15

### Added
- Method in space service to add a dataset by space name [#273](https://github.com/IN-CORE/pyincore/issues/273)
- Method in space service to get space id by space name [#272](https://github.com/IN-CORE/pyincore/issues/272)
- Method in space service to remove dataset from the space [#283](https://github.com/IN-CORE/pyincore/issues/283)
- Method in space service to remove dataset by space name [#284](https://github.com/IN-CORE/pyincore/issues/284)
- Combined wind, surge-wave, and flood building loss [#276](https://github.com/IN-CORE/pyincore/issues/276)

### Changed
- Rewrote clustering utility function to use flexible archetype column [#247](https://github.com/IN-CORE/pyincore/issues/247)
- Made documentation containter to use requirements instead of environemt [#257](https://github.com/IN-CORE/pyincore/issues/257)
- Parallelized the HHRS analysis [#268](https://github.com/IN-CORE/pyincore/issues/268)
- Updated Salt Lake City CGE [#281](https://github.com/IN-CORE/pyincore/issues/281)
- Tested hurricane windfield test methods [#100](https://github.com/IN-CORE/incore-services/issues/100)
- Updatd Salt Lake City CGE formatting and handled infeasible case  [#287](https://github.com/IN-CORE/pyincore/issues/287)

### Fixed
- Duplicate input spec for housing recovery sequential model [#263](https://github.com/IN-CORE/pyincore/issues/263)
- Updated building economic loss analysis to handle case when no occupancy multiplier is provided [#274](https://github.com/IN-CORE/pyincore/issues/274)

## [1.8.0] - 2022-11-16

### Changed
- Enable liquefaction for bridge earthquake damage [#226](https://github.com/IN-CORE/pyincore/issues/226)

### Fixed
- Added missing output spec description for EPF damage [#107](https://github.com/IN-CORE/pyincore/issues/107)
- Removed PEP 8 warnings [#210](https://github.com/IN-CORE/pyincore/issues/210)

## [1.7.0] - 2022-09-14

### Added
- EPN-WDS network cascading interdependency functionality analysis working with MMSA Shelby [#197](https://github.com/IN-CORE/pyincore/issues/197)
- Combined building damage for wind, wave and surge working with Galveston [#199](https://github.com/IN-CORE/pyincore/issues/199)

### Changed
- Improved validation of list types with nested sub-types in get_spec [#180](https://github.com/IN-CORE/pyincore/issues/180)
- Format test for the code simplified to include all the paths [#193](https://github.com/IN-CORE/pyincore/issues/193)
- Enable Hurricane in EPF damage [#200](https://github.com/IN-CORE/pyincore/issues/200)
- Refactored caching mechanism to separate datasets by specifying hashed repository names. [#196](https://github.com/IN-CORE/pyincore/issues/196)

## [1.6.0] - 2022-07-27

### Added
- Pipeline functionality analysis working with MMSA Shelby buried pipelines [#175](https://github.com/IN-CORE/pyincore/issues/175)
- Electric power network functionality analysis working with MMSA Shelby [#178](https://github.com/IN-CORE/pyincore/issues/178)
- Water facility network functionality analysis working with MMSA Shelby [#103](https://github.com/IN-CORE/pyincore/issues/103)

### Changed
- Network utils refactored to use network dataset [#149](https://github.com/IN-CORE/pyincore/issues/149)
- EPF restoration uses damage to compute discretized functionality [#169](https://github.com/IN-CORE/pyincore/issues/169)
- Water facility restoration uses damage to compute discretized functionality [#170](https://github.com/IN-CORE/pyincore/issues/170)
- Household-level housing sequential recovery uses social vulnerability analysis result [#168](https://github.com/IN-CORE/pyincore/issues/168)
- Social vulnerability no longer requires year, state, county and census tract as input parameters [#152](https://github.com/IN-CORE/pyincore/pull/156)

### Fixed
- Fix data type of Census input dataset to CSV [#166](https://github.com/IN-CORE/pyincore/issues/166)
- MCS handles empty rows in the input dataset [#195](https://github.com/IN-CORE/pyincore/issues/195)

## [1.5.0] - 2022-06-29

### Added
- PyPi description and README.rst [#150](https://github.com/IN-CORE/pyincore/issues/150)
- Earthquake liquefaction to building damage analysis [#155](https://github.com/IN-CORE/pyincore/issues/155)
- When releases are made, now push builds to pypi (or testpypi) automatically

### Changed
- Made pyincore build with legacy naming for pypi publish [#138](https://github.com/IN-CORE/pyincore/issues/138)
- Network dataset's sub category's dataType has been changed from networkType to dataType [#145](https://github.com/IN-CORE/pyincore/issues/145)
- Tornado EPN damage analysis uses network dataset instead of link, node, graph datasets [#147](https://github.com/IN-CORE/pyincore/issues/147)
- Building functionality to compute functionality without power network [#143](https://github.com/IN-CORE/pyincore/issues/143)

## [1.4.1] - 2022-04-22

### Fixed
- Fix issue with data type conversion for `blockid` [#129](https://github.com/IN-CORE/pyincore/issues/129)
- Fix indentation bug at DataService [#135](https://github.com/IN-CORE/pyincore/issues/135)

## [1.4.0] - 2022-03-30

### Added
- Check to mean damage analysis to verify damage keys match inventory type and remove unsupported types [#53](https://github.com/IN-CORE/pyincore/issues/53)
- Housing recovery model analysis [#99](https://github.com/IN-CORE/pyincore/issues/99)
- Social vulnerability analysis [#106](https://github.com/IN-CORE/pyincore/issues/106)

### Changed
- Rewrite the EPF and WF restoration model [#100](https://github.com/IN-CORE/pyincore/issues/100)
- Index and improve the performance of restoration util [#113](https://github.com/IN-CORE/pyincore/issues/113)
- Update house unit allocation id [#116](https://github.com/IN-CORE/pyincore/issues/116)

### Fixed
- Fix shapely deprecation error with tornadoepn analysis [#40](https://github.com/IN-CORE/pyincore/issues/40)
- Fix Building economic loss multipliers [#91](https://github.com/IN-CORE/pyincore/issues/91)
- Fix Pandas future warning: dtype in Series [#96](https://github.com/IN-CORE/pyincore/issues/96)
- Fix Pandas future warning: append method [#97](https://github.com/IN-CORE/pyincore/issues/96)
- Fix Population dislocation typo [#112](https://github.com/IN-CORE/pyincore/issues/112)
- Seaside cge displays wrong units in the output [#118](https://github.com/IN-CORE/pyincore/issues/118)
- Fix csv save in Housing recovery analysis [#124](https://github.com/IN-CORE/pyincore/issues/124)


## [1.3.0] - 2022-02-07

### Added
- Water facility restoration model [#76](https://github.com/IN-CORE/pyincore/issues/76)
- Electric power facility model [#77](https://github.com/IN-CORE/pyincore/issues/77)
- Water pipeline restoration model [#78](https://github.com/IN-CORE/pyincore/issues/78)

### Changed
- Update building econ loss to include non structural and content damage [51](https://github.com/IN-CORE/pyincore/issues/51)
- Rename master branch to main [#67](https://github.com/IN-CORE/pyincore/issues/67)
- update fragility specific functions so it deals with the service deprecations and using common DFR3Curve classes [#69](https://github.com/IN-CORE/pyincore/issues/69)
- Support for Restoration curves in pyincore. Included pytests [#71](https://github.com/IN-CORE/pyincore/issues/71)

### Fixed
- Pipeline damage with repair rate only computes total repairs when including liquefaction [#63](https://github.com/IN-CORE/pyincore/issues/63)
- Fix total population dislocation is Null [#72](https://github.com/IN-CORE/pyincore/issues/72)
- Fixed PEP8 issues [#81](https://github.com/IN-CORE/pyincore/issues/81)

## [1.2.0] - 2021-12-15

### Added
- Vacant household category to population dislocation output [#43](https://github.com/IN-CORE/pyincore/issues/43)
- Input dataset with target functionality for Joplin empirical restoration [#56](https://github.com/IN-CORE/pyincore/issues/56)
- Multi-objective retrofit optimization analysis [#19](https://github.com/IN-CORE/pyincore/issues/19)

### Fixed
- EPFDamage to remove deprecated LS/DS code and properly handle liquefaction [#32](https://github.com/IN-CORE/pyincore/issues/32)
- Automatic build for pyincore documentation docker [#61](https://github.com/IN-CORE/pyincore/issues/61)
- Fix get_building_period() method to work with new-format Fragility curves [#15](https://github.com/IN-CORE/pyincore/issues/15)

## [1.1.0] - 2021-10-27

### Added
- Convert HUA and PD outputs to JSON [#9](https://github.com/IN-CORE/pyincore/issues/9)
- Convert population dislocation output to heatmap [#3](https://github.com/IN-CORE/pyincore/issues/3)
- Joplin empirical restoration analysis [#28](https://github.com/IN-CORE/pyincore/issues/28)
- GitHub action to run unit tests [#26](https://github.com/IN-CORE/pyincore/issues/26)
- GitHub action to build documentation [#23](https://github.com/IN-CORE/pyincore/issues/23)
- Conda recipe [#17](https://github.com/IN-CORE/pyincore/issues/17)

### Changed
- Percent change in utils converting CGE output to JSON [#34](https://github.com/IN-CORE/pyincore/issues/34)
- Show API response messages that services return [#6](https://github.com/IN-CORE/pyincore/issues/6)
- Removed deprecated methods [#7](https://github.com/IN-CORE/pyincore/issues/7)

### Fixed
- Pass dataset type as parameter to from_dataframe method [#8](https://github.com/IN-CORE/pyincore/issues/8)
- PEP8 styling issues [#20](https://github.com/IN-CORE/pyincore/issues/20)
- Corrections to residential building recovery [#25](https://github.com/IN-CORE/pyincore/issues/25)

## [1.0.0] - 2021-08-31
### Changed
- Improve runtime efficiency of residential recovery analysis [INCORE1-1339](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1339)

### Added
- Allow users to specify seed value for tornado using hazard service [INCORE1-1374](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1374)
- Create auto docker build and push script for pyincore docs [INCORE1-1348](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1348)
- Convert CGE analysis output to JSON  [INCORE1-1370](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1370)
- Apply hazard exposure to all analyses [INCORE1-1376](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1376)

### Fixed
- Apply PEP8 formatting consistently across codebase [INCORE1-1231](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1231)
- Regularize application of liquefaction for fragility curves across various analyses [INCORE1-1264](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1264)
- Change `math.exp(0)` to 0 in all MMSA bridge DFR3 curves [INCORE1-1377](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1377)
- Change types of capital shock files in Joplin and Seaside CGE to `incore:capitalShocks` [INCORE1-1388](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1388)

## [0.9.6] - 2021-08-04
### Fixed
- Docstrings for technical manual when rendering some method parameters [INCORE1-1333](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1333)
- A bug related to mean damage analysis [INCORE1-1317](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1317)

## [0.9.5] - 2021-07-28
### Changed
- Handle no hazard exposure cases [INCORE1-1130](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1130)
- Modify bridge damage to support MMSA bridge damage [INCORE1-1269](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1269) 
- update python version in requirements [INCORE1-1270](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1270)
- Rename residential recovery analysis [INCORE1-1322](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1322)
- Rename household-level housing serial recovery to sequential [INCORE1-1323](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1323)

### Added
- Samples max damage states as an output for monte carlo analysis [INCORE1-1266](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1266)
- Create joplin residential recovery analysis [INCORE1-1274](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1274)
- Integrate household-level housing recovery sequential model [INCORE1-1275](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1275)
- pyincore-data reference link in pyincore doc [INCORE1-1298](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1298)
- Links to analyses to pyincore doc [INCORE1-1307](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1307)

### Fixed
- Micromamba build with version 0.15.2 [INCORE1-1315](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1315)
- Failing pytests such as posting legacy dfr3 curves, and GET tornado values [INCORE1-1319](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1319)


## [0.9.4] - 2021-06-16
### Added
- Support refactored fragility curves for water facility damage [INCORE1-1063](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1063)
- Support refactored fragility curves for pipeline damage [INCORE1-1057](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1057)
- Support refactored fragility curves for non-structural building damage [INCORE1-1060](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1060)
- Support refactored fragility curves for road damage [INCORE1-1180](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1180)
- Support refactored fragility curves for Tornado EPN damage [INCORE1-1062](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1062)
- Support Add refactored fragility curves for pipeline repair rate analysis [INCORE1-1165](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1065)

### Changed
- Merge roadway failure analysis into road damage [INCORE1-1180](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1180)
- Damage calculation not subject to the upper/lowercase of the demand types and other fragility curve parameters [INCORE1-1221](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1221)

### Fixed
- Calculate building period and conjugate it with "SA" to form the correct demand type [INCORE1-1240](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1240) 


## [0.9.3] - 2021-05-21
### Changed
- Split epf damage output to json and csv, rename LS/DS [INCORE1-1136](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1136)
- Split non-structural damage output to json and csv, rename LS/DS [INCORE1-1137](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1137)
- Split pipeline damage output to json and csv, rename LS/DS [INCORE1-1138](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1138)
- Split pipeline repair rate analysis output to json and csv, rename LS/DS [INCORE1-1139](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1139)
- Split road damage output to json and csv, rename LS/DS [INCORE1-1140](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1140)
- Split road failure analysis output to json and csv, rename LS/DS [INCORE1-1141](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1141)
- Split tornado EPN damage output to json and csv, rename LS/DS [INCORE1-1142](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1142)
- Split water facility damage output to json and csv, rename LS/DS [INCORE1-1143](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1143)
- Optimize damage interval calculation method code [INCORE1-1165](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1165)
- Renaming the json format damage output to new dataType [INCORE-1190](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1190)

### Added
- seed number in Monte Carlo simulation [INCORE1-1086](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1086)
- support retrofit strategy in building damage [INCORE1-1149](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1149)
- enable parsing new format of fragility mapping rules with explicity booleans [INCORE1-1178](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1178)

### Fixed
- Fix broken unit test in test_dataservice [INCORE1-1147](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1147)


## [0.9.2] - 2021-04-22

### Fixed
- Manual and pyincore-viz links in documentation [INCORE1-1122](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1122)
- Relationship between dsf and huestimate variables in Population dislocation analysis [INCORE1-1123](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1123)

## [0.9.1] - 2021-04-09
### Added
- Support bridge hurricane damage and calculation from refactored fragility curves [INCORE1-1058](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1058)
- Create utility method to join table and shapefile [INCORE1-1080](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1080)
- Dependencies in requirement.txt [INCORE1-1108](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1108)

### Changed
- EPF damage using bulk hazard values methods and support refactored fragility curves [INCORE1-1059](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1059)
- Modules in pyincore documentation [INCORE1-867](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-867)
- Random number generator method in social analyses [INCORE1-1040](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1040)
- Data processing utility methods to handle max damage state extraction and clustering [INCORE1-1079](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1079)
- Building Functionality Code using pandas index for performance improvement [INCORE1-1083](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1083)

### Fixed
- Use Decimal package when calculating DS from LS to avoid rounding issue [INCORE1-1033](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1003)
- Overlapping limit state probability curves [INCORE1-1006](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1006)
- Dataset Object get_dataframe_from_shapefile method returns GeoDataframe without CRS [INCORE1-1069](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1069)
- Pytest for network dataset [INCORE1-1078](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-1078)


## [0.9.0] - 2021-02-28
### Added
- Class and methods to handle equation based fragilities [INCORE1-805] (https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-805)
- Methods to get bulk hazard values from hazard endpoints [INCORE1-923] (https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-923)
- Support hurricane in Building Damage analysis [INCORE1-696] (https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-696)
- Support flood in Building Damage analysis [INCORE1-982] (https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-982)
- Convert building damage output to have 3 limit state and 4 damage state [INCORE1-871] (https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-871)
- Split building damage output two files: a csv table with damage results, and a json formatted file with supplemental information [INCORE1-969] (https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-969)
- A utility method to add GUID (Global Unique ID) to inventory dataset in ESRI Shapefile format [INCORE1-978] (https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-978)
- Utility method to do archetype mapping [INCORE1-913] (https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-913)

### Changed
- Demand types and units on fragility model changed from string to list [INCORE1-946] (https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-946)
- Change insignificant damage probability in population dislocation [INCORE1-907] (https://opensource.ncsa.illinois.edu/jira/browse/INCORE-907)
- Replace building inventory csv with shape file in Housing Unit Allocation [INCORE1-977] (https://opensource.ncsa.illinois.edu/jira/browse/INCORE-977)
- Move test scripts from analyses to test analyses [INCORE1-987] (https://opensource.ncsa.illinois.edu/jira/browse/INCORE-987)
- Update precision of damage states, limit states and hazard values to a max of 5 digits [INCORE1-985] (https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-985)

### Fixed
- CGE analysis for Joplin and Seaside uses the system temp folder for temporary file instead of the installation folder [INCORE1-980] (https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-980)

## [0.8.1] - 2020-10-21

### Added
- Building direct economic loss analysis [INCORE1-442](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-442)
- Seaside cge analysis [INCORE1-651](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-651)

### Changed
- Updated Joplin CGE analysis outputs and updated the assignment of ipopt path with shutil [INCORE1-731](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-731)
- Updated Pytests to delete created datasets[INCORE1-784](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-784)
- Added missing fields in fragilitycurveset class [INCORE1-792](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-792)
- Updated dataset types to match changes in mongo dev [INCORE1-806](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-806)

### Fixed
- Typos in damage probabily calculation [INCORE1-781](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-781)
- pytest client initialization by adding a conftest.py file in the pytests root folder [INCORE1-789](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-789)

## [0.8.0] - 2020-09-04

### Removed
- Clean up redundant method in analysisutil [INCORE1-732](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-732)

### Added
- \_\_version__ property to show pyincore version. IncoreClient will print the detected version [INCORE1-520](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-520)
- Building Functionality analysis outputs functionality samples as an additional result [INCORE1-734](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-734)
- Python method to interact with flood endpoints in hazard service [INCORE1-747](https://opensource.ncsa.illinois
.edu/jira/browse/INCORE1-747)

### Changed
- Calculate multiple limit states of custom expression fragility curves [INCORE1-682](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-682) 
- Updated docstrings to include all hazards that each support [INCORE1-708](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-708)

## [0.7.0] - 2020-07-31

### Added
- Wrapper methods for hurricane endpoints and their pytests [INCORE1-698](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-698)
- Road damage by hurricane inundation [INCORE1-697](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-697)
- Docker build and release scripts [INCORE1-709](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-709).  
- Capital shocks analysis [INCORE1-691](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-691).

### Changed
- Allow more input data types for MC failure probability; Add a failure state output for each sample [INCORE1-695](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-695)
- Modify input dataset for building functionality analysis [INCORE1-700](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-700)
- Updated Joplin CGE for new capital shocks output [INCORE1-718](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-718)

## [0.6.4] - 2020-06-30

### Added
- Added pycodestyle tests to ensure we follow PEP-8 style guide [INCORE1-650](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-650)

### Fixed
- in Dataset Class from_json_str() method, set local_file_path by either from dataservices json definition, or pass
 in local file path [INCORE1-662](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-662)

### Changed
- Replace old analyses util methods with new methods that use DFR3 Classes [INCORE1-685](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-685)
- Refactored the following analyses to use local DFR3 classes and methods; added corresponding test folder and tests.
    * Building Damage [INCORE1-644](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-644)
    * Nonstructural Building Damage [INCORE1-664](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-664)
    * Bridge Damage [INCORE1-652](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-652)
    * EPF Damage [INCORE1-663](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-663)
    * Pipeline Damage with repair rate [INCORE1-666](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-666)
    * Pipeline Damage with limit states [INCORE1-665](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-665)
    * Water Facility Damage [INCORE1-668](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-668)
    * Tornado EPN Damage [INCORE1-667](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-667)
    * Road Damage [INCORE1-680](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-680)
- Updated folder structure [INCORE1-655](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-655)
- Refactoring Tornado EPN damage format. [INCORE1-672](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-672)


## [0.6.3] - 2020-05-31

### Added
- Initial implementation of local dfr3 curve and mapping in pyincore [INCORE1-479](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-479)
- Implement conditional and parametric fragility calculation methods but not yet used in analyses [INCORE1-528](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-528)
- User warning message when mapping fails due to mismatched datatype [INCORE1-559](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-559)
- Methods to get uncertainty and variance for model based earthquakes [INCORE1-542](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-542) 
- Added network utility that contains network dataset builder. [INCORE1-576](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-576)

### Fixed
- DFR3 service will now handle empty rules better. Acceptable forms are [[]], [], [null] [INCORE1-606](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-606)

### Changed
- updated documentation modules [INCORE1-617](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-617)

## [0.6.2] - 2020-04-23

### Fixed
- pandas error when accessing missing labels in the dataframe of Joplin CGE's BB matrix [INCORE1-557](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-557)
- make sure in various places that version is bumped up to 0.6.2

## [0.6.1] - 2020-03-31

### Fixed
- fix liquefaction calculation bug in bridge damage analysis [INCORE1-535](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-535) 

### Changed
- refactored EPF damage analysis to submit batch requests to get hazard values from API [INCORE1-510](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-510)
- refactored bridge damage analysis to submit batch requests to get hazard values from API [INCORE1-500](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-500)
- refactored road damage analysis to submit batch requests to get hazard values from API [INCORE1-511](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-511)
- refactoring building damage batch processing [INCORE1-522](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-522)

## [0.6.0] - 2020-02-28

### Added

### Changed
- Refactored building damage analysis to submit batch requests to get hazard values from API [INCORE1-439](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-439)
- Moved mapping matched endpoint to pyincore side [INCORE1-474](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-474)

### Fixed
- make sure only download zip from dataservice when the zipped cached file doesn't exist [INCORE1-457](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-457)
- updated failing hazard test [INCORE1-477](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-477)

## [0.5.5] - 2020-02-10

### Added
- move inventory dfr3 curve mapping logic to pyincore side so we can phase out /match endpoint[INCORE1-474](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-474)

- Added insecure client to test against {url}:31888 when using NCSA's network. [INCORE1-455](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-455)
- Added documentation to building functionality analysis. [INCORE-435](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-435)

### Fixed

- add another layer of folder in cache folder using datasetid to differentiate 
datasets with the same name [INCORE1-433](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-433)
- Fixed link in pyIncore documentation, page refs
- Fixed end of file exception caused by analysis that run in parallel by checking validity of token on client instantiation. [INCORE1-427](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-427)
- Fixed url inconsistency in dfr3 tests
- Fixed error in reading token file in windows os [INCORE-449](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-449)
- Bug in setting fragility_key in building damage[INCORE1-456](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-456)

## [0.5.4] - 2019-12-23

### Fixed

- Update bridge damage type in MonteCarlo Analysis
- Fixed error handling with formatting problem in pyIncore Client

## [0.5.3] - 2019-12-20
pyIncore release for IN-CORE v1.0

### Added

- CHANGELOG, CONTRIBUTORS, and LICENSE

## [0.5.2] - 2019-10-17

## [0.5.1] - 2019-09-11

## [0.5.0] - 2019-08-29

## [0.4.1] - 2019-08-15

## [0.4.0] - 2019-07-25

## [0.3.0] - 2019-04-26

## [0.2.0] - 2019-03-13


