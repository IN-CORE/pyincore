import yaml
import zipfile
import os

with open('release-packages.yml') as f:
    config = yaml.safe_load(f)

internalExcludes = ['__pycache__', 'build', 'cache_data']
excludeList = config['exclude'] + internalExcludes

dest_path = os.path.abspath(os.path.join('..', '..'))
zipName = 'pyincore_release.zip'
zf = zipfile.ZipFile(os.path.join(dest_path, zipName), "w")

for dirname, subdirs, files in os.walk('..'):
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
