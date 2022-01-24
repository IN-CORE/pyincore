import json
import os
import collections

import numpy
import pytest

from pyincore import globals as pyglobals, FragilityCurveSet, RepairCurveSet,  RestorationCurveSet, AnalysisUtil
import numpy as np


def test_fragility_set_small_overlap():
    fragility_set = get_fragility_set("fragility_curve.json")

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
    fragility_set = get_fragility_set("fragility_curve.json")
    assert len(fragility_set.fragility_curves) != 0


def get_repair_set(repair_dir: str):
    with open(os.path.join(pyglobals.TEST_DATA_DIR, repair_dir), 'r', encoding='utf-8') as f:
        repair_curveset = json.load(f)
    repair_set = RepairCurveSet(repair_curveset)
    return repair_set

def get_remote_repair_set(repair_id: str):
    dfr3svc = pytest.repairsvc
    repair_set = RepairCurveSet(dfr3svc.get_dfr3_set(repair_id))
    return repair_set

def get_restoration_set(restoration_dir: str):
    with open(os.path.join(pyglobals.TEST_DATA_DIR, restoration_dir), 'r', encoding='utf-8') as f:
        restoration_curveset = json.load(f)
    restoration_set = RestorationCurveSet(restoration_curveset)
    return restoration_set

@pytest.mark.parametrize("fragility_set,hazard_values,args,expected", [
    (get_fragility_set("fragility_curve.json"), {}, {}, 0.2619967240482869),
    (get_fragility_set("fragility_curve.json"), {"surgeLevel": 6, "waveHeight": 4}, {}, 1.0),
    (get_fragility_set("fragility_curve.json"), {"waveHeight": 4}, {}, 1.0),
    (get_fragility_set("fragility_curve.json"), {"surgeLevel": 6}, {}, 0.9999999950124077),
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
    print(result)
    assert np.isclose(result["LS_0"], expected)


@pytest.mark.parametrize("repair_set,args,expected", [
    (get_repair_set("repairset.json"), {"repair_time": [3.5, 1.2]}, 2),
    (get_repair_set("repairset.json"), {"repair_time": 80}, 0.9943516689414926),
    (get_remote_repair_set("60edf9a4fc0f3a7af53a2194"), {"repair_time": [3.5, 1.2]}, 2)
])
def test_calculate_repair_rates(repair_set, args, expected):
    result = repair_set.calculate_repair_rates(**args)
    if type(result["PF_0"]) == numpy.ndarray:
        assert len(result["PF_0"]) == expected
    elif type(result["PF_0"]) == numpy.float64:
        assert result["PF_0"] == expected
    else:
        assert False


@pytest.mark.parametrize("repair_set,args,expected", [
    (get_repair_set("repairset.json"), {"repair_time": [0.5, 0.2]}, 2),
    (get_repair_set("repairset.json"), {"repair_time": 0.67}, 27.50466741611462)
])
def test_calculate_inverse_repair_rates(repair_set, args, expected):
    result = repair_set.calculate_inverse_repair_rates(**args)
    print(result)
    if type(result["PF_0"]) == numpy.ndarray:
        assert len(result["PF_0"]) == expected
    elif type(result["PF_0"]) == numpy.float64:
        assert result["PF_0"] == expected
    else:
        assert False


@pytest.mark.parametrize("restoration_set,args,expected", [
    (get_restoration_set("restorationset.json"), {"time": [3.5, 1.2]}, 2),
    (get_restoration_set("restorationset.json"), {"time": 80}, 0.9943516689414926)
])
def test_calculate_restoration_rates(restoration_set, args, expected):
    result = restoration_set.calculate_restoration_rates(**args)
    if type(result["PF_0"]) == numpy.ndarray:
        assert len(result["PF_0"]) == expected
    elif type(result["PF_0"]) == numpy.float64:
        assert result["PF_0"] == expected
    else:
        assert False
