# basic_data.maritalstatus

maritalStatusNames = [
    "Single",
    "Married",
    "Separated",
    "Divorced",
    "Widowed"
]

def check_marital_status(value):
    ucValue = value.strip().upper()
    if len(ucValue) == 0:
        return ""
    elif ucValue == "UNKNOWN":
        return "Unknown"
    elif ucValue.startswith("SING"):
        return "Single"
    elif ucValue.startswith("M"):
        return "Married"
    elif ucValue.startswith("SEP"):
        return "Separated"
    elif ucValue.startswith("D"):
        return "Divorced"
    elif ucValue.startswith("W"):
        return "Widowed"
    else:
        raise ValueError('"{}" is not a valid marital status'.format(value))
