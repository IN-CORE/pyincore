import math
import collections
import scipy.stats as st
from pyincore import AnalysisUtil

class LifelineUtil:
    """
        Utility methods for analysis
    """

    @staticmethod
    def compute_limit_state_probability(fragility_curves, hazard_val, yvalue,
                                        std_dev):
        ls_probs = collections.OrderedDict()
        for fragility in fragility_curves:
            ls_probs['ls_'+fragility['description'].lower()] = \
                AnalysisUtil.compute_cdf(fragility, hazard_val, std_dev)
        return ls_probs

    @staticmethod
    def compute_damage_intervals(ls_probs):
        dmg_intervals = collections.OrderedDict()
        #['none', 'slight-mod', 'mod-extens', 'ext-comple', 'complete']
        dmg_intervals['none'] = 1 - ls_probs['ls_slight']
        # what happens when this value is negative ie, moderate > slight
        dmg_intervals['slight-mod'] = ls_probs['ls_slight'] - \
                                      ls_probs['ls_moderate']
        dmg_intervals['mod-extens'] = ls_probs['ls_moderate'] -\
                                      ls_probs['ls_extensive']
        dmg_intervals['ext-comple'] = ls_probs['ls_extensive'] - \
                                      ls_probs['ls_complete']
        dmg_intervals['complete'] = ls_probs['ls_complete']

        return dmg_intervals


    @staticmethod
    def adjustLimitStatesForPGD(limit_states, pgd_limit_states):


        adj_limit_states = collections.OrderedDict()

        for key, value in limit_states.items():
            adj_limit_states[key] = limit_states[key] + pgd_limit_states[key] - \
                                   (limit_states[key]*pgd_limit_states[key])

        return adj_limit_states

