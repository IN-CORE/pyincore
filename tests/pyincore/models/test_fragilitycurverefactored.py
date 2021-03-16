import json
import os
import collections

import pytest

from pyincore import globals as pyglobals, FragilityCurveSet


def test_fragility_set_small_overlap():
    fragility_set = get_fragility_set("refactored_fragility_curve.json")

    # Test Case 1 - single overlap
    output = collections.OrderedDict([("LS_0", 0.9692754643), ("LS_1", 0.0001444974), ("LS_2", 0.0004277083)])
    damage = fragility_set._3ls_to_4ds(output)
    assert damage['DS_0'] == 0.0307245357 and damage['DS_1'] == 0.968847756 and damage['DS_2'] == 0.0 and \
           damage['DS_3'] == 0.0004277083

    # Test Case 1 - double overlap
    output = collections.OrderedDict([("LS_0", 0.98), ("LS_1", 0.99), ("LS_2", 1.0)])
    damage = fragility_set._3ls_to_4ds(output)
    assert damage['DS_0'] == 0.0 and damage['DS_1'] == 0.0 and damage['DS_2'] == 0.0 and damage['DS_3'] == 1.0


def get_fragility_set(fragility_dir: str):
    with open(os.path.join(pyglobals.TEST_DATA_DIR, fragility_dir), 'r') as f:
        fragility_curve = json.load(f)
    fragility_set = FragilityCurveSet(fragility_curve)
    return fragility_set


def test_create_fragility_set():
    fragility_set = get_fragility_set("refactored_fragility_curve.json")
    assert fragility_set.id == "5f6ccf67de7b566bb71b202d" and len(fragility_set.fragility_curves) != 0


@pytest.mark.parametrize("hazard_values,expected", [
    ({}, 0.2619967240482869),
    ({"surgeLevel": 6, "waveHeight": 4}, 1.0),
    ({"waveHeight": 4}, 1.0),
    ({"surgeLevel": 6}, 0.9999999950124077),
])
def test_calculate_limit_state_probability(hazard_values, expected):
    fragility_set = get_fragility_set("refactored_fragility_curve.json")
    result = fragility_set.calculate_limit_state_refactored_w_conversion(hazard_values)
    assert result["LS_0"] == expected


@pytest.mark.parametrize("curve, hazard_val, refactored_curve, hazard_val_refactored, num_stories", [
    ("fragility_curves/ConditionalStandardFragilityCurve_original.json", 4,
     "fragility_curves/ConditionalStandardFragilityCurve_refactored.json", {"Vmax": 4}, 1),
    ("fragility_curves/ParametricFragilityCurve_original.json", 4,
     "fragility_curves/ParametricFragilityCurve_refactored.json", {"PGA": 4}, 1),
    ("fragility_curves/PeriodBuildingFragilityCurve_original.json", 0.05,
     "fragility_curves/PeriodBuildingFragilityCurve_refactored.json", {"Sa": 0.05}, 6),
    ("fragility_curves/PeriodStandardFragilityCurve_original.json", 4,
     "fragility_curves/PeriodStandardFragilityCurve_refactored.json", {"0.2 sec Sa": 4}, 6),
    ("fragility_curves/StandardFragilityCurve_original.json", 4,
     "fragility_curves/StandardFragilityCurve_refactored.json", {"momentumFlux": 4}, 1),
])
def test_curves_results(curve, hazard_val, refactored_curve, hazard_val_refactored, num_stories):
    fragility_set = get_fragility_set(curve)
    refactored_fragility_set = get_fragility_set(refactored_curve)

    # add period if applicable

    building_period = fragility_set.fragility_curves[0].get_building_period(num_stories)
    if len(fragility_set.fragility_curves) <= 3:
        result = fragility_set.calculate_limit_state_w_conversion(hazard_val, period=building_period)
        refactored_result = refactored_fragility_set.calculate_limit_state_refactored_w_conversion(
            hazard_val_refactored,
            num_stories=num_stories)

        assert result == refactored_result

    # no longer handle fragility curves > 3, test if can catch this error
    else:
        with pytest.raises(ValueError):
            refactored_result = refactored_fragility_set.calculate_limit_state_refactored_w_conversion(
                hazard_val_refactored,
                num_stories=1)
