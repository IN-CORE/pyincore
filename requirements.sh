#!/bin/bash

# setup pip-compile to resolve dependencies, also is minimal version of python
if [ ! -d /tmp/pyincore-requirements ]; then
  python3 -m virtualenv /tmp/pyincore-requirements
  . /tmp/pyincore-requirements/bin/activate
  pip install pip-tools
else
  . /tmp/pyincore-requirements/bin/activate
fi

# all requirements in pyincore files
IMPORTS=$(egrep -R -h --include "*.py" '(import|from) ' pyincore | \
          sed -e 's/^ *"//' -e 's/\\n",$//' | \
          egrep '^(from|import)' | \
          awk '!/pyincore/ { print $2 }' | \
          sort -u | \
          egrep -v '^(\(|_)' | \
          sed 's/,/ /g')
# check which imports are not standard python
rm -f requirements.tmp
for x in $IMPORTS; do
  python3 -c "import $x" 2>&1 | \
    awk '/ModuleNotFoundError/ { print $5 }' | \
    sed -e 's/yaml/pyyaml/' -e 's/jose/python-jose/' -e 's/_pytest/pytest/' -e "s/'//g" >> requirements.tmp
done
sort -u requirements.tmp > requirements.pyincore

# all requirements in test files
IMPORTS=$(egrep -R -h --include "*.py" '(import|from) ' tests | \
          sed -e 's/^ *"//' -e 's/\\n",$//' | \
          egrep '^(from|import)' | \
          awk '!/pyincore/ { print $2 }' | \
          sort -u | \
          egrep -v '^(\(|_)' | \
          sed 's/,/ /g')
# check which imports are not standard python
rm -f requirements.tmp
for x in $IMPORTS; do
    MISSING=$(python3 -c "import $x" 2>&1 | \
      awk '/ModuleNotFoundError/ { print $5 }' | \
      sed -e 's/yaml/pyyaml/' -e 's/jose/python-jose/' -e 's/_pytest/pytest/' -e "s/'//g")
    if ! grep "${MISSING}" requirements.pyincore &>/dev/null ; then
      echo ${MISSING} >> requirements.tmp
    fi
done
sort -u requirements.tmp > requirements.testing

# all requirements in notebook files
IMPORTS=$(egrep -R -h --include "*.ipynb" '(import|from) ' pyincore | \
          sed -e 's/^ *"//' -e 's/\\n",$//' | \
          egrep '^(from|import)' | \
          awk '!/pyincore/ { print $2 }' | \
          sort -u | \
          egrep -v '^(\(|_)' | \
          sed 's/,/ /g')
# check which imports are not standard python
rm -f requirements.tmp
for x in $IMPORTS; do
    MISSING=$(python3 -c "import $x" 2>&1 | \
      awk '/ModuleNotFoundError/ { print $5 }' | \
      sed -e 's/yaml/pyyaml/' -e 's/jose/python-jose/' -e 's/_pytest/pytest/' -e "s/'//g")
    if ! grep "${MISSING}" requirements.pyincore &>/dev/null ; then
      echo ${MISSING} >> requirements.tmp
    fi
done
sort -u requirements.tmp > requirements.notebooks

# combine pyincore and testing
cat requirements.pyincore requirements.testing requirements.notebooks > requirements.in

# create the requirements.txt file for pip. This is intended to setup a virtualenv for
# development on pyincore.
pip-compile --quiet --upgrade --rebuild --output-file requirements.txt requirements.in
cat requirements.txt | grep -v ' *#.*' | grep -v '^$' > requirements.ver

# create the environment.yml file for conda. This is intended to setup a conda environment for
# development on pyincore.
cat << EOF > environment.yml
name: base
channels:
  - conda-forge
  - defaults
dependencies:
  - ipopt>=3.11
  - numpy>=1.16
EOF
cat requirements.ver | egrep -v '^(numpy|ipopt)==' | sed 's/^/  - /' >> environment.yml

# update conda recipe
for x in $(cat requirements.pyincore | egrep -v '(ipopt|numpy)'); do
  if ! grep "    - $x==" recipes/meta.yaml >/dev/null ; then
    echo "NEW IMPORT $x"
  fi
  version=$(grep "^$x==" requirements.ver | sed 's/wntr==/wntr==v/')
  sed -i~ "s/    - $x==.*/    - $version/" recipes/meta.yaml
done
for x in $(cat requirements.testing | egrep -v '(pytest)'); do
  if ! grep "    - $x==" recipes/meta.yaml >/dev/null ; then
    echo "NEW IMPORT $x"
  fi
  version=$(grep "^$x==" requirements.ver)
  sed -i~ "s/    - $x==.*/    - $version/" recipes/meta.yaml
done

# update setup file
for x in $(cat requirements.pyincore | egrep -v '(ipopt)'); do
  if ! grep "'$x==" setup.py >/dev/null ; then
    echo "NEW IMPORT $x"
  fi
  version=$(grep "^$x==" requirements.ver)
  sed -i~ "s/'$x==.*'/'$version'/" setup.py
done
for x in $(cat requirements.testing); do
  if ! grep "'$x==" setup.py >/dev/null ; then
    echo "NEW IMPORT $x"
  fi
  version=$(grep "^$x==" requirements.ver)
  sed -i~ "s/'$x==.*'/'$version'/" setup.py
done
for x in $(cat requirements.notebooks); do
  if ! grep "'$x==" setup.py >/dev/null ; then
    echo "NEW IMPORT $x"
  fi
  version=$(grep "^$x==" requirements.ver)
  sed -i~ "s/'$x==.*'/'$version'/" setup.py
done

# cleanup
rm -f requirements.pyincore requirements.testing requirements.notebooks requirements.tmp requirements.ver
