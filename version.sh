#!/bin/bash

VERSION=${1:-9.9.9rc99}
MAJOR=${VERSION%.*}

if [ -e CHANGELOG.md ]; then
  sed -i~ "s/## unreleased.*/## ${VERSION} - $(date +'%Y-%m-%d')/i" CHANGELOG.md
fi

sed -i~ "s/PACKAGE_VERSION = \".*\"/PACKAGE_VERSION = \"${VERSION}\"/" pyincore/globals.py

sed -i~ "s/version = \".*\"/version = \"${VERSION}\"/" recipes/meta.yaml
sed -i~ "s/version: '.*'/version: '${VERSION}'/" scripts/release-packages.yml

sed -i~ -e "s/release = '.*'/release = '${VERSION}'/" -e "s/version = '.*'/version = '${MAJOR}'/" docs/source/conf.py

sed -i~ "s/version = .*/version = '${VERSION}'/" setup.py
