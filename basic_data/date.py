# basic_data.date

monthNames = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December'
]

ucMonthAbbrToNum = {name[0:3].upper(): i+1 for i, name in enumerate(monthNames)}

daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
daysInMonthLy = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

def is_leap_year(year):
    return (year % 4) == 0

def days_in_month(month, year=None):
    if year is None or is_leap_year(year):
        return daysInMonthLy[month-1]
    else:
        return daysInMonth[month-1]

class DateChecker:
    def __init__(self):
        self.year = ""
        self.iyear = None
        self.month = ""
        self.imonth = None
        self.day = ""
        self.iday = None
        self.unknown = False
        self.incomplete = False

    # DateChecker intended for one-time use, but to use again call reset()
    def reset(self):
        self.__init__()

    def check_date(self, value, fixDay=False, tolerateIncomplete=False):
        if "UNKNOWN" in value.upper():
            self.unknown = True
        else:
            # split on dashes and assign parts to year/month/day
            parts = [part.strip() for part in value.split("-", maxsplit=2)]
            if len(parts) == 1:
                (self.year,) = parts
            elif len(parts) == 2:
                if parts[0].isnumeric() and len(parts[0]) >= 4:
                    (self.year, self.month) = parts
                else:
                    (self.month, self.day) = parts
            else:
                (self.year, self.month, self.day) = parts

            # convert spelled-out months before other validation
            if not self.month.isnumeric():
                ucMonthAbbr = self.month[0:3].upper()
                if ucMonthAbbr in ucMonthAbbrToNum:
                    self.imonth = ucMonthAbbrToNum[ucMonthAbbr]

            # convert to integers and validate ranges
            if self.year:
                try:
                    self.iyear = int(self.year)
                    if self.iyear < 1000 or self.iyear > 9999:
                        raise ValueError()
                except ValueError:
                    raise ValueError("{} is not a valid year".format(self.year))
            if self.imonth is None and self.month:
                try:
                    self.imonth = int(self.month)
                    if self.imonth < 1 or self.imonth > 12:
                        raise ValueError()
                except ValueError:
                    raise ValueError("{} is not a valid month".format(self.month))
            if self.day:
                try:
                    self.iday = int(self.day)
                    if self.iday < 1 or self.iday > 31:
                        raise ValueError()
                except ValueError:
                    raise ValueError("{} is not a valid day".format(self.day))
                if self.imonth is not None:
                    n = days_in_month(self.imonth, self.iyear)
                    if self.iday > n:
                        if fixDay:
                            self.iday = n
                        else:
                            raise ValueError("Day {} is out of range for {}".format(self.iday, monthNames[self.imonth-1]))

            # check for incomplete
            if (self.day and not self.month) or (self.month and not (self.day or self.year)):
                self.incomplete = True
                if not tolerateIncomplete:
                    raise ValueError("Date is incomplete")

    def format(self, asEntered=False, slash=False):
        if self.unknown:
            return "Unknown"
        elif self.incomplete or asEntered:
            return "{}-{}-{}".format(self.year, self.month, self.day)
        elif self.iyear is not None:
            if self.imonth is not None:
                if self.iday is not None:
                    if slash:
                        return "{:d}/{:d}/{:04d}".format(self.imonth, self.iday, self.iyear)
                    else:
                        return "{:04d}-{:02d}-{:02d}".format(self.iyear, self.imonth, self.iday)
                else:
                    if slash:
                        return "{:d}/{:04d}".format(self.imonth, self.iyear)
                    else:
                        return "{:04d}-{:02d}".format(self.iyear, self.imonth)
            else:
                return "{:04d}".format(self.iyear)
        elif self.imonth is not None and self.iday is not None:
            if slash:
                return "{:d}/{:d}".format(self.imonth, self.iday)
            else:
                return "{:02d}-{:02d}".format(self.imonth, self.iday)
        else:
            return ""

def check_date(value):
    dc = DateChecker()
    dc.check_date(value)
    return dc.format()

def format(value, slash=False):
    dc = DateChecker()
    dc.check_date(value)
    return dc.format(slash=slash)
