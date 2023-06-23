#! /usr/bin/env python3

"""Calculate optimal periodic pill dosage schedules."""

import argparse
from fractions import Fraction
from typing import NamedTuple
import math


def generate_partitions(num_stacks: int, total: int) -> list[tuple[int]]:
    """Generate partitions.

    This returns a list of tuples.
    Each tuple contains "num_stacks" elements.
    Each tuple element is a non-negative integer.
    The sum of each tople is "total".
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
    if dosage.denominator == 1:
        if 0 <= dosage.numerator <= 9:
            return str(dosage.numerator)
    elif dosage == Fraction(1, 2):
        return "h"
    elif dosage == Fraction(1, 4):
        return "k"
    elif dosage == Fraction(3, 2):
        return "a"

    raise ValueError("Unable to make daily dosage string for fraction {}".format(dosage))


class DosageSchedule(NamedTuple):
    possible_dosages: list[Fraction]
    counts: tuple[int]

    def period(self) -> int:
        return sum(self.counts)

    def mean(self) -> Fraction:
        return float(sum(dosage * count for (dosage, count) in zip(self.possible_dosages, self.counts)) / self.period())

    def stddev(self):
        mean = self.mean()
        variance = sum((dosage - mean) ** 2 * count for (dosage, count) in zip(self.possible_dosages, self.counts)) / self.period()
        return math.sqrt(variance)

    def schedule_string(self) -> str:
        specs = []
        for (dosage, count) in zip(self.possible_dosages, self.counts):
            if count != 0:
                spec = count * fraction_to_dosage_string(dosage)
                specs.append(spec)
        return "".join(specs)


def show_optimal_schedules_plot(optimal_schedules):
    import matplotlib.pyplot as plt
    mean = [schedule.mean() for schedule in optimal_schedules]
    stddev = [schedule.stddev() for schedule in optimal_schedules]
    period = [schedule.period() for schedule in optimal_schedules]
    plt.title("{} optimal schedules\n(colors correspond to period)".format(len(optimal_schedules)))
    plt.scatter(mean, stddev, c=period)
    plt.xlabel("mean")
    plt.ylabel("stddev")
    plt.colorbar()
    plt.grid()
    plt.show()


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--possible_daily_dosages", "-d", default="0,0.5,1,2", help="possible daily dosages, in pills, separated by comma")
    parser.add_argument("--max-period","-p",  type=int, default="21", help="max period, in days")
    parser.add_argument("--show-plot", "-s", action="store_true", help="show optimal schedules plot")

    args = parser.parse_args()

    possible_dosages_as_floats = [float(dosage) for dosage in args.possible_daily_dosages.split(",")]

    possible_dosages = sorted(set(Fraction(round(pills * 4), 4) for pills in possible_dosages_as_floats))

    # Enumerate all dosage schedules.

    print("Enumerating all dosage schedules ...")

    schedules = []
    for period in range(1, args.max_period + 1):
        partitions = generate_partitions(len(possible_dosages), period)
        schedules.extend(DosageSchedule(possible_dosages, partition) for partition in partitions)

    print("{} dosage schedules found.".format(len(schedules)))

    # Order schedules by mean.

    schedules_by_mean = {}

    for schedule in schedules:
        mean = schedule.mean()

        if mean in schedules_by_mean:
            schedules_by_mean[mean].append(schedule)
        else:
            schedules_by_mean[mean] = [schedule]

    # Find optimal schedules for each mean, by rejecting non-optimal ones.

    print("Rejecting non-optimal schedules ...")

    means_reachable = sorted(schedules_by_mean)

    optimal_schedules = []
    for mean in means_reachable:
        schedules = schedules_by_mean[mean]

        # Lower standard deviation is more important than lower period, so we select for lowest standard deviation first.
        min_stddev =min(schedule.stddev() for schedule in schedules)
        schedules = [schedule for schedule in schedules if schedule.stddev() == min_stddev]

        # For schedules with the same mean and stddev, reject ones that are longer than necessary.
        min_period = min(schedule.period() for schedule in schedules)
        schedules = [schedule for schedule in schedules if schedule.period() == min_period]

        if len(schedules) != 1:
            print(schedules)
            raise RuntimeError("Found multiple schedules with the same stdandard deviation and period.")

        schedule = schedules[0]
        optimal_schedules.append(schedule)

    print("{} optimal dosage schedules found.".format(len(optimal_schedules)))

    # Present optimal solutions.

    for schedule in optimal_schedules:

        print("mean {:10.6f}    stddev {:10.6f}    period {:6d}    schedule  {}".format(
            schedule.mean(),
            schedule.stddev(),
            schedule.period(),
            schedule.schedule_string()
        ))

    if args.show_plot:
        show_optimal_schedules_plot(optimal_schedules)


if __name__ == "__main__":
    main()
