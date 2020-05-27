#!/bin/sh

# Exit on error
set -e

# use DEBUG=echo ./release-all.sh to print all commands
export DEBUG=${DEBUG:-""}

$DEBUG docker login hub.ncsa.illinois.edupwd

# Find out what branch we are on
BRANCH=${BRANCH:-"$(git rev-parse --abbrev-ref HEAD)"}

# Find out the version
if [ "$BRANCH" = "master" ]; then
    VERSION=""
elif [ "${BRANCH}" = "develop" ]; then
    VERSION="-dev"
else
    exit 0
fi

#TODO this should be replaced with tagging
# Push pyincore documenation image
docker push hub.ncsa.illinois.edu/incore/doc/pyincore$VERSION:latest