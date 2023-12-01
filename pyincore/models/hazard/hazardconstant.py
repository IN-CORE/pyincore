# Copyright (c) 2023 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

class HazardConstant:

    """HazardConstant class to hold all the constants related to hazard."""
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
