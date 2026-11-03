# cronreader

Explain a cron expression in English and print the next times it actually fires.

```bash
python cronreader.py "*/15 3-6 * * 1-5"
```

```
At minute 0, 15, 30 and 45 past hour 03, 04, 05 and 06 on Monday, Tuesday, Wednesday, Thursday and Friday.

Next runs:
  2026-11-04 03:00  Wednesday
  2026-11-04 03:15  Wednesday
  2026-11-04 03:30  Wednesday
  2026-11-04 03:45  Wednesday
  2026-11-04 04:00  Wednesday
```

Nobody parses `*/15 3-6 * * 1-5` right on the first read. Seeing the real
timestamps catches a wrong schedule before it ships, instead of a week later
when the report never arrived.

## Install

```bash
curl -O https://raw.githubusercontent.com/antonidashaci/cronreader/main/cronreader.py
```

Python 3.9+. No dependencies.

## Supports

- ranges `1-5`, steps `*/15` and `0-30/5`, lists `1,15,30`
- names: `mon-fri`, `jan,dec`
- aliases: `@daily` `@hourly` `@weekly` `@monthly` `@yearly` `@midnight`
- Sunday as both `0` and `7`
- the real cron rule that **day-of-month and day-of-week are OR'd** when both
  are restricted, so `0 0 1 * 5` fires on the 1st *and* on every Friday

An invalid field exits `2` and names the field. A schedule that can never fire,
like `0 0 30 2 *`, exits `1`.

## As a library

```python
from cronreader import describe, next_runs

describe("0 9 * * 1-5")          # 'At 09:00 on Monday, ... and Friday.'
next_runs("0 9 * * 1-5", count=3)
```

## Tests

```bash
pytest
```

## License

MIT
