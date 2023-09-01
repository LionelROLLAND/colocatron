"""Class that represents a coloc."""

# import zoneinfo
import logging
from collections.abc import Iterable as ClassIterable
from datetime import date, timedelta
from typing import Iterable as TypeIterable

DEFAULT_TZ = ["Europe/Paris", "Etc/GMT+1", "UTC"]
ONE_DAY = timedelta(days=1)


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

    def period_type_error(self, invalid_period) -> TypeError:
        """Return a type error in case a date was given in a bad type."""
        return TypeError(
            f"Incorrect type for an absence : "
            f"Expected date | Iterable[date], got {invalid_period}."
        )

    def set_absence_check(self, day: date) -> None:
        """Raise an error if an absence can not be added/removed for the date day."""
        if not isinstance(day, date):
            raise self.period_type_error(day)
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
            raise self.period_type_error(period)

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
        # raise NotImplementedError("Implement me !")
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


# class TaskRecorder:
#     """Records the tasks performed by some Coloc over time."""
