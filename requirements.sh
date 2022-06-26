#!/bin/bash

set -o noglob

#TESTPYPI="--extra-index-url https://test.pypi.org/simple/"
#TESTPYPI="--index-url http://localhost:3141/incore/dev"

MODULE="pyincore"
EXTRA_CONDA="ipopt>=3.11"

# setup pip-compile to resolve dependencies, also is minimal version of python
if [ ! -d /tmp/pyincore-requirements ]; then
  python3 -m virtualenv /tmp/pyincore-requirements
  . /tmp/pyincore-requirements/bin/activate
  pip install pip-tools
else
  . /tmp/pyincore-requirements/bin/activate
fi

# all requirements in pyincore_viz files
rm requirements.in
for x in ${MODULE} tests notebooks; do
  case $x in
    notebooks)
      FILES="*.ipynb"
      FOLDER="${MODULE}"
      ;;
    *)
      FILES="*.py"
      FOLDER="${x}"
      ;;
  esac
  IMPORTS=$(egrep -R -h --include "${FILES}" '(import|from) ' ${FOLDER} | \
            sed -e 's/^ *"//' -e 's/\\n",$//' | \
            egrep '^(from|import)' | \
            awk "!/${MODULE}/ { print \$2 }" | \
            sort -u | \
            egrep -v '^(\(|_)' | \
            sed 's/,/ /g')
  if [ "${IMPORTS}" == "" ]; then continue; fi
  # check which imports are not standard python
  rm -f requirements.tmp
  for i in $IMPORTS; do
    MISSING=$(python3 -c "import $i" 2>&1 | \
      awk '/ModuleNotFoundError/ { print $5 }' | \
      sed -e 's/yaml/pyyaml/' -e 's/jose/python-jose/' -e 's/_pytest/pytest/' -e 's/PIL/pillow/' -e 's/osgeo//' -e "s/'//g")
    if ! grep "${MISSING}" requirements.in &>/dev/null ; then
      echo ${MISSING} >> requirements.tmp
    fi
  done
  sort -u requirements.tmp > requirements.${x}
  cat requirements.${x} >> requirements.in
done

# some tweaks to requirements.in to fix dependencies not found in conda
sed -i~ -e 's/pyproj/pyproj<3.3.0/' requirements.in

# create the requirements.txt file for pip. This is intended to setup a virtualenv for
# development on pyincore_viz.
pip-compile ${TESTPYPI} --quiet --upgrade --rebuild --output-file requirements.txt requirements.in
cat requirements.txt | grep -v ' *#.*' | grep -v '^$' | grep -v "^${TESTPYPI}$" > requirements.ver

# create the environment.yml file for conda. This is intended to setup a conda environment for
# development on pyincore_viz.
cat << EOF > environment.yml
name: base
channels:
  - conda-forge
  - defaults
dependencies:
  - numpy>=1.16
EOF
for p in ${EXTRA_CONDA}; do
  echo "  - $p" >> environment.yml
done
cat requirements.ver | egrep -v '^(numpy|ipopt)==' | sed 's/^/  - /' >> environment.yml

# update conda recipe
for y in ${MODULE} tests; do
  if [ ! -e requirements.${y} ]; then continue; fi
  for x in $(cat requirements.${y} | egrep -v '(ipopt|numpy|pytest)'); do
    if ! grep "    - $x==" recipes/meta.yaml >/dev/null ; then
      echo "CONDA [$y] NEW IMPORT : $x"
    fi
    version=$(grep "^$x==" requirements.ver)
    sed -i~ "s/    - $x==.*/    - $version/" recipes/meta.yaml
  done
done

# conda fixes
for x in environment.yml recipes/meta.yaml; do
  sed -e 's/wntr==0.4.2/wntr==v0.4.2/' \
      -e 's/soupsieve==2.3.2.post1/soupsieve==2.3.1/' \
      -e 's/pure-eval==0.2.2/pure_eval==0.2.1/' \
      -e 's/fastjsonschema/python-fastjsonschema/' \
      -e 's/ipython-genutils/ipython_genutils/' \
      -e 's/jupyter-core/jupyter_core/' \
      -e 's/jupyter-client/jupyter_client/' \
      -e 's/jupyterlab-pygments/jupyterlab_pygments/' \
      -e 's/jupyterlab-widgets/jupyterlab_widgets/' \
      -e 's/prometheus-client/prometheus_client/' \
      -e 's/stack-data/stack_data/' \
      -i~ $x
done

# update setup file
for y in ${MODULE} tests notebooks; do
  if [ ! -e requirements.${y} ]; then continue; fi
  for x in $(cat requirements.${y} | egrep -v '(ipopt|pytest)'); do
    if ! grep "'$x==" setup.py >/dev/null ; then
      echo "SETUP [$y] NEW IMPORT $x"
    fi
    version=$(grep "^$x==" requirements.ver)
    sed -i~ "s/'$x==.*'/'$version'/" setup.py
  done
done

# cleanup
rm -f requirements.${MODULE} requirements.tests requirements.notebooks requirements.tmp requirements.ver
