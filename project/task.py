"""Class that represents a task."""

from math import ceil
from typing import Callable, Optional

from utils import UniqueId


# pylint: disable=too-few-public-methods
class TaskId(UniqueId):
    """A class to make unique task IDs."""


# The error management for this function could be improved maybe
# pylint: disable=too-many-arguments
def general_weight_fun(
    _: int,
    n_coloc_days: float,
    min_prop: float = 0,
    min_nb_coloc: int = 0,
    weight_per_coloc: Optional[float] = None,
    total_weight: Optional[float] = None,
) -> tuple[int, float]:
    """
    Return the number of colocs needed for one task and how tedious it is.

    Uncurrified version. Should be a very common form for this kind of functions.
    The returned tediousness is per coloc.
    """
    n_virt_coloc = n_coloc_days / 7
    coloc_needed = max(1, int(ceil(min_prop * n_virt_coloc)), min_nb_coloc)
    match isinstance(weight_per_coloc, float), isinstance(total_weight, float):
        case True, False:
            weight = n_virt_coloc * weight_per_coloc / coloc_needed  # type: ignore
        case False, True:
            weight = total_weight / coloc_needed  # type: ignore
        case _:
            raise ValueError(
                "Expected weight_per_coloc xor total_weight to be provided, "
                "got none of them or the 2 of them"
            )
    return coloc_needed, weight


def weight_fun(
    proportional: bool = True,
    min_prop: float = 0,
    min_nb_coloc: int = 0,
    weight_per_coloc: Optional[float] = None,
    total_weight: Optional[float] = None,
) -> Callable[[int, float], tuple[int, float]]:
    """
    Return a function used to compute the number of coloc and the weight associated to one task.

    Args:
        min_prop (float): In the interval [0, 1]. Minimum proportion of the coloc needed to
            perform the task. At the end the true number of coloc needed is computed
            relatively to the number of coloc * days, in the week.
        proportional (bool): If the total weight of the task is proportional to the number of
            colocs here at the coloc.
        weight_per_coloc (float): Weight per coloc. If proportional is False, then it is also
            the total weight.
    """
    if proportional:
        if weight_per_coloc is None:
            raise ValueError(
                "Task function proportional but no weight per coloc provided."
            )
        if total_weight is not None:
            raise ValueError("Task function proportional but total weight provided.")
    else:
        if weight_per_coloc is not None:
            raise ValueError(
                "Task function not proportional but weight per coloc provided."
            )
        if total_weight is None:
            raise ValueError(
                "Task function proportional but total weight not provided."
            )
    return lambda _, n_coloc_days: general_weight_fun(
        _,
        n_coloc_days=n_coloc_days,
        min_prop=min_prop,
        min_nb_coloc=min_nb_coloc,
        weight_per_coloc=weight_per_coloc,
        total_weight=total_weight,
    )


def need_weekend(available_days: list[bool]) -> bool:
    """Return true if the week-end is available in the available days defined by the argument."""
    return available_days[-1] and available_days[-2]


def less_than_n_consecutive_days_absent(
    available_days: list[bool], n_days: int
) -> bool:
    """Return True if the available days contain strictly less than n consecutive absent days."""
    absent_days: int = 0
    for day in available_days:
        if day:
            absent_days = 0
        else:
            absent_days += 1
            if absent_days >= n_days:
                return False
    return True


class Task:
    """
    Represents a task.

    Attributes:
        name (str): Name of the task.
        weight (Callable[[int, float], tuple[int, float]]):
            Args:
                The number of colocs here at the coloc
                The number of colocs * days in the week for which we try to find a planning.
            Returns:
                The number of colocs needed to do this task.
                How tedious this task is for each coloc that has to do it.
        possible_within (Callable[[list[bool]], bool]): Takes a list of
            bool representing the days of availability of some coloc ([is_availbale_monday,
            is_available_tuesday, ... , is_available_sunday]) as argument, and returns
            True if the task can be done by this coloc, False otherwise.
    """

    def __init__(
        self,
        name: str,
        weight: Callable[[int, float], tuple[int, float]],
        possible_within: Callable[[list[bool]], bool],
    ) -> None:
        """Initialize a task with some standard weight function."""
        self.name = name
        self.weight = weight
        self.prossible_within = possible_within

    def __str__(self):
        """Return a string representation of the task."""
        raise NotImplementedError("")

    def can_be_made_by(self, coloc):
        """Return True if the task can be made by `coloc`."""
        raise NotImplementedError("")

    @classmethod
    def one_shot_fixed_weight(
        cls, name: str, total_weight: float, min_prop: float
    ) -> "Task":
        """Return a one-shot task with fixed weight."""
        weight = weight_fun(
            proportional=False,
            min_prop=min_prop,
            min_nb_coloc=1,
            total_weight=total_weight,
        )
        return Task(name=name, weight=weight, possible_within=any)

    @classmethod
    def one_shot_variable_weight(
        cls, name: str, weight_per_coloc: float, min_prop: float
    ) -> "Task":
        """Return a one-shot task with a weight growing with the number of colocs."""
        weight = weight_fun(
            proportional=True,
            min_prop=min_prop,
            min_nb_coloc=1,
            weight_per_coloc=weight_per_coloc,
        )
        return Task(name=name, weight=weight, possible_within=any)

    @classmethod
    def regular_fixed_weight(
        cls, name: str, total_weight: float, min_prop: float, each_n_days: int
    ):
        """Return a regular task with fixed weight."""
        weight = weight_fun(
            proportional=False,
            min_prop=min_prop,
            min_nb_coloc=1,
            total_weight=total_weight,
        )
        return Task(
            name=name,
            weight=weight,
            possible_within=lambda av_days: less_than_n_consecutive_days_absent(
                av_days, each_n_days
            ),
        )

    @classmethod
    def regular_variable_weight(
        cls, name: str, weight_per_coloc: float, min_prop: float, each_n_days: int
    ) -> "Task":
        """Return a regular task with a weight growing with the number of colocs."""
        weight = weight_fun(
            proportional=False,
            min_prop=min_prop,
            min_nb_coloc=1,
            weight_per_coloc=weight_per_coloc,
        )
        return Task(
            name=name,
            weight=weight,
            possible_within=lambda av_days: less_than_n_consecutive_days_absent(
                av_days, each_n_days
            ),
        )
