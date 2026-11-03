#!/usr/bin/env python3
"""Explain a cron expression in English and show its next run times.

Nobody reads `*/15 3-6 * * 1-5` correctly on the first try. This prints what it
means and when it actually fires, so a wrong schedule is caught before deploy.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta

FIELDS = ("minute", "hour", "day of month", "month", "day of week")
RANGES = ((0, 59), (0, 23), (1, 31), (1, 12), (0, 6))
MONTHS = "jan feb mar apr may jun jul aug sep oct nov dec".split()
DAYS = "sun mon tue wed thu fri sat".split()
DAY_NAMES = "Sunday Monday Tuesday Wednesday Thursday Friday Saturday".split()
MONTH_NAMES = (
    "January February March April May June July "
    "August September October November December"
).split()
ALIASES = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}


class CronError(ValueError):
    pass


def _token_to_int(token: str, index: int) -> int:
    t = token.strip().lower()
    if index == 3 and t in MONTHS:
        return MONTHS.index(t) + 1
    if index == 4 and t in DAYS:
        return DAYS.index(t)
    if not t.isdigit():
        raise CronError(f"{FIELDS[index]}: {token!r} is not a number")
    return int(t)


def parse_field(spec: str, index: int) -> set[int]:
    """Expand one cron field into the set of values it matches."""
    low, high = RANGES[index]
    values: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            raise CronError(f"{FIELDS[index]}: empty value")
        step = 1
        if "/" in part:
            part, _, step_s = part.partition("/")
            if not step_s.isdigit() or int(step_s) == 0:
                raise CronError(f"{FIELDS[index]}: bad step {step_s!r}")
            step = int(step_s)
        if part in ("*", ""):
            start, end = low, high
        elif "-" in part:
            a, _, b = part.partition("-")
            start, end = _token_to_int(a, index), _token_to_int(b, index)
        else:
            start = _token_to_int(part, index)
            end = high if step > 1 else start
        if index == 4:  # both 0 and 7 mean Sunday
            start = 0 if start == 7 else start
            end = 0 if end == 7 else end
        if start < low or end > high or start > end:
            raise CronError(f"{FIELDS[index]}: {part!r} outside {low}-{high}")
        values.update(range(start, end + 1, step))
    return values


def parse(expression: str) -> list[set[int]]:
    expr = ALIASES.get(expression.strip().lower(), expression).strip()
    parts = expr.split()
    if len(parts) != 5:
        raise CronError(f"expected 5 fields, got {len(parts)}")
    return [parse_field(p, i) for i, p in enumerate(parts)]


def _list_phrase(names: list[str]) -> str:
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def describe(expression: str) -> str:
    """Render a cron expression as an English sentence."""
    minutes, hours, doms, months, dows = parse(expression)
    full = [set(range(lo, hi + 1)) for lo, hi in RANGES]

    if minutes == full[0] and hours == full[1]:
        when = "Every minute"
    elif hours == full[1]:
        when = f"At minute {_list_phrase([str(m) for m in sorted(minutes)])} of every hour"
    elif len(minutes) == 1 and len(hours) == 1:
        when = f"At {next(iter(hours)):02d}:{next(iter(minutes)):02d}"
    else:
        hh = _list_phrase([f"{h:02d}" for h in sorted(hours)])
        mm = _list_phrase([str(m) for m in sorted(minutes)])
        when = f"At minute {mm} past hour {hh}"

    parts = [when]
    if dows != full[4]:
        parts.append("on " + _list_phrase([DAY_NAMES[d] for d in sorted(dows)]))
    if doms != full[2]:
        parts.append("on day " + _list_phrase([str(d) for d in sorted(doms)]) + " of the month")
    if months != full[3]:
        parts.append("in " + _list_phrase([MONTH_NAMES[m - 1] for m in sorted(months)]))
    if len(parts) == 1:
        parts.append("every day")
    return " ".join(parts) + "."


def matches(fields: list[set[int]], moment: datetime) -> bool:
    minutes, hours, doms, months, dows = fields
    if moment.minute not in minutes or moment.hour not in hours:
        return False
    if moment.month not in months:
        return False
    dom_restricted = doms != set(range(1, 32))
    dow_restricted = dows != set(range(0, 7))
    dom_ok = moment.day in doms
    dow_ok = (moment.weekday() + 1) % 7 in dows
    # cron ORs the two day fields when both are restricted
    if dom_restricted and dow_restricted:
        return dom_ok or dow_ok
    return dom_ok and dow_ok


def next_runs(expression: str, count: int = 5, after: datetime | None = None) -> list[datetime]:
    """The next `count` times this expression fires, at or after `after`."""
    fields = parse(expression)
    moment = (after or datetime.now()).replace(second=0, microsecond=0)
    out: list[datetime] = []
    limit = moment + timedelta(days=366 * 5)
    while len(out) < count and moment < limit:
        if matches(fields, moment):
            out.append(moment)
        moment += timedelta(minutes=1)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="cronreader", description="Explain a cron expression.")
    ap.add_argument("expression", help="for example: */15 3-6 * * 1-5")
    ap.add_argument("-n", "--count", type=int, default=5, help="how many upcoming runs to show")
    args = ap.parse_args(argv)

    try:
        print(describe(args.expression))
        runs = next_runs(args.expression, args.count)
    except CronError as exc:
        print(f"cronreader: {exc}", file=sys.stderr)
        return 2

    if not runs:
        print("\nNo run in the next 5 years - this schedule never fires.")
        return 1
    print("\nNext runs:")
    for run in runs:
        print(f"  {run:%Y-%m-%d %H:%M}  {run:%A}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
