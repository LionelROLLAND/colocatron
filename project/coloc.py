"""Class that represents a coloc."""

from collections.abc import Iterable as ClassIterable
from dataclasses import dataclass
from datetime import date
from typing import Generator
from typing import Iterable as TypeIterable
from typing import Optional

from presence import Presence
from task import TaskId
from task_history import TaskHistory
from utils import UniqueId, Week, period_type_error

# DEFAULT_TZ = ["Europe/Paris", "Etc/GMT+1", "UTC"]


# pylint: disable=too-few-public-methods
class ColocId(UniqueId):
    """A class to make unique coloc IDs."""


@dataclass(init=False)
class ColocTaskLocalInfo:
    """Groups info specific to some coloc and some task."""

    task_history: TaskHistory
    old_last_time: date
    last_time: date
    old_ever_done: bool
    ever_done: bool

    def __init__(self, start: date, old_last_time: Optional[date] = None):
        """Initialize an empty ColocTaskLocal info, with an optional old_last_time."""
        if old_last_time is not None:
            if old_last_time >= start:
                raise ValueError(
                    "Calling ColocTaskLocalInfo(start, old_last_time) "
                    "with old_last_time after start."
                )
            self.old_ever_done = True
            self.ever_done = True
            self.old_last_time = old_last_time
            self.last_time = old_last_time
        else:
            self.old_ever_done = False
            self.ever_done = False
            self.old_last_time = date(year=9999, month=12, day=31)
            self.last_time = date(year=9999, month=12, day=31)
        self.task_history = TaskHistory(start=Week.week_of_day(start))

    def update_last_time(self, new_last_time: date):
        """Update self.last_time with new_last_time."""
        if not isinstance(new_last_time, date):
            raise TypeError(f"Expected arg of type date, got {new_last_time}")
        if not self.ever_done:
            self.ever_done = True
            self.last_time = new_last_time
        elif new_last_time > self.last_time:
            self.last_time = new_last_time


class ColocSchedule:
    """Class that represents a coloc, in particular their planning."""

    def __init__(self, start: date) -> None:
        """Initialize an empty coloc."""
        self.__start = start
        self.__present: Presence = Presence(start=start)
        self.__tasks: dict[TaskId, ColocTaskLocalInfo] = {}

    def add_blank_task(self, task: TaskId) -> None:
        """Add manually a task if not already there."""
        self.__tasks.setdefault(task, ColocTaskLocalInfo(start=self.__start))

    def add_task_with_last_time(self, task: TaskId, last_time: date) -> None:
        """
        Add manually a task with the last time it has been done.

        Raise if task is already in self.__tasks (no update of
        ColocTaskLocalInfo.old_last_time allowed).
        """
        if task in self.__tasks:
            raise ValueError(
                "Trying to manually add a task that is already there "
                "with a last_time arg."
            )
        self.__tasks[task] = ColocTaskLocalInfo(
            start=self.__start, old_last_time=last_time
        )

    def add_task_on_week(self, task: TaskId, week: Week) -> None:
        """
        Add task to the corresponding task history of the coloc.

        No error management as the errors will already be caught by Presence.on_any_of and
        TaskHistory.add.
        """
        task_info = self.__tasks.setdefault(
            task, ColocTaskLocalInfo(start=self.__start)
        )

        if self.__present.on_any_of(iter(week)):
            last_day = max(self.__present.days_between(week.monday, week.sunday))
            task_info.update_last_time(last_day)
        task_info.task_history.add(week)

    def presence_days_with_task_after_start(
        self, task: TaskId
    ) -> Generator[date, None, None]:
        """Iterate over the days of presence during which task is assigned to self."""
        for week in self.__tasks[task].task_history:
            for day in week:
                if self.__present.on_all_of(day):
                    yield day

    def compute_last_time_after_added_absence(self, task) -> None:
        """
        Compute the ColocTaskLocalInfo.last_time for task.

        Assume that it is used just after an absence has been added for self.
        It means that it may produce unexpected results if it used after having
        removed an absence / added a presence day.
        """
        if task in self.__tasks:
            task_info = self.__tasks[task]
            if any(True for _ in self.presence_days_with_task_after_start(task)):
                task_info.last_time = max(
                    self.presence_days_with_task_after_start(task)
                )
            else:
                task_info.ever_done = task_info.old_ever_done
                task_info.last_time = task_info.old_last_time

    def add_absence_on(self, period: date | TypeIterable[date]) -> None:
        """Add period to the absence days of the coloc self."""
        self.__present.add_absence(period)
        if isinstance(period, date):
            for task, task_info in self.__tasks.items():
                if period == task_info.last_time:
                    self.compute_last_time_after_added_absence(task)
        elif isinstance(period, ClassIterable):
            for task, task_info in self.__tasks.items():
                if any(day == task_info.last_time for day in period):
                    self.compute_last_time_after_added_absence(task)
        else:
            raise RuntimeError(
                "Unexpected error that should have been caught before, "
                "about the type of period in ColocSchedule.add_absence_on(period)."
            )

    def add_presence_on(self, period: date | TypeIterable[date]) -> None:
        """Add period to the presence days of the coloc self."""
        self.__present.discard_absence(period)
        if isinstance(period, date):
            for task_info in self.__tasks.values():
                if Week.week_of_day(period) in task_info.task_history:
                    task_info.update_last_time(period)

        elif isinstance(period, ClassIterable):
            latest_days_in_weeks: dict[Week, date] = {}
            for day in period:
                week = Week.week_of_day(day)
                if (week not in latest_days_in_weeks) or latest_days_in_weeks[
                    week
                ] < day:
                    latest_days_in_weeks[week] = day
            for task_info in self.__tasks.values():
                if any(week in task_info.task_history for week in latest_days_in_weeks):
                    # Warning: potential_days is valid only in its iteration
                    # pylint: disable=cell-var-from-loop
                    potential_days = (
                        day
                        for _, day in filter(
                            lambda week_day: week_day[0] in task_info.task_history,
                            latest_days_in_weeks.items(),
                        )
                    )
                    last_day = max(potential_days)
                    task_info.update_last_time(last_day)
        else:
            raise period_type_error(period)
