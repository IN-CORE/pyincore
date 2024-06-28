# Copyright (c) 2018 University of Illinois and others. All rights reserved.

# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import sys
import random


class Solution:
    """Abstract solution. To be implemented."""

    def __init__(self, num_objectives):
        """Constructor. Parameters: number of objectives."""
        self.num_objectives = num_objectives
        self.objectives = []
        for _ in range(num_objectives):
            self.objectives.append(None)
        self.attributes = []
        self.rank = sys.maxsize
        self.distance = 0.0

        self.chromos_fitness = {}
        self.sch = {}

    def __rshift__(self, other):
        """True if this solution dominates the other (">>" operator)."""
        dominates = False

        for i in range(len(self.objectives)):
            if self.objectives[i] > other.objectives[i]:
                return False

            elif self.objectives[i] < other.objectives[i]:
                dominates = True

        return dominates

    def __lshift__(self, other):
        """True if this solution is dominated by the other ("<<" operator)."""
        return other >> self


def crowded_comparison(s1, s2):
    """Compare the two solutions based on crowded comparison.

    Args:
        s1 (obj): One chromosome.
        s2 (obj): Another chromosome.

    Returns:
        float: A comparison value.

    """
    if s1.rank < s2.rank:
        return 1

    elif s1.rank > s2.rank:
        return -1

    elif s1.distance > s2.distance:
        return 1

    elif s1.distance < s2.distance:
        return -1

    else:
        return 0


class NSGAII:
    """Implementation of NSGA-II algorithm."""

    current_evaluated_objective = 0

    def __init__(self, num_objectives, mutation_rate=0.1, crossover_rate=1.0):
        """Constructor.

        Args:
            num_objectives (obj): Number of objectives.
            mutation_rate (float): Mutation rate (default value 10%).
            crossover_rate (float): Crossover rate (default value 100%)..

        """
        self.num_objectives = num_objectives
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate

        random.seed(100)

    def run(self, p, population_size, num_generations):
        """Run NSGA-II.

        Args:
            p (obj): A set of chromosomes (population).
            population_size (obj): A population size.
            num_generations (obj): A number of generations.

        Returns:
            list: First front of Pareto front.

        """
        for s in p:
            s.evaluate_solution(0)

        first_front = []
        for i in range(num_generations):
            r = []
            r.extend(p)

            fronts = self.fast_nondominated_sort(r)

            del p[:]

            for front in fronts.values():
                if len(front) == 0:
                    break

                self.crowding_distance_assignment(front)
                p.extend(front)

                if len(p) >= population_size:
                    break

            self.sort_crowding(p)

            if len(p) > population_size:
                del p[population_size:]

            first_front = list(fronts.values())[0]

        return first_front

    @staticmethod
    def sort_ranking(p):
        """Run sort the sort of chromosomes according to their ranks.

        Args:
            p (obj): A set of chromosomes (population).

        """
        for i in range(len(p) - 1, -1, -1):
            for j in range(1, i + 1):
                s1 = p[j - 1]
                s2 = p[j]

                if s1.rank > s2.rank:
                    p[j - 1] = s2
                    p[j] = s1

    @staticmethod
    def sort_objective(p, obj_idx):
        """Run sort the chromosome based on their objective value.

        Args:
            p (obj): A set of chromosomes (population).
            obj_idx (int): The index of objective function.

        """
        for i in range(len(p) - 1, -1, -1):
            for j in range(1, i + 1):
                s1 = p[j - 1]
                s2 = p[j]

                if s1.objectives[obj_idx] > s2.objectives[obj_idx]:
                    p[j - 1] = s2
                    p[j] = s1

    @staticmethod
    def sort_crowding(p):
        """Run calculate the crowding distance of adjacent two chromosome in a front level.

        Args:
            p (obj): A set of chromosomes (population).

        """
        for i in range(len(p) - 1, -1, -1):
            for j in range(1, i + 1):
                s1 = p[j - 1]
                s2 = p[j]

                if crowded_comparison(s1, s2) < 0:
                    p[j - 1] = s2
                    p[j] = s1

    def make_new_pop(self, p):
        """Make new population Q, offspring of P.

        Args:
            p (obj): A set of chromosomes (population).

        Returns:
            list: Offspring.

        """
        q = []

        while len(q) != len(p):
            selected_solutions = [None, None]

            while selected_solutions[0] == selected_solutions[1]:
                for i in range(2):
                    s1 = random.choice(p)
                    s2 = s1
                    while s1 == s2:
                        s2 = random.choice(p)

                    if crowded_comparison(s1, s2) > 0:
                        selected_solutions[i] = s1

                    else:
                        selected_solutions[i] = s2

            if random.random() < self.crossover_rate:
                child_solution = selected_solutions[0].crossover(selected_solutions[1])

                if random.random() < self.mutation_rate:
                    child_solution.mutate()

                child_solution.evaluate_solution(0)

                q.append(child_solution)

        return q

    @staticmethod
    def fast_nondominated_sort(p):
        """Discover Pareto fronts in P, based on non-domination criterion.

        Args:
            p (obj): A set of chromosomes (population).

        Returns:
            dict: Fronts.

        """
        fronts = {}

        s = {}
        n = {}
        for i in p:
            s[i] = []
            n[i] = 0

        fronts[1] = []

        for pk in p:
            for qk in p:
                if pk == qk:
                    continue

                if pk >> qk:
                    s[pk].append(qk)

                elif pk << qk:
                    n[pk] += 1

            if n[pk] == 0:
                fronts[1].append(pk)

        i = 1
        while len(fronts[i]) != 0:
            next_front = []
            for r in fronts[i]:
                for j in s[r]:
                    n[j] -= 1
                    if n[j] == 0:
                        next_front.append(j)

            i += 1
            fronts[i] = next_front

        return fronts

    def crowding_distance_assignment(self, front):
        """Assign a crowding distance for each solution in the front.

        Args:
            front (dict): A set of chromosomes in the front level.

        """
        for p in front:
            p.distance = 0

        for obj_index in range(self.num_objectives):
            self.sort_objective(front, obj_index)

            front[0].distance = float("inf")
            front[len(front) - 1].distance = float("inf")

            for i in range(1, len(front) - 1):
                front[i].distance += front[i + 1].distance - front[i - 1].distance
