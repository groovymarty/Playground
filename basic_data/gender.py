# basic_data.gender

genderToNameList = [
    ("M", "Male"),
    ("F", "Female")
]

genders = [gender for gender, name in genderToNameList]
genderNames = [name for gender, name in genderToNameList]
genderToName = {gender: name for gender, name in genderToNameList}

def check_gender(value):
    ucValue = value.strip().upper()
    if len(ucValue) == 0:
        return ""
    elif ucValue == "UNKNOWN":
        return "Unknown"
    elif ucValue.startswith("M"):
        return "M"
    elif ucValue.startswith("F"):
        return "F"
    else:
        raise ValueError('"{}" is not a valid gender'.format(value))

class GenderMapper:
    @staticmethod
    def map_out(value):
        if value in genderToName:
            return genderToName[value]
        else:
            return value

    @staticmethod
    def map_in(name):
        try:
            return check_gender(name)
        except ValueError:
            return name
