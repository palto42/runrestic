import logging
import re
from typing import Any, Dict, Union

logger = logging.getLogger(__name__)


def make_size(size: int) -> str:
    """
    Convert a size in bytes to a human-readable string with appropriate units.

    Parameters
    ----------
    size : int
        The size in bytes.

    Returns
    -------
    str
        The size formatted as a string with units (e.g., "1.23 GiB").
    """
    if size > 1 << 40:
        return f"{size / (1 << 40):.2f} TiB"
    if size > 1 << 30:
        return f"{size / (1 << 30):.2f} GiB"
    if size > 1 << 20:
        return f"{size / (1 << 20):.2f} MiB"
    if size > 1 << 10:
        return f"{size / (1 << 10):.2f} KiB"
    return f"{size:.0f} B"


def parse_size(size: str) -> float:
    """
    Parse a human-readable size string into its equivalent size in bytes.

    Parameters
    ----------
    size : str
        The size string (e.g., "1.23 GiB", "500 MB").

    Returns
    -------
    float
        The size in bytes. Returns 0.0 if parsing fails.
    """
    re_bytes = re.compile(r"([0-9.]+) ?([a-zA-Z]*B)")
    try:
        number, unit = re_bytes.findall(size)[0]
    except IndexError:
        logger.error("Failed to parse size of '%s'", size)
        return 0.0
    units = {
        "B": 1,
        "kB": 10**3,
        "MB": 10**6,
        "GB": 10**9,
        "TB": 10**12,
        "KiB": 1024,
        "MiB": 2**20,
        "GiB": 2**30,
        "TiB": 2**40,
    }
    return float(number) * units[unit]


def parse_time(time_str: str) -> int:
    """
    Parse a time string in the format HH:MM:SS or MM:SS into seconds.

    Parameters
    ----------
    time_str : str
        The time string to parse.

    Returns
    -------
    int
        The total time in seconds. Returns 0 if parsing fails.
    """
    re_time = re.compile(r"(?:([0-9]+):)?([0-9]+):([0-9]+)")
    try:
        hours, minutes, seconds = (
            int(x) if x else 0 for x in re_time.findall(time_str)[0]
        )
    except IndexError:
        logger.error("Failed to parse time of '%s'", time_str)
        return 0
    if minutes:
        seconds += minutes * 60
    if hours:
        seconds += hours * 3600
    return seconds


def deep_update(base: Dict[Any, Any], update: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Recursively update a dictionary with values from another dictionary.

    Parameters
    ----------
    base : dict
        The base dictionary to update.
    update : dict
        The dictionary with updates.

    Returns
    -------
    dict
        A new dictionary with the updates applied.
    """
    new = base.copy()
    for key, value in update.items():
        base_value = new.get(key, {})
        if not isinstance(base_value, dict):
            new[key] = value
        elif isinstance(value, dict):
            new[key] = deep_update(base_value, value)
        else:
            new[key] = value
    return new


def parse_line(  # type: ignore[no-untyped-def]
    regex: str,
    output: str,
    default: Union[str, tuple],  # type: ignore[type-arg]
):
    """
    Parse a line of text using a regex and return matched variables.

    Parameters
    ----------
    regex : str
        The regex pattern to match.
    output : str
        The text to parse.
    default : str or tuple
        Default value(s) to return if no match is found.

    Returns
    -------
    str or tuple
        The parsed result or the default value(s).

    Examples
    --------
    parse_line(
        output=output,
        regex=r"Files:\s+([0-9]+) new,\s+([0-9]+) changed,\s+([0-9]+) unmodified",
        default=("0", "0", "0")
    )
    """
    try:
        parsed = re.findall(regex, output)[0]
    except IndexError:
        logger.error("No match in output for regex '%s'", regex)
        return default
    return parsed