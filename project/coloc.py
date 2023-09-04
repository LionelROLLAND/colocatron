"""Class that represents a coloc."""

# import zoneinfo
import logging
from collections.abc import Iterable as ClassIterable
from datetime import date, timedelta
from typing import Iterable as TypeIterable
from typing import Optional

DEFAULT_TZ = ["Europe/Paris", "Etc/GMT+1", "UTC"]
ONE_DAY = timedelta(days=1)


def period_type_error(invalid_period) -> TypeError:
    """Return a type error in case a date was given in a bad type."""
    return TypeError(
        f"Incorrect type for an absence : "
        f"Expected date | Iterable[date], got {invalid_period}."
    )


class Presence:
    """Class to store the days of absence/presence of a coloc."""

    class InvalidDayError(ValueError):
        """Raised when setting an absence on an incorrect day for a Presence Instance."""

    class BeforeStartDayError(InvalidDayError):
        """Raised when setting an absence before the start of a Presence instance."""

    class StartToReliableDayError(InvalidDayError):
        """
        Raised when setting an absence on an incorrect period of a Presence instance.

        The incorrect period is the one between the starting date of the Presence instance
        and the day since which the absences are recorded day by day (Presence.__absences_begin_on).
        """

    class AbsenceTrackingAfterBeginError(InvalidDayError):
        """
        Raised when setting the absences number on a period in a wrong way.

        Raised when the starting point of the period is after self.__absences_begin_on.
        """

    def __init__(self, start: date) -> None:
        """Initialize an empty Presence instance."""
        self.__absences: set[date] = set()
        self.__start: date = start
        self.__absences_begin_on: date = start
        self.__absences_before_begin: int = 0

    def set_absence_check(self, day: date) -> None:
        """Raise an error if an absence can not be added/removed for the date day."""
        if not isinstance(day, date):
            raise period_type_error(day)
        if day < self.__start:
            raise self.BeforeStartDayError(
                "Trying to set an absence before the start of the Presence instance."
            )
        if day < self.__absences_begin_on:
            raise self.StartToReliableDayError(
                "Trying to set an absence between the start "
                "of the Presence instance and the start of "
                "the reliability of the absences."
            )

    def add_absence(self, period: date | TypeIterable[date]) -> None:
        """Add the absences defined by period."""
        if isinstance(period, date):
            self.set_absence_check(period)
            self.__absences.add(period)
        elif isinstance(period, ClassIterable):
            for day in period:
                self.set_absence_check(day)
            self.__absences.update(period)
        else:
            raise period_type_error(period)

    @classmethod
    def from_absences(cls, start: date, absences: TypeIterable[date]) -> "Presence":
        """Return a Presence instance defined by the absences passed as arguments."""
        pres = Presence(start=start)
        pres.add_absence(absences)
        return pres

    def on_period(self, period: date | TypeIterable[date]) -> bool:
        """Return True if present on period."""
        type_error = TypeError(
            f"Incorrect type for a period : Expected date | Iterable[date], got {period}."
        )
        if isinstance(period, date):
            return self.on_period([period])
        if isinstance(period, ClassIterable):
            present: bool = True
            for day in period:
                if not isinstance(day, date):
                    raise type_error
                if day < self.__start:
                    logging.warning(
                        "Asking for the presence before the start of a presence instance."
                    )
                    present = False
                elif day < self.__absences_begin_on:
                    raise self.StartToReliableDayError(
                        "Asking for the presence between the start "
                        "of the Presence instance and the start of "
                        "the reliability of the absences."
                    )
                elif day in self.__absences:
                    present = False
            return present
        raise type_error

    def not_on_period(self, period: date | TypeIterable[date]) -> bool:
        """Return True if absent on period."""
        type_error = TypeError(
            f"Incorrect type for a period : Expected date | Iterable[date], got {period}."
        )
        if isinstance(period, date):
            return self.not_on_period([period])
        if isinstance(period, ClassIterable):
            absent: bool = True
            for day in period:
                if not isinstance(day, date):
                    raise type_error
                if day < self.__start:
                    logging.warning(
                        "Asking for the presence before the start of a presence instance."
                    )
                elif day < self.__absences_begin_on:
                    raise self.StartToReliableDayError(
                        "Asking for the presence between the start "
                        "of the Presence instance and the start of "
                        "the reliability of the absences."
                    )
                elif day not in self.__absences:
                    absent = False
            return absent
        raise type_error

    def days_nb_until(self, day: date) -> int:
        """Return the number of days of presence until day (included)."""
        if day < self.__start:
            logging.warning(
                "Asking for the presence before the start of a presence instance."
            )
            return 0
        if day < self.__absences_begin_on:
            raise self.StartToReliableDayError(
                "Asking for the presence between the start "
                "of the Presence instance and the start of "
                "the reliability of the absences."
            )
        nb_days = (day - self.__start).days + 1
        nb_abs = sum(1 for _ in filter(lambda absence: absence <= day, self.__absences))
        return nb_days - nb_abs - self.__absences_before_begin

    def rm_absence(self, period: date | TypeIterable[date]) -> None:
        """
        Remove the absences defined by period.

        Said in another words, set period as a presence period.
        """
        type_error = TypeError(
            f"Incorrect type for an absence : Expected date | Iterable[date], got {period}."
        )
        if isinstance(period, date):
            self.rm_absence([period])
        elif isinstance(period, ClassIterable):
            buffer: set[date] = set()
            for day in period:
                if not isinstance(day, date):
                    raise type_error
                if day < self.__start:
                    raise self.BeforeStartDayError(
                        "Trying to set an absence before the start "
                        "of the Presence instance."
                    )
                if day < self.__absences_begin_on:
                    raise self.StartToReliableDayError(
                        "Trying to set an absence between the start "
                        "of the Presence instance and the start of "
                        "the reliability of the absences."
                    )
                buffer.add(day)
            self.__absences -= buffer
        else:
            raise type_error

    def set_absence_nb_between(self, start: date, end: date, abs_nb: int) -> None:
        """
        Set the absences number between start and end (included).

        Update self.__absences_begin_on and self.__absences.
        """
        if end < start:
            raise ValueError(
                "end date before start date in Presence.set_absence_nb_between(start, end, nb_abs)."
            )
        if start < self.__start:
            raise self.BeforeStartDayError(
                "Trying to set an absence before the start of the Presence instance."
            )
        if (
            self.__start < start < self.__absences_begin_on
            or end < self.__absences_begin_on
        ):
            raise self.StartToReliableDayError(
                "Trying to set an absence between the start "
                "of the Presence instance and the start of "
                "the reliability of the absences."
            )
        if start > self.__absences_begin_on:
            raise self.AbsenceTrackingAfterBeginError(
                "Trying to set the number of absences on a period "
                "such that it creates holes in the absences tracking."
            )
        if start == self.__start:
            self.__absences_before_begin = abs_nb
        elif start == self.__absences_begin_on:
            self.__absences_before_begin += abs_nb
        else:
            raise ValueError(
                "The start date in "
                "Presence.set_absence_nb_between(start, end, nb_abs) "
                "is not valid. No more information since this error "
                "was not supposed to happen and was not catched before."
            )
        self.__absences_begin_on = end + ONE_DAY
        self.__absences -= set(filter(lambda day: day <= end, self.__absences))  # type: ignore
        # I wanted to do it like this:
        #
        # self.__absences.difference_update(filter(lambda day: day <= end, self.__absences))
        #
        # but as filter(...) is an iterator, I was afraid that it would imply modifying
        # self.__absences while iterating over it (I'm not aware of the implementation
        # of set.difference_update though so maybe that's not a problem), so I preferred this way.

    def forward_absences_begin_to(self, day: date) -> None:
        """Reduce the data stored by setting `self.__absences_begin_on` later."""
        raise NotImplementedError("Implement me !")


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

    # Handle the case when the instance is reset ! (when self.__ever_done becomes False)
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


# class TaskRecorder:
#     """Records the tasks performed by some Coloc over time."""
