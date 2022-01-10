#!/bin/sh

# Exit on error
set -e

# use DEBUG=echo ./release-all.sh to print all commands
export DEBUG=${DEBUG:-""}

export SERVER=${SERVER:-"hub.ncsa.illinois.edu"}
$DEBUG docker login ${SERVER}

# Find out what branch we are on
BRANCH=${BRANCH:-"$(git rev-parse --abbrev-ref HEAD)"}

PKG_VERSION=$(cat source/conf.py | grep "release" | head -1 | awk -F= "{ print $2 }" | sed "s/[release =,',]//g")

# Find out the version
if [ "$BRANCH" = "main" ]; then
    echo "Detected version ${PKG_VERSION}"
    VERSIONS="latest"
    OLDVERSION=""
    TMPVERSION=$PKG_VERSION
    while [ "$OLDVERSION" != "$TMPVERSION" ]; do
        VERSIONS="${VERSIONS} ${TMPVERSION}"
        OLDVERSION="${TMPVERSION}"
        TMPVERSION=$(echo ${OLDVERSION} | sed 's/\.[0-9]*$//')
    done

    TAG=$VERSIONS
elif [ "${BRANCH}" = "develop" ]; then
    TAG="develop"
else
    # Get the issue number for tagging
    TAG=$(echo $BRANCH | sed -e 's/^.*INCORE1-\([0-9]*\).*/INCORE-\1/' -e 's/^\(.\{15\}\).*/\1/' -e 's|/|-|g')
fi

for v in ${TAG}; do
    ${DEBUG} docker tag incore/doc/pyincore hub.ncsa.illinois.edu/incore/doc/pyincore:${v}

    ${DEBUG} docker push ${SERVER}/incore/doc/pyincore:${v}
done
