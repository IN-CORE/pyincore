#!/bin/sh

# Exit on error
set -e

# use DEBUG=echo docker.sh to print all commands
export DEBUG=${DEBUG:-""}

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

# go to parent directory to create a docker
cd ../

# Build docker image
$DEBUG docker build -t hub.ncsa.illinois.edu/incore/doc/pyincore$VERSION:latest -f Dockerfile.docs .
