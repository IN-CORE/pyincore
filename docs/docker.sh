#!/bin/sh

# Exit on error
set -e

# use DEBUG=echo docker.sh to print all commands
export DEBUG=${DEBUG:-""}

# Find out what branch we are on
BRANCH=${BRANCH:-"$(git rev-parse --abbrev-ref HEAD)"}

# go to parent directory to create a docker
cd ../

# Build docker image
$DEBUG docker build -t incore/doc/pyincore -f Dockerfile.docs .
