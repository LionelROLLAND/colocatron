"""Provide a class that represents the history of some specific task performed by some coloc."""

# import zoneinfo
from collections.abc import Iterable as ClassIterable
from datetime import date
from typing import Iterable as TypeIterable
from typing import Optional

from constants import ONE_DAY
from utils import period_type_error


class TaskHistory:
    """
    A class to store the history of some task relatively to some coloc.

    A bit similar to Presence.
    """

    class BeforeBeginError(ValueError):
        """Raised when trying to tell that the task was done on a day before self.__begin_on."""

    class NeverDoneError(ValueError):
        """
        Raised when asking for the last time the task was done.

        Raised if the task has never been done.
        """

    class UpdateLoadError(ValueError):
        """
        Raised when adding a date for the task.

        Raised if it would result in implicitly updating the load for that date.
        """

    unsafe_rm_date_error = ValueError(
        "Trying to delete a date from a task history such that it would then "
        "be impossible to retrieve the last time the task has been done."
    )

    def __init__(self) -> None:
        """Initialize an empty task history."""
        self.__ever_done: bool = False
        self.__begin_on: date = date(year=1, month=1, day=1)
        self.__n_until_begin: int = 0
        self.__load_until_begin: float = 0
        self.__last_time: date = date(year=9999, month=12, day=31)
        self.__dates: dict[date, float] = {}

    # Needs typing
    @classmethod
    def from_json_object(cls, json_obj):
        """Return a TaskHistory instance from an object extracted from a json."""
        raise NotImplementedError("Implement me !")

    # Needs typing
    def to_json_object(self):
        """Return an object that stores the data of the class and that can be put in a json."""
        raise NotImplementedError("Implement me !")

    def set_date_check(self, day: date) -> None:
        """Raise an error if a date cannot be added/removed for the date day."""
        if not isinstance(day, date):
            raise period_type_error(day)
        if day < self.__begin_on:
            raise self.BeforeBeginError(
                "Trying to set a date before when the dates recording start."
            )

    def add_date_check(self, day: date, load: float) -> None:
        """Raise an error if day cannot be added with load."""
        self.set_date_check(day)
        if day in self.__dates and load != self.__dates[day]:
            raise self.UpdateLoadError("Date already added with a different load.")

    def add_date(
        self,
        period: date | TypeIterable[date],
        load: float,
    ) -> None:
        """Add a period on which the task was done."""
        if not isinstance(load, float):
            raise TypeError(f"Expected load argument of type float, got {load}.")
        if isinstance(period, date):
            self.add_date_check(day=period, load=load)
            if not self.__ever_done:
                self.__last_time = period
                self.__ever_done = True
            elif period > self.__last_time:
                self.__last_time = period
            self.__dates.setdefault(period, load)
        elif isinstance(period, ClassIterable):
            length: int = sum(1 for _ in period)
            if length > 0:
                single_day_load = load / length
                for day in period:
                    self.add_date_check(day=day, load=load)
                potential_last_time = max(period)
                if not self.__ever_done:
                    self.__ever_done = True
                    self.__last_time = potential_last_time
                elif potential_last_time > self.__last_time:
                    self.__last_time = potential_last_time
                for day in period:
                    self.__dates.setdefault(day, single_day_load)
        else:
            raise period_type_error(period)

    @property
    def last_time(self) -> date:
        """Return self.__last_time if it makes sense."""
        if not self.__ever_done:
            raise self.NeverDoneError("The task has never been done.")
        return self.__last_time

    @property
    def ever_done(self) -> bool:
        """Return True if the task has ever been done."""
        return self.__ever_done

    def days_nb_until(self, day: date) -> int:
        """Return the number of days the task has been done until day."""
        return (
            sum(1 for _ in filter(lambda d: d <= day, self.__dates))
            + self.__n_until_begin
        )

    def load_until(self, day: date) -> float:
        """Return the total load until day."""
        return (
            sum(load if d <= day else 0 for d, load in self.__dates.items())
            + self.__load_until_begin
        )

    def rm_date_check(self, day: date) -> None:
        """Raise an error if day cannot be safely removed from self.__dates."""
        self.set_date_check(day)
        if (
            day == self.__last_time
            and self.__n_until_begin > 0
            and all(d == self.__last_time for d in self.__dates)
        ):
            raise self.unsafe_rm_date_error

    def rm_date(self, period: date | TypeIterable[date]):
        """Remove a period on which the task was done."""
        if isinstance(period, date):
            self.rm_date_check(period)
            del self.__dates[period]
            if period == self.__last_time:
                if len(self.__dates) > 0:
                    self.__last_time = max(self.__dates)
                else:
                    self.__ever_done = False
                    self.__last_time = date(year=9999, month=12, day=31)
        elif isinstance(period, ClassIterable):
            days_to_delete: set[date] = set()
            for day in period:
                self.set_date_check(day)
                days_to_delete.add(day)
            if (
                self.__last_time in days_to_delete
                and self.__n_until_begin > 0
                and all(day in days_to_delete for day in self.__dates)
            ):
                raise self.unsafe_rm_date_error
            for day in days_to_delete:
                del self.__dates[day]
            if self.__last_time in days_to_delete:
                if len(self.__dates) > 0:
                    self.__last_time = max(self.__dates)
                else:
                    self.__ever_done = False
                    self.__last_time = date(year=9999, month=12, day=31)

    def set_situation_check(
        self,
        until: date,
        n_days: int,
        last_time_between_start_and_until: Optional[date] = None,
        start: Optional[date] = None,
    ) -> None:
        """Raise an error if self.set_situation_on_period cannot be called with the same args."""
        if until < self.__begin_on:
            raise ValueError(
                "Trying to set global information until a date that is before "
                "the beginning of the precise task recording."
            )
        if last_time_between_start_and_until is None:
            if n_days > 0 and not self.__ever_done:
                raise ValueError(
                    "Trying to update an empty task history with global information "
                    "without specifying the last time the task was done."
                )
        else:
            if last_time_between_start_and_until > until:
                raise ValueError(
                    "Setting a last time in a period after the end of that period."
                )
            if n_days == 0:
                raise ValueError(
                    "Inconsistent call to TaskHistory.set_situation_on_period: "
                    "the number of days on a period is 0 even though "
                    'some date "last time" on that same period is provided, which '
                    "should at least count for one day."
                )
        if start is not None and start > until:
            raise ValueError(
                'End date ("until") sooner than start date in the method '
                "TaskHistory.set_situation_on_period."
            )
        if start is not None and start > self.__begin_on:
            raise ValueError(
                "Setting global information on a period such that it creates holes "
                "in the task history."
            )
        if (
            start is not None
            and start < self.__begin_on
            and self.__n_until_begin != 0
            and self.__load_until_begin != 0
        ):
            raise self.BeforeBeginError(
                "Trying to set global information starting before the beginning "
                "of the precise task recording for a task history that is such that "
                "there is already some history information for before the beginning "
                "of the precise recording."
            )

    # pylint: disable=too-many-arguments
    def set_situation_on_period(
        self,
        until: date,
        n_days: int,
        load: float,
        last_time_between_start_and_until: Optional[date] = None,
        start: Optional[date] = None,
    ) -> None:
        """
        Set the situation until day.

        Set the number of times the task has been done and the total load associated with
        these times.
        """
        self.set_situation_check(
            until=until,
            n_days=n_days,
            last_time_between_start_and_until=last_time_between_start_and_until,
            start=start,
        )
        if start is None:
            self.__n_until_begin = n_days
            self.__load_until_begin = load
        else:
            self.__n_until_begin += n_days
            self.__load_until_begin += load

        if last_time_between_start_and_until is not None:
            if self.__ever_done:
                if last_time_between_start_and_until > self.__last_time:
                    self.__last_time = last_time_between_start_and_until
            elif n_days > 0:
                self.__ever_done = True
                self.__last_time = last_time_between_start_and_until

        self.__begin_on = until + ONE_DAY
        days_to_delete: list[date] = list(
            filter(lambda day: day <= until, self.__dates)
        )
        for day in days_to_delete:
            del self.__dates[day]
        if self.__n_until_begin == 0 and len(self.__dates) == 0:
            self.__ever_done = False
            self.__last_time = date(year=9999, month=12, day=31)

    def forward_begin_to(self, day: date) -> None:
        """Reduce the data stored by setting `self.__begin_on` later."""
        raise NotImplementedError("Implement me !")


# class TaskRecorder:
#     """Records the tasks performed by some Coloc over time."""
