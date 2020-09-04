# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

### Added 
- Building direct, structural economic loss analysis.  [INCORE1-442](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-442).

### Removed
- Clean up redundant method in analysisutil [INCORE1-732](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-732)

### Added
- \_\_version__ property to show pyincore version. IncoreClient will print the detected version [INCORE1-520](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-520)
- Building Functionality analysis outputs functionality samples as an additional result [INCORE1-734](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-734)
- Python method to interact with flood endpoints in hazard service [INCORE1-747](https://opensource.ncsa.illinois
.edu/jira/browse/INCORE1-747)
### Changed
- Calculate multiple limit states of custom expression fragility curves [INCORE1-682](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-682) 


### Changed
- Updated docstrings to include all hazards that each support [INCORE1-708](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-708)
>>>>>>> develop

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


