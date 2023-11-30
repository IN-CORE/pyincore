# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from logging import config as logging_config

import logging
import os
import shutil

PACKAGE_VERSION = "1.14.0"

INCORE_API_PROD_URL = "https://incore.ncsa.illinois.edu"
INCORE_API_DEV_URL = "https://incore-dev.ncsa.illinois.edu"

KEYCLOAK_AUTH_PATH = "/auth/realms/In-core/protocol/openid-connect/token"
KEYCLOAK_USERINFO_PATH = "/auth/realms/In-core/protocol/openid-connect/userinfo"
CLIENT_ID = "react-auth"
INCORE_LDAP_TEST_USER_INFO = "{\"preferred_username\": \"incrtest\"}"

PYINCORE_PACKAGE_HOME = os.path.dirname(__file__)
PYINCORE_ROOT_FOLDER = os.path.dirname(os.path.dirname(__file__))
USER_HOME = os.path.expanduser('~')
USER_CACHE_DIR = ".incore"
PYINCORE_USER_CACHE = os.path.join(USER_HOME, USER_CACHE_DIR)

DATA_CACHE_FOLDER_NAME = "cache_data"
DATA_CACHE_HASH_NAMES_SERVICE_JSON = "service.json"
PYINCORE_USER_DATA_CACHE = os.path.join(PYINCORE_USER_CACHE, DATA_CACHE_FOLDER_NAME)
PYINCORE_SERVICE_JSON = os.path.join(PYINCORE_USER_CACHE, DATA_CACHE_HASH_NAMES_SERVICE_JSON)

LOGGING_CONFIG = os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logging.ini'))
logging_config.fileConfig(LOGGING_CONFIG)
LOGGER = logging.getLogger('pyincore')

TEST_DATA_DIR = os.path.join(PYINCORE_ROOT_FOLDER, "tests/data")

MAX_LOGIN_ATTEMPTS = 3

IPOPT_PATH = shutil.which("ipopt")
GLPK_PATH = shutil.which("glpsol")
SCIP_PATH = shutil.which("scip")

DAMAGE_PRECISION = 10

DEFAULT_ALLOWED_DEMANDS = {
    "earthquake": [
        {
            "demand_type": "pga",
            "demand_unit": [
                "g",
                "in/sec^2",
                "m/sec^2"
            ],
            "description": "Peak ground acceleration"
        },
        {
            "demand_type": "pgv",
            "demand_unit": [
                "in/s",
                "cm/s"
            ],
            "description": "Peak ground velocity"
        },
        {
            "demand_type": "pgd",
            "demand_unit": [
                "in",
                "ft",
                "m"
            ],
            "description": "Peak ground displacement"
        },
        {
            "demand_type": "sa",
            "demand_unit": [
                "g",
                "in/sec^2",
                "m/sec^2"
            ],
            "description": "Spectral acceleration"
        },
        {
            "demand_type": "sd",
            "demand_unit": [
                "in",
                "ft",
                "m",
                "cm"
            ],
            "description": "Spectral displacement"
        },
        {
            "demand_type": "sv",
            "demand_unit": [
                "cm/s",
                "in/s"
            ],
            "description": "Spectral Velocity"
        }
    ],
    "tsunami": [
        {
            "demand_type": "Hmax",
            "demand_unit": [
                "ft",
                "m"
            ],
            "description": "Onshore: maximum tsunami height above local ground level overland. Offshore: "
                           "maximum tsunami height taken crest to trough"
        },
        {
            "demand_type": "Vmax",
            "demand_unit": [
                "mph",
                "kph",
                "ft/sec",
                "m/sec"
            ],
            "description": "Maximum near-coast or overland water velocity due to tsunami"
        },
        {
            "demand_type": "Mmax",
            "demand_unit": [
                "m^3/s^2",
                "ft^3/s^2"
            ],
            "description": ""
        }
    ],
    "flood": [
        {
            "demand_type": "inundationDepth",
            "demand_unit": [
                "ft",
                "m"
            ],
            "description": "Depth of the water surface relative to local ground level"
        },
        {
            "demand_type": "waterSurfaceElevation",
            "demand_unit": [
                "ft",
                "m"
            ],
            "description": "Elevation of the water surface above reference datum (e.g. NAVD88, mean sea level)"
        }
    ],
    "tornado": [
        {
            "demand_type": "wind",
            "demand_unit": [
                "mps",
                "mph"
            ],
            "description": "Defined as a wind velocity below"
        }
    ],
    "hurricaneWindfield": [
        {
            "demand_type": "3s",
            "demand_unit": [
                "kph",
                "mph",
                "kt"
            ],
            "description": "Typically, reported at 10 m above local ground or sea level"
        },
        {
            "demand_type": "60s",
            "demand_unit": [
                "kph",
                "mph",
                "kt"
            ],
            "description": "Typically, reported at 10 m above local ground or sea level"
        }
    ],
    "hurricane": [
        {
            "demand_type": "waveHeight",
            "demand_unit": [
                "ft",
                "m",
                "in",
                "cm"
            ],
            "description": " Height of wave measured crest to trough.  Characteristic wave height is typically the  "
                           "average of one third highest waves for a random sea."
        },
        {
            "demand_type": "surgeLevel",
            "demand_unit": [
                "ft",
                "m",
                "in",
                "cm"
            ],
            "description": "Elevation of the water surface above reference datum (e.g. NAVD88, mean sea level)"
        },
        {
            "demand_type": "inundationDuration",
            "demand_unit": [
                "hr",
                "min",
                "s"
            ],
            "description": "Time that inundation depth exceeds a critical threshold for a given storm"
        },
        {
            "demand_type": "inundationDepth",
            "demand_unit": [
                "ft",
                "m",
                "in",
                "cm"
            ],
            "description": "Depth of the water surface relative to local ground level"
        },
        {
            "demand_type": "wavePeriod",
            "demand_unit": [
                "s",
                "hr",
                "min"
            ],
            "description": "Time between wave crests.  Characteristic wave period is typically the inverse of the "
                           "spectral peak frequency for a random sea"
        },
        {
            "demand_type": "waveDirection",
            "demand_unit": [
                "deg",
                "rad"
            ],
            "description": "Principle wave direction associated with the characteristic wave height and period"
        },
        {
            "demand_type": "waterVelocity",
            "demand_unit": [
                "ft/s",
                "m/s",
                "in/s"
            ],
            "description": ""
        },
        {
            "demand_type": "windVelocity",
            "demand_unit": [
                "ft/s",
                "m/s",
                "m/sec",
                "in/s"
            ],
            "description": ""
        }
    ],
    "earthquake+tsunami": [
        {
            "demand_type": "pga",
            "demand_unit": [
                "g",
                "in/sec^2",
                "m/sec^2"
            ],
            "description": "Peak ground acceleration"
        },
        {
            "demand_type": "pgv",
            "demand_unit": [
                "in/s",
                "cm/s"
            ],
            "description": "Peak ground velocity"
        },
        {
            "demand_type": "pgd",
            "demand_unit": [
                "in",
                "ft",
                "m"
            ],
            "description": "Peak ground displacement"
        },
        {
            "demand_type": "sa",
            "demand_unit": [
                "g",
                "in/sec^2",
                "m/sec^2"
            ],
            "description": "Spectral acceleration"
        },
        {
            "demand_type": "sd",
            "demand_unit": [
                "in",
                "ft",
                "m",
                "cm"
            ],
            "description": "Spectral displacement"
        },
        {
            "demand_type": "sv",
            "demand_unit": [
                "cm/s",
                "in/s"
            ],
            "description": "Spectral Velocity"
        },
        {
            "demand_type": "Hmax",
            "demand_unit": [
                "ft",
                "m"
            ],
            "description": "Onshore: maximum tsunami height above local ground level overland. Offshore: maximum tsunami height taken crest to trough"
        },
        {
            "demand_type": "Vmax",
            "demand_unit": [
                "mph",
                "kph",
                "ft/sec",
                "m/sec"
            ],
            "description": "Maximum near-coast or overland water velocity due to tsunami"
        },
        {
            "demand_type": "Mmax",
            "demand_unit": [
                "m^3/s^2",
                "ft^3/s^2"
            ],
            "description": ""
        }
    ]
}
