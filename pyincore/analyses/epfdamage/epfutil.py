# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


class EpfUtil:
    """Utility methods for the electric power facility damage analysis."""
    EPF_HAZUS_FRAGILITY_KEYS = {
        "ESS1", "Low Voltage (115 KV) Substation (Anchored/Seismic Components)",
        "ESS2", "Low Voltage (115 KV) Substation (Unanchored/Standard Components)",
        "ESS3", "Medium Voltage (230 KV) Substation (Anchored/Seismic Components)",
        "ESS4", "Medium Voltage (230 KV) Substation (Unanchored/Standard Components)",
        "ESS5", "High Voltage (500 KV) Substation (Anchored/Seismic Components)",
        "ESS6", "High Voltage (500 KV) Substation (Unanchored/Standard Components)",
        "EPP1", "Small Generation Facility (Anchored Components)",
        "EPP2", "Small Generation Facility (Unanchored Components)",
        "EPP3", "Medium/Large Generation Facility (Anchored Components)",
        "EPP4", "Medium/Large Generation Facility (Unanchored Components)",
        "EDC1", "Distribution Circuit (Seismic Components)",
        "EDC2", "Distribution Circuit (Standard Components)"
    }
