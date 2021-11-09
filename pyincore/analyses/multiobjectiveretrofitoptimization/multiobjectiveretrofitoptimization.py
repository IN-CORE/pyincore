# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import BaseAnalysis
import sys
import os
import pandas as pd
import numpy as np
import csv
import time
import matplotlib.pyplot as plt
#from gurobipy import *
import scipy.interpolate as interp
import matplotlib as mpl
from mpl_toolkits.mplot3d import Axes3D
from pandas import DataFrame
from pyomo.environ import ConcreteModel, Set, Var, Param, Objective, Constraint
#from pyomo.environ import quicksum, minimize, maximize, NonNegativeReals, Any
from pyomo.environ import sum_product
import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory, SolverManagerFactory
from pyomo.opt import SolverStatus, TerminationCondition
from pyomo.util.infeasible import log_infeasible_constraints
#import palettable.colorbrewer
import zipfile
import getopt
import glob

class MultiObjectiveRetrofitOptimization(BaseAnalysis):
    """
        This analysis computes a series of linear programming models for single- and multi-objective
        optimization related to the effect of extreme weather on a community in terms of three objective functions.
        The three objectives used in this program are to minimize economic loss, minimize population dislocation,
        and maximize building functionality. The computation proceeds by iteratively solving constrained linear
        models using epsilon steps.

        The output of the computation a collection of optimal resource allocations.

        Contributors
            | Science: Charles Nicholson, Yunjie Wen
            | Implementation: Dale Cochran , Tarun Adluri , Jorge Duarte, Santiago Núñez-Corrales,
                              and NCSA IN-CORE Dev Team

        Related publications


        Args:
            incore_client (IncoreClient): Service authentication.
        """

    def __init__(self, incore_client):
        super(MultiObjectiveRetrofitOptimization, self).__init__(incore_client)

    def run(self):
        """Execute the multiobjective retrofit optimization analysis using parameters and input data."""
        # Read parameters
        model_solver = self.get_parameter('model_solver')
        num_epsilon_steps = self.get_parameter('num_epsilon_steps')

        budget_available = 0.2
        if self.get_parameter('max_budget') != 'default':
            budget_available = self.get_parameter('budget_available')

        inactive_submodels = []

        in_subm = self.get_parameter('inactive_submodels')

        if in_subm is not None:
            inactive_submodels = in_subm

        scaling_factor = 1.0
        if self.get_parameter('scale_data'):
            scaling_factor = self.get_parameter('scaling_factor')

        self.multiobjective_retrofit_optimization_model(model_solver, num_epsilon_steps, budget_available,
                                                        scaling_factor, inactive_submodels)


    def multiobjective_retrofit_optimization_model(self, model_solver, num_epsilon_steps, budget_available,
                                                   scaling_factor, inactive_submodels):
        """Performs the computation of the model.

        Args:
            model_solver (str): model solver to use for analysis
            num_epsilon_steps (int): number of epsilon values for the multistep optimization algorithm
            budget_available (float): budget constraint of the optimization analysis
            scaling_factor (float): scaling factor for Q and Sc matrices
            inactive_submodels (list): submodels to avoid during the computation
        """
        pass

    def get_spec(self):
        """Get specifications of the multiobjective retrofit optimization model.

        Returns:
            obj: A JSON object of specifications of the multiobjective retrofit optimization model.

        """
        return {
            'name': 'multiobjective-retrofit-optimization',
            'description': 'Multiobjective retrofit optimization model',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'Result CSV dataset name',
                    'type': str
                },
                {
                    'id': 'model_solver',
                    'required': True,
                    'description': 'Choice of the model solver to use',
                    'type': str
                },
                {
                    'id': 'num_epsilon_steps',
                    'required': True,
                    'description': 'Number of epsilon values to evaluate',
                    'type': int
                },
                {
                    'id': 'max_budget',
                    'required': True,
                    'description': 'Selection of maximum possible budget',
                    'type': str
                },
                {
                    'id': 'budget_available',
                    'required': False,
                    'description': 'Custom budget value',
                    'type': int
                },
                {
                    'id': 'inactive_submodels',
                    'required': False,
                    'description': 'Identifier of submodels to inactivate during analysis',
                    'type': [int]
                },
                {
                    'id': 'scale_data',
                    'required': True,
                    'description': 'Choice for scaling data',
                    'type': bool
                },
                {
                    'id': 'scaling_factor',
                    'required': False,
                    'description': 'Custom scaling factor',
                    'type': float
                },
            ],
            'input_datasets': [
                {
                    'id': 'population_dislocation_block',
                    'required': True,
                    'description': 'A csv file with population dislocation result '
                                   'aggregated to the block group level',
                    'type': 'incore:popDislocation'
                },
            ],
            'output_datasets': [
                {
                    'id': 'ds_result',
                    'parent_type': 'xxxx',
                    'description': 'A csv file',
                    'type': 'incore:multiobjectiveRetrofitOptimization'
                }
            ]
        }
