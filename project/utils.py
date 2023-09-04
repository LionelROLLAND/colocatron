"""Provide some functions that might be used in different submodules."""


def period_type_error(invalid_period) -> TypeError:
    """Return a type error in case a date was given in a bad type."""
    return TypeError(
        f"Incorrect type for an absence : "
        f"Expected date | Iterable[date], got {invalid_period}."
    )
