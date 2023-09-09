"""Provide some functions that might be used in different submodules."""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Generator

from constants import ONE_DAY


@dataclass(init=False, frozen=True)
class Week:
    """A class representing some week in time."""

    __monday: date

    def __init__(self, year: int, week_nb: int) -> None:
        """Initialize a Week instance thank to its year and number in the year."""
        monday = datetime.strptime(f"{str(year)}-{str(week_nb)}-0", "%Y-%W-%w").date()
        object.__setattr__(self, "_Week__monday", monday)

    @classmethod
    def week_of_day(cls, day: date) -> "Week":
        """Initialize a Week instance from any day in this week."""
        if not isinstance(day, date):
            raise TypeError(f"Expected arg of type date, got {day}.")
        return Week(year=day.year, week_nb=int(day.strftime("%W")))

    @property
    def monday(self) -> date:
        """Return the first day of the week."""
        return self.__monday

    @property
    def sunday(self) -> date:
        """Return the last day of the week."""
        return self.__monday + 6 * ONE_DAY

    def __iter__(self) -> Generator[date, None, None]:
        """Iterate over all days in the week."""
        for i in range(7):
            yield self.__monday + i * ONE_DAY

    def __contains__(self, day: date) -> bool:
        """Return True if day is a day of week self."""
        return self.__monday <= day <= self.sunday

    def __lt__(self, other: "Week" | date) -> bool:
        """Return True if self is strictly before other."""
        if isinstance(other, Week):
            return self.__monday < other.monday
        if isinstance(other, date):
            return self.sunday < other
        raise TypeError(f"Expected argument of type Week or date, got {other}")

    def __gt__(self, other: "Week" | date) -> bool:
        """Return True if self is strictly after other."""
        if isinstance(other, Week):
            return self.__monday > other.monday
        if isinstance(other, date):
            return self.monday > other
        raise TypeError(f"Expected argument of type Week or date, got {other}")

    def __eq__(self, other: object) -> bool:
        """Return True if the 2 weeks in the arguments are the same."""
        if not isinstance(other, Week):
            raise TypeError(f"Expected argument of type Week, got {other}")
        return self.__monday == other.monday

    def __ne__(self, other: object) -> bool:
        """Return True if the 2 weeks in the arguments are not the same."""
        if not isinstance(other, Week):
            raise TypeError(f"Expected argument of type Week, got {other}")
        return not self == other

    def __le__(self, other: "Week") -> bool:
        """Return True if self is before other."""
        if not isinstance(other, Week):
            raise TypeError(f"Expected argument of type Week, got {other}")
        return self < other or self == other

    def __ge__(self, other: "Week") -> bool:
        """Return True if self is after other."""
        if not isinstance(other, Week):
            raise TypeError(f"Expected argument of type Week, got {other}")
        return self > other or self == other


def period_type_error(invalid_period) -> TypeError:
    """Return a type error in case a date was given in a bad type."""
    return TypeError(
        f"Incorrect type for an absence : "
        f"Expected date | Iterable[date], got {invalid_period}."
    )


@dataclass(frozen=True)
class UniqueId:
    """A class to make unique IDs (in case different colocs have the same name for instance)."""

    name: str
    nth: int
