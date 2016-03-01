# everybody.person

from body_and_soul import Body, BodyHelper
from basic_data import checkers, gender, us_state, maritalstatus, phone, date
from basic_services import log_error
from everybody.relat import RelatHelper

class Person(Body, BodyHelper, RelatHelper):
    # Note all phone numbers are included here, so they exist even if address counterpart does not
    defaultValues = {
        'namePrefix': "",
        'usePrefix': False,
        'firstName': "",
        'middleName': "",
        'useMiddleName': False,
        'lastName': "",
        'nameSuffix': "",
        'useSuffix': False,
        'nickName': "",
        'useNickName': False,
        'gender': "",
        'maidenName': "",
        'birthday': "",
        'maritalStatus': "",
        'anniversary': "",
        'deceased': False,
        'deathDate': "",
        'home.phone': "",
        'work.phone': "",
        'mobile.phone': "",
        'email': ""
    }
    checkers = {
        'namePrefix': str.strip,
        'firstName': checkers.check_required_str,
        'middleName': str.strip,
        'lastName': checkers.check_required_str,
        'nameSuffix': str.strip,
        'nickName': str.strip,
        'gender': gender.check_gender,
        'maidenName': str.strip,
        'maritalStatus': maritalstatus.check_marital_status,
        'birthday': date.check_date,
        'anniversary': date.check_date,
        'deathDate': date.check_date,
        'home.phone': phone.check_phone,
        'work.phone': phone.check_phone,
        'mobile.phone': phone.check_phone,
        'email': str.strip
    }

    # Address flavors
    addrFlavors = 'home', 'work', 'seasonal', 'other'
    addrNames = {
        'home': "Home",
        'work': "Work",
        'seasonal': "Seasonal",
        'other': "Other"
    }
    # If sentinel key for a flavor is present, then all other address fields must be present also
    # Two functions, post_load and touch_address, are responsible for ensuring this
    addrSentinelKeys = {
        'home': 'home.addrLine1',
        'work': 'work.addrLine1',
        'seasonal': 'seasonal.addrLine1',
        'other': 'other.addrLine1'
    }
    addrDefaults = {
        'addrLine1': "",
        'addrLine2': "",
        'addrLine3': "",
        'useLine3': False,
        'city': "",
        'state': "",
        'zipCode': "",
        'country': "USA",
        'useCountry': False
    }
    addrCheckers = {
        'addrLine1': str.strip,
        'addrLine2': str.strip,
        'addrLine3': str.strip,
        'city': str.strip,
        'state': us_state.check_state,
        'zipCode': str.strip,
        'country': str.strip
    }

    # Set of flavored keys for each address flavor (built below)
    addrKeysByFlavor = None

    # Default values with flavored keys for each address flavor (built below)
    addrDefaultsByFlavor = None

    # Mapping from key to address flavor, for example 'home.addrLine1' maps to 'home'
    keyToAddrFlavor = None

    def post_load(self):
        # Fill in missing defaults for all existing address flavors
        # But don't add any new address flavors
        for flavor, sentinelKey in self.addrSentinelKeys.items():
            if sentinelKey in self.soul.values:
                self.soul.values.update((key, value) for key, value in self.addrDefaultsByFlavor[flavor].items()
                                        if not key in self.soul.values)
        self.count_indexed_relats()

    def pre_save(self):
        # If an address flavor (other than home) is all defaults, remove it before saving to storage
        for flavor, sentinelKey in self.addrSentinelKeys.items():
            if sentinelKey in self.soul.values and flavor != 'home':
                if all(self.soul.values[key] == value for key, value in self.addrDefaultsByFlavor[flavor].items()):
                    for key in self.addrKeysByFlavor[flavor]:
                        del self.soul.values[key]
        self.remove_deleted_relats()

    def build_name(self, lnf=False, punct=False, formal=False):
        words = []
        if self.lastName and lnf:
            words.append(self.lastName+",")
        if self.namePrefix and (self.usePrefix or formal):
            if formal or punct:
                words.append(self.namePrefix)
            else:
                words.append(self.namePrefix.rstrip("."))
        if self.nickName and self.useNickName and not formal:
            words.append(self.nickName)
        elif self.firstName:
            words.append(self.firstName)
        if self.middleName and self.useMiddleName:
            words.append(self.middleName)
        elif self.middleName:
            if formal or punct:
                words.append(self.middleName[:1]+".")
            else:
                words.append(self.middleName[:1])
        if self.lastName and not lnf:
            words.append(self.lastName)
        if self.nameSuffix and (self.useSuffix or formal):
            if formal or punct:
                if len(words) > 0:
                    words[-1] += ","
                words.append(self.nameSuffix)
            else:
                words.append(self.nameSuffix.rstrip("."))
        return " ".join(words)

    @property
    def fullName(self):
        return self.build_name(punct=True)

    @property
    def formalName(self):
        return self.build_name(formal=True)

    @property
    def sortName(self):
        return self.build_name(lnf=True)

    def get_real_label(self):
        return self.sortName

    def has_address(self, flavor):
        return self.has_value(self.addrSentinelKeys[flavor])

    def is_ok_to_save(self):
        return not any(key in self.valueErrors for key in ('firstName', 'lastName'))

    def touch_address(self, flavor):
        if not self.has_address(flavor):
            self.protoValues.update((key, value) for key, value in self.addrDefaultsByFlavor[flavor].items()
                                    if key not in self.newValues)

    def get_addresses(self):
        return [flavor for flavor in self.addrFlavors if self.has_address(flavor)]

    def touch_addresses(self, flavors):
        for flavor in flavors:
            self.touch_address(flavor)

    def get_addr_value(self, flavor, key):
        self.touch_address(flavor)
        return self.get_value(self.join_key(flavor, key))

    def set_addr_value(self, flavor, key, value):
        self.touch_address(flavor)
        self.set_value(self.join_key(flavor, value))

    def build_address(self, flavor='home'):
        lines = []
        if self.has_address(flavor):
            if not self.get_addr_value(flavor, 'useLine3'):
                if self.get_addr_value(flavor, 'useCountry'):
                    trailKeys = 'city', 'state', 'zipCode', 'country'
                else:
                    trailKeys = 'city', 'state', 'zipCode'
                trailer = " ".join(self.get_addr_value(flavor, key) for key in trailKeys)
            else:
                trailer = self.get_addr_value(flavor, 'addrLine3')
            for key in 'addrLine1', 'addrLine2':
                line = self.get_addr_value(flavor, key)
                if line:
                    lines.append(line)
            if trailer:
                lines.append(trailer)
        return lines

# Add properties for all non-flavored fields
Person.make_all_properties()

# Build default value dictionary with flavored keys for each address flavor
Person.addrDefaultsByFlavor = {flavor: Person.make_flavored(flavor, Person.addrDefaults)
                               for flavor in Person.addrFlavors}

# Built set of flavored keys for each address flavor
Person.addrKeysByFlavor = {flavor: set(d.keys()) for flavor, d in Person.addrDefaultsByFlavor.items()}

# Include home address fields in defaultValues so person will always have home address
Person.defaultValues.update(Person.addrDefaultsByFlavor['home'])

# Add checkers for each address flavor
for flavor in Person.addrFlavors:
    Person.checkers.update(Person.make_flavored(flavor, Person.addrCheckers))

# Mapping from key to address flavor, for example 'home.addrLine1' maps to 'home'
Person.keyToAddrFlavor = {key: flavor for flavor, d in Person.addrKeysByFlavor.items() for key in d}
