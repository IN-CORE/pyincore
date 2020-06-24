# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

### Added
- Added pycodestyle tests to ensure we follow PEP-8 style guide [INCORE1-650](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-650)

### Changed
- Refactoring road damage analyses to use local dfr3 classes and methods; adding corresponding test folder and
 tests [INCORE1-680](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-680) 
- Refactoring bridge damage analyses to use local dfr3 classes and methods; adding corresponding test folder and
 tests [INCORE1-652](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-652) 
- Refactoring building damage analyses to use local dfr3 classes and methods; adding corresponding test folder and
 tests [INCORE1-644](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-644) 
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


