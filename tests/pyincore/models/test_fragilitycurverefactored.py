import json
import os
import collections

import pytest

from pyincore import globals as pyglobals, FragilityCurveSet, AnalysisUtil
import numpy as np


def test_fragility_set_small_overlap():
    fragility_set = get_fragility_set("refactored_fragility_curve.json")

    # Test Case 1 - single overlap
    limit_states = collections.OrderedDict([("LS_0", 0.9692754643), ("LS_1", 0.0001444974), ("LS_2", 0.0004277083)])
    limit_states = AnalysisUtil.float_dict_to_decimal(limit_states)
    damage_states = fragility_set._3ls_to_4ds(limit_states)
    assert damage_states['DS_0'] == AnalysisUtil.float_to_decimal(0.0307245357) and \
           damage_states['DS_1'] == AnalysisUtil.float_to_decimal(0.968847756) and \
           damage_states['DS_2'] == AnalysisUtil.float_to_decimal(0.0) and \
           damage_states['DS_3'] == AnalysisUtil.float_to_decimal(0.0004277083)

    # Test Case 2 - double overlap
    limit_states = collections.OrderedDict([("LS_0", 0.12), ("LS_1", 0.64), ("LS_2", 0.8)])
    limit_states = AnalysisUtil.float_dict_to_decimal(limit_states)
    damage_states = fragility_set._3ls_to_4ds(limit_states)
    assert damage_states['DS_0'] == AnalysisUtil.float_to_decimal(0.2) and \
           damage_states['DS_1'] == AnalysisUtil.float_to_decimal(0.0) and \
           damage_states['DS_2'] == AnalysisUtil.float_to_decimal(0.0) and \
           damage_states['DS_3'] == AnalysisUtil.float_to_decimal(0.8)


def get_fragility_set(fragility_dir: str):
    with open(os.path.join(pyglobals.TEST_DATA_DIR, fragility_dir), 'r', encoding='utf-8') as f:
        fragility_curve = json.load(f)
    fragility_set = FragilityCurveSet(fragility_curve)
    return fragility_set


def get_remote_fragility_set(fragility_id: str):
    dfr3svc = pytest.fragilitysvc
    fragility_set = FragilityCurveSet(dfr3svc.get_dfr3_set(fragility_id))
    return fragility_set


def test_create_fragility_set():
    fragility_set = get_fragility_set("refactored_fragility_curve.json")
    assert len(fragility_set.fragility_curves) != 0


@pytest.mark.parametrize("fragility_set,hazard_values,args,expected", [
    (get_fragility_set("refactored_fragility_curve.json"), {}, {}, 0.2619967240482869),
    (get_fragility_set("refactored_fragility_curve.json"), {"surgeLevel": 6, "waveHeight": 4}, {}, 1.0),
    (get_fragility_set("refactored_fragility_curve.json"), {"waveHeight": 4}, {}, 1.0),
    (get_fragility_set("refactored_fragility_curve.json"), {"surgeLevel": 6}, {}, 0.9999999950124077),
    (get_remote_fragility_set("606221fe618178207f6608a1"),
     {"waveHeight": 1.1111, "surgeLevel": 3},
     {"clearance": 4, "span_mass": 12, "g_elev": 0.2},
     0.142618908),
    # test case sensitivity
    (get_remote_fragility_set("606221fe618178207f6608a1"),
     {"WAVEheight": 1.1111, "sURgeLEVEL": 3},
     {"CLEARANCE": 4, "span_maSS": 12, "g_ELEV": 0.2},
     0.142618908),
    (get_fragility_set("fragility_curves/PeriodStandardFragilityCurve_refactored.json"), {"0.2 sec Sa": 4}, {},
     0.9905435183),
    # test liquefaction
    (get_remote_fragility_set("5b47bcce337d4a37755e0c85"),
     {"pga": 0.314128903},
     {"inventory_type": "bridge"},
     0.8097974088),
])
def test_calculate_limit_state_probability(fragility_set, hazard_values, args, expected):
    result = fragility_set.calculate_limit_state(hazard_values, **args)
    assert np.isclose(result["LS_0"], expected)


