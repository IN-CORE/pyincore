import yaml
import zipfile
import os


script_path = os.path.dirname(os.path.realpath(__file__))
dest_path = os.path.abspath(os.path.join(script_path, '..', '..'))

with open(os.path.join(script_path, 'release-packages.yml')) as f:
    config = yaml.safe_load(f)

internalExcludes = ['__pycache__', 'build', 'cache_data', 'dist', 'pyincore.egg-info']
excludeList = config['exclude'] + internalExcludes

version = config['version']

zipName = 'pyincore_' + version + '.zip'
zf = zipfile.ZipFile(os.path.join(dest_path, zipName), "w")

for dirname, subdirs, files in os.walk(os.path.relpath(os.path.join(script_path, '..'))):
    for exclude in excludeList:
        if exclude in subdirs:
            subdirs.remove(exclude)

    for subdir in subdirs:
        if subdir[0] == '.':  # hidden sub directories
            subdirs.remove(subdir)

    dirbasename = os.path.basename(os.path.abspath(dirname))
    if dirbasename[0] != '.':  # hidden directories
        zf.write(dirname)

    for filename in files:
        if filename[0] != '.':  # hidden files
            zf.write(os.path.join(dirname, filename))
zf.close()

print("Release zip file created at: " + os.path.join(dest_path, zipName))
