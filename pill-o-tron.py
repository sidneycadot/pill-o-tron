#! /usr/bin/env python3

"""The Pill-O-Tron tool calculates optimal periodic pill dosage schedules.

Given a set of allowable daily doses, and a maximum period for a dosage schedule, find optimal dosage schedules
to reach all possible mean dosage values.

For many mean values, multiple dosage schedules are possible. We prune them by applying the following rules:

(1) Dosage schedules with lower standard deviation are preferred; so we reject all dosage schedules where a
    schedule with the same mean but higher standard deviation exists.

(2) For dosage schedules with the same mean and standard deviation, we prefer ones that are shorter (lower period).

For a given mean, the lowest standard-deviation schedule, with the shortest period, isa considered "optimal".
"""

import argparse
from fractions import Fraction
from typing import NamedTuple
import math


def generate_partitions(num_stacks: int, total: int) -> list[tuple[int]]:
    """Generate integer partitions of 'total' into 'num_stacks'.

    This returns a list of tuples.
    Each tuple contains "num_stacks" elements.
    Each tuple element is a non-negative integer.
    The sum of each tuple is "total".
    """

    if num_stacks == 0:
        if total == 0:
            return [()]
        else:
            return []

    solutions = []

    for last_stack in range(0, total + 1):
        stacks_before_solutions = generate_partitions(num_stacks - 1, total - last_stack)
        solutions.extend(stacks_before_solution + (last_stack, ) for stacks_before_solution in stacks_before_solutions)

    return solutions


def fraction_to_dosage_string(dosage: Fraction) -> str:
    """Represent a fraction as a dosage string."""
    if dosage.denominator == 1 and 0 <= dosage.numerator <= 9:
        # Represent single-digit integer doses by just the integer.
        return str(dosage.numerator)
    elif dosage == Fraction(1, 2):
        # Dutch: "half".
        return "h"
    elif dosage == Fraction(1, 4):
        # Dutch: "kwart".
        return "k"
    elif dosage == Fraction(3, 2):
        # Dutch: "anderhalf"
        return "a"
    else:
        # All other dosages are printed inside parentheses.
        return "({})".format(dosage)


def possible_dosages_to_string(possible_dosages: list[Fraction]) -> str:
    return ",".join(str(float(dosage)) for dosage in possible_dosages)

class DosageSchedule(NamedTuple):
    """A dosage schedule."""

    possible_dosages: list[Fraction]
    counts: tuple[int]

    def period(self) -> int:
        """Return the period, in days."""
        return sum(self.counts)

    def mean(self) -> float:
        """Return the mean daily dose, in doses/day."""
        return float(sum(dosage * count for (dosage, count) in zip(self.possible_dosages, self.counts)) / self.period())

    def stddev(self) -> float:
        """Return the standard deviation of the daily dose, in doses/day."""
        mean = self.mean()
        variance = sum((dosage - mean) ** 2 * count for (dosage, count) in zip(self.possible_dosages, self.counts)) / self.period()
        return math.sqrt(variance)

    def schedule_as_string(self) -> str:
        """Return the dosage schedule as a string."""
        specs = []
        for (dosage, count) in zip(self.possible_dosages, self.counts):
            if count != 0:
                spec = count * fraction_to_dosage_string(dosage)
                specs.append(spec)
        return "".join(specs)


def show_optimal_schedules_plot(possible_dosages: list[Fraction], max_period: int, optimal_schedules: list[DosageSchedule]) -> None:
    """Show a plot of all optimal schedules."""
    import matplotlib.pyplot as plt
    mean = [schedule.mean() for schedule in optimal_schedules]
    stddev = [schedule.stddev() for schedule in optimal_schedules]
    period = [schedule.period() for schedule in optimal_schedules]

    plt.scatter(mean, stddev, c=period)
    plt.title("\n{} optimal schedules\npossible daily doses: {{{}}}; max period: {}\n(colors correspond to schedule period in days)\n".format(len(optimal_schedules), possible_dosages_to_string(possible_dosages), max_period))
    plt.xlabel("mean dose [pills/day]")
    plt.ylabel("standard deviation [pills/day]")
    cbar = plt.colorbar()
    plt.grid()
    plt.gcf().set_size_inches(12, 8)

    cbar.ax.yaxis.get_major_locator().set_params(integer=True)

    plt.show()


def main():
    """Main program for the Pill-O-Tron tool."""

    default_possible_daily_dosages="0,0.5,1,2"
    default_max_period = 21

    parser = argparse.ArgumentParser(description="The Pill-O-Tron tool calculates optimal periodic pill dosage schedules.")

    parser.add_argument("--possible-daily-dosages", "-d", default=default_possible_daily_dosages,
        help="possible daily dosages, in pills, separated by comma (default: {})".format(default_possible_daily_dosages))
    parser.add_argument("--max-period","-p",  type=int, default=default_max_period,
        help="max period, in days (default: {})".format(default_max_period))
    parser.add_argument("--show-plot", "-s", action="store_true", help="show optimal schedules plot")

    args = parser.parse_args()

    possible_dosages_as_floats = [float(dosage) for dosage in args.possible_daily_dosages.split(",")]

    possible_dosages = sorted(set(Fraction(round(dosage * 4), 4) for dosage in possible_dosages_as_floats))

    print("# Pill-O-Tron 1.0.3 - Copyright (c) 2023 by Sidney Cadot.")
    print("#")
    print("# Parameters:")
    print("#")
    print("#   --possible-daily-dosages:", possible_dosages_to_string(possible_dosages))
    print("#   --max-period: {}".format(args.max_period))
    print("#")

    # Enumerate all dosage schedules.

    print("# Enumerating all dosage schedules ...")

    schedules = []
    for period in range(1, args.max_period + 1):
        partitions = generate_partitions(len(possible_dosages), period)
        schedules.extend(DosageSchedule(possible_dosages, partition) for partition in partitions)

    print("# Possible dosage schedules found: {}.".format(len(schedules)))

    # Order schedules by mean.

    print("# Finding reachable mean daily dosages ...")

    schedules_by_mean = {}

    for schedule in schedules:
        mean = schedule.mean()

        if mean in schedules_by_mean:
            schedules_by_mean[mean].append(schedule)
        else:
            schedules_by_mean[mean] = [schedule]

    print("# Reachable mean daily dosages found: {}.".format(len(schedules_by_mean)))

    means_reachable = sorted(schedules_by_mean)

    # Find optimal schedules for each mean, by rejecting non-optimal ones.

    print("# Rejecting non-optimal dosage schedules ...")

    optimal_schedules = []
    for mean in means_reachable:
        schedules = schedules_by_mean[mean]

        # Lower standard deviation is more important than lower period, so we select for lowest standard deviation first.
        min_stddev = min(schedule.stddev() for schedule in schedules)
        schedules = [schedule for schedule in schedules if schedule.stddev() == min_stddev]

        # For schedules with the same mean and stddev, reject ones that are longer than necessary.
        min_period = min(schedule.period() for schedule in schedules)
        schedules = [schedule for schedule in schedules if schedule.period() == min_period]

        if len(schedules) != 1:
            print(schedules)
            raise RuntimeError("Found multiple dosage schedules with the same stdandard deviation and period.")

        schedule = schedules[0]
        optimal_schedules.append(schedule)

    print("# Done. Report for {} optimal dosage schedules follows:".format(len(optimal_schedules)))
    print()

    # Print optimal schedules.

    for schedule in optimal_schedules:

        print("mean {:10.6f}    stddev {:10.6f}    period {:6d}    schedule  {}".format(
            schedule.mean(),
            schedule.stddev(),
            schedule.period(),
            schedule.schedule_as_string()
        ))

    if args.show_plot:
        show_optimal_schedules_plot(possible_dosages, args.max_period, optimal_schedules)


if __name__ == "__main__":
    main()
