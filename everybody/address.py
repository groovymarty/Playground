# everybody.addr

from basic_data import us_state
from body_and_soul import join_key, make_flavored

# Address flavors
addrFlavors = 'home', 'work', 'seasonal', 'other'
addrNames = {
    'home': "Home",
    'work': "Work",
    'seasonal': "Seasonal",
    'other': "Other"
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
    'useCountry': False,
    'useSharedAddr': False
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

# If sentinel key for a flavor is present, then all other address fields must be present also
# Two functions, post_load and touch_address, are responsible for ensuring this
addrSentinelKeys = { flavor: join_key(flavor, 'addrLine1')
                     for flavor in addrFlavors }

# Default value dictionary with flavored keys for each address flavor
addrDefaultsByFlavor = { flavor: make_flavored(flavor, addrDefaults)
                         for flavor in addrFlavors }

# Set of flavored keys for each address flavor
addrKeysByFlavor = { flavor: set(d.keys())
                     for flavor, d in addrDefaultsByFlavor.items() }

# Mapping from key to address flavor
# For example 'home.addrLine1' maps to 'home'
keyToAddrFlavor = { key: flavor
                    for flavor, d in addrKeysByFlavor.items()
                        for key in d}

# Adds address methods to Person
class AddrHelper:
    # To be called from post_load()
    # Fill in missing defaults for all existing address flavors
    # But don't add any new address flavors
    def fill_addr_defaults(self):
        for flavor, sentinelKey in addrSentinelKeys.items():
            if sentinelKey in self.soul.values:
                self.soul.values.update((key, value) for key, value in addrDefaultsByFlavor[flavor].items()
                                        if not key in self.soul.values)

    # To be called from pre_save()
    # If an address flavor (other than home) is all defaults, remove it before saving to storage
    def remove_deleted_addrs(self):
        for flavor, sentinelKey in addrSentinelKeys.items():
            if sentinelKey in self.soul.values and flavor != 'home':
                if all(self.soul.values[key] == value for key, value in addrDefaultsByFlavor[flavor].items()):
                    for key in addrKeysByFlavor[flavor]:
                        del self.soul.values[key]

    def has_address(self, flavor):
        return self.has_value(addrSentinelKeys[flavor])

    def touch_address(self, flavor):
        if not self.has_address(flavor):
            self.protoValues.update((key, value) for key, value in addrDefaultsByFlavor[flavor].items()
                                    if key not in self.newValues)

    def get_addresses(self):
        return [flavor for flavor in addrFlavors if self.has_address(flavor)]

    def touch_addresses(self, flavors):
        for flavor in flavors:
            self.touch_address(flavor)

    def get_addr_value(self, flavor, key):
        self.touch_address(flavor)
        return self.get_value(join_key(flavor, key))

    def set_addr_value(self, flavor, key, value):
        self.touch_address(flavor)
        self.set_value(join_key(flavor, key), value)

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
