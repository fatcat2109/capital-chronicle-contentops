"""Market dates for CC-495's one-trading-day fact rule; no runtime scheduling."""
from datetime import date, timedelta


def _observed(day):
    return day + timedelta(days=1 if day.weekday() == 6 else -1 if day.weekday() == 5 else 0)


def _nth(year, month, weekday, n):
    first = date(year, month, 1)
    return first + timedelta(days=(weekday-first.weekday()) % 7 + 7*(n-1))


def _easter(year):
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b-f+1) // 3
    h = (19*a+b-d-g+15) % 30
    i, k = c // 4, c % 4
    l = (32+2*e+2*i-h-k) % 7
    m = (a+11*h+22*l) // 451
    return date(year, (h+l-7*m+114)//31, (h+l-7*m+114) % 31+1)


def trading_date(day, markets):
    if day.weekday() >= 5:
        return False
    y = day.year
    holidays = {_observed(date(y, 1, 1)), _observed(date(y+1, 1, 1)), _observed(date(y, 12, 25))}
    if markets & {"SPX", "NDX", "NASDAQ", "DOW", "EQUITIES", "US2Y", "US10Y", "US30Y", "RATES"}:
        holidays |= {_nth(y, 1, 0, 3), _nth(y, 2, 0, 3), _easter(y)-timedelta(days=2),
                     _nth(y, 9, 0, 1), _nth(y, 11, 3, 4), _observed(date(y, 7, 4))}
        memorial = date(y, 5, 31)
        holidays.add(memorial-timedelta(days=memorial.weekday()))
        if y >= 2022:
            holidays.add(_observed(date(y, 6, 19)))
    if markets & {"US2Y", "US10Y", "US30Y", "RATES"}:
        holidays |= {_nth(y, 10, 0, 2), _observed(date(y, 11, 11))}
    return day not in holidays
