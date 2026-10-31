"""Calculate this ward's single-/two-day HSCT labels, using calendar dates."""
import argparse
import json
import re
from datetime import date


def parse_date(value):
    """Accept only explicit calendar dates, consistently across Python versions."""
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ValueError("Dates must use YYYY-MM-DD with an explicit year.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Invalid calendar date: " + value) from exc


def transplant_day(event_date, transplant_dates):
    if not isinstance(transplant_dates, (list, tuple)) or len(transplant_dates) not in (1, 2):
        raise ValueError("Provide exactly one or two transplant dates.")
    event = parse_date(event_date)
    dates = [parse_date(value) for value in transplant_dates]
    if len(dates) == 2 and dates[1] <= dates[0]:
        raise ValueError("The second transplant date must follow the first.")
    if event < dates[0]:
        return {"date": event.isoformat(), "label": None, "status": "before_transplant"}
    if len(dates) == 1 and event == dates[0]:
        label = "0d"
    elif len(dates) == 2 and event in dates:
        label = "01d" if event == dates[0] else "02d"
    elif event < dates[-1]:
        return {"date": event.isoformat(), "label": None, "status": "between_infusions_confirm_convention"}
    else:
        label = f"+{(event - dates[-1]).days}d"
    return {"date": event.isoformat(), "label": label, "status": "resolved"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True, help="Event date, YYYY-MM-DD")
    parser.add_argument("--transplant", required=True, nargs="+", help="One or two dates in chronological order")
    args = parser.parse_args()
    try:
        result = transplant_day(args.date, args.transplant)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False))
