"""Shared data utilities: CSV IO, completeness helpers, and time parsing."""

import csv

NULL = "NULL"


def read_csv(path):
    """Read a CSV into a list of dict rows (handles BOM + bad bytes)."""
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, columns, rows, null=NULL):
    """Write rows as CSV with the given columns, filling missing values with null."""
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {c: null if row.get(c) is None else row[c] for c in columns}
            )


def races_last_year(path):
    """Return the latest year present in a races.csv, or None if unreadable."""
    try:
        years = {int(row["year"]) for row in read_csv(path)}
    except Exception:
        return None
    return max(years) if years else None


def time_str_to_millis(value):
    """Parse 'H:MM:SS.mmm', 'M:SS.mmm' or 'S.mmm' to an integer ms string.

    Returns NULL for missing/unparseable input. Used for lap times and pit
    stop durations from the API, which only provide the formatted string.
    """
    if value is None:
        return NULL
    try:
        parts = str(value).split(":")
        total = float(parts[-1])
        multiplier = 60
        for p in parts[-2::-1]:
            total += float(p) * multiplier
            multiplier *= 60
        return str(round(total * 1000))
    except ValueError:
        return NULL


def strip_z(value):
    """Strip a trailing 'Z' from an API time string; NULL for None."""
    if value is None:
        return NULL
    value = str(value)
    return value[:-1] if value.endswith("Z") else value
