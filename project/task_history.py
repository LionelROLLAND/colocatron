"""Provide a class that represents the history of some specific task performed by some coloc."""

from typing import Iterator, Optional

from utils import Week


class TaskHistory:
    """A class to store the history of some task relatively to some coloc, week by week."""

    def __init__(self, start: Week) -> None:
        """Initialize an empty task history."""
        self.__data: set[Week] = set()
        self.__start: Week = start

    def __ask_or_set_week(self, week: Week) -> None:
        """Test if something can be done with week for the history."""
        if week < self.__start:
            raise ValueError(
                "Trying to access or add a week before "
                "the beginning of the TaskHistory instance."
            )

    def add(self, week: Week) -> None:
        """Add a week during which the task was done in the task history."""
        self.__ask_or_set_week(week)
        self.__data.add(week)

    def discard(self, week: Week) -> None:
        """Remove a week during which the task was done."""
        self.__ask_or_set_week(week)
        self.__data.discard(week)

    def remove(self, week: Week) -> None:
        """Remove a week during which the task was done. Raise if week not in history."""
        self.__ask_or_set_week(week)
        self.__data.remove(week)

    def __iter__(self) -> Iterator[Week]:
        """Iterate over the week in the history."""
        return iter(self.__data)

    def __contains__(self, week: Week) -> bool:
        """Return True if week is in the history."""
        self.__ask_or_set_week(week)
        return week in self.__data

    def weeks_between_weeks(
        self, first_week: Optional[Week], last_week: Optional[Week]
    ) -> Iterator[Week]:
        """Iterate over the weeks in the history between the 2 args (included)."""
        if first_week is not None and last_week is not None and last_week < first_week:
            raise ValueError(
                "Argument first_week of TaskHistory.weeks_between_weeks "
                "is supposed to be before (in time) argument last_week."
            )
        if first_week is not None:
            self.__ask_or_set_week(first_week)
        elif last_week is not None:
            self.__ask_or_set_week(last_week)
        return filter(
            lambda week: (first_week is None or week >= first_week)
            and (last_week is None or week <= last_week),
            self.__data,
        )

    def forward_begin_to(self, week: Week) -> None:
        """Delete the history before week (NOT included)."""
        self.__ask_or_set_week(week)
        to_delete = set(filter(lambda i_week: i_week < week, self.__data))
        self.__data -= to_delete
        self.__start = week

    @property
    def empty_after_start(self) -> bool:
        """Return True if there's no data after self.__start."""
        return len(self.__data) == 0


# class TaskRecorder:
#     """Records the tasks performed by some Coloc over time."""
