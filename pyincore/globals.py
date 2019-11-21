# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import os
import logging
from logging import config as logging_config

PACKAGE_VERSION = "0.5.2"

# INCORE_API_PROD_URL = "https://incore2-services.ncsa.illinois.edu"
INCORE_API_PROD_URL = "https://incore-dev-kube.ncsa.illinois.edu"
INCORE_API_INSECURE_URL = "http://incore2-services.ncsa.illinois.edu:8888"
# INCORE_API_DEV_INSECURE_URL = "http://incore2-services-dev.ncsa.illinois.edu:8888"
INCORE_API_DEV_INSECURE_URL = "http://localhost:8080"
INCORE_API_DEV_URL = "https://incore2-services-dev.ncsa.illinois.edu"
INCORE_LDAP_TEST_USER = "incrtest"

KEYCLOAK_TOKEN_URL = "https://incore-dev-kube.ncsa.illinois.edu/auth/realms/In-core/protocol/openid-connect/token"
CLIENT_ID = "react-auth"
INCORE_LDAP_TEST_USER_INFO = "{\"preferred_username\": \"incrtest\"}"

PYINCORE_PACKAGE_HOME = os.path.dirname(__file__)
PYINCORE_ROOT_FOLDER = os.path.dirname(os.path.dirname(__file__))
USER_HOME = os.path.expanduser('~')
USER_CACHE_DIR = ".incore"
PYINCORE_USER_CACHE = os.path.join(USER_HOME, USER_CACHE_DIR)
CRED_FILE_NAME = ".incorepw"
DATA_CACHE_FOLDER_NAME = "cache_data"
PYINCORE_USER_DATA_CACHE = os.path.join(PYINCORE_USER_CACHE, DATA_CACHE_FOLDER_NAME)

LOGGING_CONFIG = os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logging.ini'))
logging_config.fileConfig(LOGGING_CONFIG)
LOGGER = logging.getLogger('pyincore')
