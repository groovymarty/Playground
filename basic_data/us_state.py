# basic_data.us_state

stateToNameList = [
    ("AL", "Alabama"),
    ("AK", "Alaska"),
    ("AZ", "Arizona"),
    ("AR", "Arkansas"),
    ("CA", "California"),
    ("CO", "Colorado"),
    ("CT", "Connecticut"),
    ("DE", "Delaware"),
    ("DC", "District of Columbia"),
    ("FL", "Florida"),
    ("GA", "Georgia"),
    ("HI", "Hawaii"),
    ("ID", "Idaho"),
    ("IL", "Illinois"),
    ("IN", "Indiana"),
    ("IA", "Iowa"),
    ("KS", "Kansas"),
    ("KY", "Kentucky"),
    ("LA", "Louisiana"),
    ("ME", "Maine"),
    ("MD", "Maryland"),
    ("MA", "Massachusetts"),
    ("MI", "Michigan"),
    ("MN", "Minnesota"),
    ("MS", "Mississippi"),
    ("MO", "Missouri"),
    ("MT", "Montana"),
    ("NE", "Nebraska"),
    ("NV", "Nevada"),
    ("NH", "New Hampshire"),
    ("NJ", "New Jersey"),
    ("NM", "New Mexico"),
    ("NY", "New York"),
    ("NC", "North Carolina"),
    ("ND", "North Dakota"),
    ("OH", "Ohio"),
    ("OK", "Oklahoma"),
    ("OR", "Oregon"),
    ("PA", "Pennsylvania"),
    ("RI", "Rhode Island"),
    ("SC", "South Carolina"),
    ("SD", "South Dakota"),
    ("TN", "Tennessee"),
    ("TX", "Texas"),
    ("UT", "Utah"),
    ("VT", "Vermont"),
    ("VA", "Virginia"),
    ("WA", "Washington"),
    ("WV", "West Virginia"),
    ("WI", "Wisconsin"),
    ("WY", "Wyoming")
]

states = [state for state, name in stateToNameList]
stateNames = [name for state, name in stateToNameList]
stateToName = {state: name for state, name in stateToNameList}
ucNameToState = {name.upper(): state for state, name in stateToNameList}

def check_state(value):
    ucValue = value.strip().upper()
    if len(ucValue) == 0:
        return ""
    elif ucValue == "UNKNOWN":
        return "Unknown"
    elif ucValue in stateToName:
        return ucValue
    elif ucValue in ucNameToState:
        return ucNameToState[ucValue]
    else:
        raise ValueError('"{}" is not a valid state'.format(value))

class StateMapper:
    @staticmethod
    def map_out(value):
        if value in stateToName:
            return stateToName[value]
        else:
            return value

    @staticmethod
    def map_in(name):
        try:
            return check_state(name)
        except ValueError:
            return name
