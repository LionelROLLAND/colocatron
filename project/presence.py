"""Provide a Presence class to represent the days of presence/absence of a coloc."""

# import zoneinfo
from collections.abc import Iterable as ClassIterable
from datetime import date
from typing import Iterable as TypeIterable
from typing import Optional

from constants import ONE_DAY
from utils import period_type_error


class Presence:
    """Class to store the days of absence/presence of a coloc."""

    class InvalidDayError(ValueError):
        """Raised when setting an absence on an incorrect day for a Presence Instance."""

    class BeforeAbsenceBeginError(InvalidDayError):
        """
        Raised when setting an absence on an incorrect period of a Presence instance.

        The incorrect period is the one before the day since which the absences are
        recorded day by day (Presence.__absences_begin_on).
        """

    class AbsenceTrackingAfterBeginError(InvalidDayError):
        """
        Raised when setting the absences number on a period in a wrong way.

        Raised when the starting point of the period is after self.__absences_begin_on.
        """

    def __init__(self, start: date) -> None:
        """Initialize an empty Presence instance."""
        self.__absences: set[date] = set()
        self.__absences_begin_on: date = start
        self.__presences_before_begin: int = 0

    # Needs typing
    @classmethod
    def from_json_object(cls, json_obj):
        """Return a TaskHistory instance from an object extracted from a json."""
        raise NotImplementedError("Implement me !")

    # Needs typing
    def to_json_object(self):
        """Return an object that stores the data of the class and that can be put in a json."""
        raise NotImplementedError("Implement me !")

    def ask_or_set_absence_check(self, day: date) -> None:
        """Raise an error if an absence can not be added/removed for the date day."""
        if not isinstance(day, date):
            raise period_type_error(day)
        if day < self.__absences_begin_on:
            raise self.BeforeAbsenceBeginError(
                "Trying to set/ask for an absence before the start of the absences recording."
            )

    def add_absence(self, period: date | TypeIterable[date]) -> None:
        """Add the absences defined by period."""
        if isinstance(period, date):
            self.ask_or_set_absence_check(period)
            self.__absences.add(period)
        elif isinstance(period, ClassIterable):
            for day in period:
                self.ask_or_set_absence_check(day)
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
        if isinstance(period, date):
            self.ask_or_set_absence_check(period)
            return period not in self.__absences
        if isinstance(period, ClassIterable):
            present: bool = True
            for day in period:
                self.ask_or_set_absence_check(day)
                if day in self.__absences:
                    present = False
            return present
        raise period_type_error(period)

    def not_on_period(self, period: date | TypeIterable[date]) -> bool:
        """Return True if absent on period."""
        if isinstance(period, date):
            self.ask_or_set_absence_check(period)
            return period in self.__absences
        if isinstance(period, ClassIterable):
            absent: bool = True
            for day in period:
                self.ask_or_set_absence_check(day)
                if day not in self.__absences:
                    absent = False
            return absent
        raise period_type_error(period)

    def days_nb_until(self, day: date) -> int:
        """Return the number of days of presence until day (included)."""
        self.ask_or_set_absence_check(day)
        nb_days_after_begin = (day - self.__absences_begin_on).days + 1
        nb_abs = sum(1 for _ in filter(lambda absence: absence <= day, self.__absences))
        return nb_days_after_begin - nb_abs + self.__presences_before_begin

    def rm_absence(self, period: date | TypeIterable[date]) -> None:
        """
        Remove the absences defined by period.

        Said in other words, set period as a presence period.
        """
        if isinstance(period, date):
            self.ask_or_set_absence_check(period)
            self.__absences.discard(period)
        elif isinstance(period, ClassIterable):
            buffer: set[date] = set()
            for day in period:
                self.ask_or_set_absence_check(day)
                buffer.add(day)
            self.__absences -= buffer
        else:
            raise period_type_error(period)

    def set_presence_nb_between(
        self, until: date, pres_nb: int, start: Optional[date] = None
    ) -> None:
        """
        Set the absences number between start and end (included).

        Update self.__absences_begin_on and self.__absences.
        """
        if until < self.__absences_begin_on:
            raise ValueError(
                "Trying to set global information until a date that is before "
                "the beginning of the absences recording."
            )
        if start is not None:
            if start > until:
                raise ValueError(
                    'End date ("until") sooner than start date in the method '
                    "Presence.set_presence_nb_between."
                )
            if start > self.__absences_begin_on:
                raise self.AbsenceTrackingAfterBeginError(
                    "Trying to set the number of absences on a period "
                    "such that it creates holes in the absences tracking."
                )
            if start < self.__absences_begin_on and self.__presences_before_begin != 0:
                raise ValueError(
                    "Trying to set global information starting before the beginning "
                    "of the absences recording for a Presence instancethat is such that "
                    "there is already some presence information for before the beginning "
                    "of the absences recording."
                )
        if start is None or start < self.__absences_begin_on:
            self.__presences_before_begin = pres_nb
        else:
            self.__presences_before_begin += pres_nb
        self.__absences_begin_on = until + ONE_DAY
        self.__absences -= set(filter(lambda day: day <= until, self.__absences))  # type: ignore
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
