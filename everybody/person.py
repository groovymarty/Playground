# everybody.person

from body_and_soul import *
from basic_data import checkers, gender, maritalstatus, phone, date
from everybody import address
from everybody.address import AddrHelper
from everybody.relationship import RelatHelper

namePrefixes = "Mr.", "Ms.", "Mrs.", "Miss", "Dr.", "Rev."

class Person(Body, RelatHelper, AddrHelper):
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
        'useSharedAnniv': False,
        'deceased': False,
        'deathDate': "",
        'home.phone': "",
        'work.phone': "",
        'seasonal.phone': "",
        'other.phone': "",
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
        'seasonal.phone': phone.check_phone,
        'other.phone': phone.check_phone,
        'mobile.phone': phone.check_phone,
        'email': str.strip
    }

    def post_load(self):
        self.fill_addr_defaults()
        self.count_indexed_relats()

    def pre_save(self):
        self.remove_deleted_addrs()
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

    def is_ok_to_save(self):
        return not any(key in self.valueErrors for key in ('firstName', 'lastName'))

# Add properties for all non-flavored fields
Person.make_all_properties()

# Include home address fields in defaultValues so person will always have home address
Person.defaultValues.update(address.addrDefaultsByFlavor['home'])

# Add checkers for each address flavor
for flavor in address.addrFlavors:
    Person.checkers.update(make_flavored(flavor, address.addrCheckers))

def get_default_value(key):
    if key in address.keyToAddrFlavor:
        flavor = address.keyToAddrFlavor[key]
        return address.addrDefaultsByFlavor[flavor].get(key, None)
    else:
        return Person.defaultValues.get(key, None)
