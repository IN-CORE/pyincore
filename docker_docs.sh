#!/bin/sh

# Exit on error
set -e

# use DEBUG=echo ./docker_docs.sh to print all commands
export DEBUG=${DEBUG:-""}

# Find out what branch we are on
BRANCH=${BRANCH:-"$(git rev-parse --abbrev-ref HEAD)"}

# Find out the version
if [ "$BRANCH" = "master" ]; then
    VERSION=""
elif [ "${BRANCH}" = "develop" ]; then
    VERSION="-dev"
else
    docker build -f docs/Dockerfile --no-cache -t pyincore_docs .
    exit 0
fi

# Build docker image
# $DEBUG docker build -f docs/Dockerfile -t hub.ncsa.illinois.edu/incore/doc/pyincore$VERSION:latest .
