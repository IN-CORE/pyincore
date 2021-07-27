# Pyincore Scripts

Useful scripts for pyincore

## Create Release Zip
Creates a zip file with all pyincore code except the exclusions specified in release-packages.yml. Used to exclude analyses that are not ready to be open sourced yet.

`python3 build-release.py`

It is recommended to run this from a clean pyincore folder. Avoid creating the release zip from a developer's instance of pyincore to avoid including any intermediate files or results generated in the root folder.
