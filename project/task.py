"""Class that represents a task."""

from math import ceil
from typing import Callable, Union


def general_weight_fun(
    _: int,
    n_coloc_days: float,
    min_prop: float,
    proportional: bool = True,
    weight_per_coloc: Union[float, None] = None,
    total_weight: Union[float, None] = None,
) -> tuple[int, float]:
    """
    Return the number of colocs needed for one task and how tedious it is.

    Uncurrified version. Should be a very common form for this kind of functions.
    The returned tediousness is per coloc.
    """
    n_virt_coloc = n_coloc_days / 7
    coloc_needed = max(1, int(ceil(min_prop * n_virt_coloc)))
    match proportional:
        case True:
            assert isinstance(weight_per_coloc, float)  # nosec
            weight = n_virt_coloc * weight_per_coloc / coloc_needed
        case False:
            assert isinstance(total_weight, float)  # nosec
            weight = total_weight / coloc_needed
    return coloc_needed, weight


def weight_fun(
    min_prop: float,
    proportional: bool = True,
    weight_per_coloc: Union[float, None] = None,
    total_weight: Union[float, None] = None,
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
    match proportional:
        case True:
            if weight_per_coloc is None:
                raise ValueError(
                    "Task function proportional but no weight per coloc provided."
                )
            if total_weight is not None:
                raise ValueError(
                    "Task function proportional but total weight provided."
                )
        case False:
            if weight_per_coloc is not None:
                raise ValueError(
                    "Task function not proportional but weight per coloc provided."
                )
            if total_weight is None:
                raise ValueError(
                    "Task function proportional but total weight not provided."
                )
        case _:
            raise ValueError(
                f"Expected type bool for argument 'proportional', got {proportional}."
            )

    return lambda _, n_coloc_days: general_weight_fun(
        _,
        n_coloc_days=n_coloc_days,
        min_prop=min_prop,
        proportional=proportional,
        weight_per_coloc=weight_per_coloc,
        total_weight=total_weight,
    )


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

    def __init__(self, name: str):
        """Initialize a task with some standard weight function."""
        raise NotImplementedError("")

    def __str__(self):
        """Return a string representation of the task."""
        raise NotImplementedError("")

    def can_be_made_by(self, coloc):
        """Return True if the task can be made by `coloc`."""
        raise NotImplementedError("")
