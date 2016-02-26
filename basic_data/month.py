# basic_data.month

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

ucMonthToNum = {name.upper(): i+1 for i, name in enumerate(monthNames)}

def check_month(value):
    if isinstance(value, int):
        if value >= 1 and value <= 12:
            return value
    else:
        ucValue = value.strip().upper()
        if ucValue in ucMonthToNum:
            return ucMonthToNum[ucValue]
        else:
            try:
                month = int(value)
                if month >= 1 and month <= 12:
                    return month
            except ValueError:
                pass
    raise ValueError('"{}" is not a valid month'.format(value))

class MonthMapper:
    @staticmethod
    def map_out(value):
        if isinstance(value, int) and value >= 1 and value <= 12:
            return monthNames[value-1]
        else:
            return value

    @staticmethod
    def map_in(name):
        try:
            return check_month(name)
        except ValueError:
            return name
