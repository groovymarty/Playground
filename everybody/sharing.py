# everybody.sharing

from body_and_soul import join_key, make_flavored
from everybody import address, relationship, person
from everybody.person import Person

# Set of unflavored keys governed by a "Use Shared Address" key
useSharedAddrKeys = set(address.addrDefaults.keys())
useSharedAddrKeys.remove('useSharedAddr')
useSharedAddrKeys.add('phone')

# Set of flavored "Use Shared Address" keys
useSharedAddrFlavors = { join_key(flavor, "useSharedAddr")
                         for flavor in address.addrFlavors }

# Set of keys governed by each "Use Shared" key
# For example this dictionary maps 'home.useSharedAddr' to a set containing 'home.addrLine1', 'home.phone', etc.
useSharedGroups = {'useSharedAnniv': {'anniversary'}}
useSharedGroups.update({ join_key(flavor, 'useSharedAddr'): make_flavored(flavor, useSharedAddrKeys)
                         for flavor in address.addrFlavors })
    
# Mapping from key to the corresponding "Use Shared" key, if any
# For example this dictionary maps 'home.addrLine1' to 'home.useSharedAddr'
# But keys with no sharing, like 'birthday', are not in the dictionary
keyToUseShared = { key: usKey
                   for usKey, usGroup in useSharedGroups.items()
                       for key in usGroup }

# Mapping from relat to sets of shared values dependent on that relationship
# Each group of shared values is represented by its "Use Shared" key
relatToUseShared = {
    'father': useSharedAddrFlavors,
    'mother': useSharedAddrFlavors,
    'husband': useSharedAddrFlavors | {'useSharedAnniv'},
    'wife': useSharedAddrFlavors | {'useSharedAnniv'},
    'spouse': useSharedAddrFlavors | {'useSharedAnniv'},
    'livesWith': useSharedAddrFlavors,
    'parent': useSharedAddrFlavors
}

class SharingHelper:
    def find_shared_value(self, key):
        usKey = keyToUseShared[key]
        sharer = self.find_sharer(usKey)
        if sharer is not None:
            self.person.set_value_error(usKey, None)
            return sharer.get_value(key)
        else:
            self.person.set_value_error(usKey, "Sharer not found")
            return person.get_default_value(key)

    def find_sharer(self, usKey):
        if usKey in self.sharerCache:
            return self.sharerCache[usKey]
        elif usKey == 'useSharedAnniv':
            sharer, spec = self.find_anniv_sharer()
        elif usKey in address.keyToAddrFlavor:
            flavor = address.keyToAddrFlavor[usKey]
            sharer, spec = self.find_addr_sharer(flavor)
        else:
            sharer = None
        if sharer is not None:
            self.sharerCache[usKey] = sharer
            self.sharerRelat[usKey] = spec
        return sharer

    def find_anniv_sharer(self):
        for spec in 'husband', 'wife', 'spouse':
            if spec in self.relatCache:
                who = self.relatCache[spec]
                if not who.get_value('useSharedAnniv'):
                    return who, spec
        return None, None

    def find_addr_sharer(self, flavor):
        for spec in self.generate_shared_addr_specs():
            if spec in self.relatCache:
                who = self.relatCache[spec]
                if not who.get_addr_value(flavor, 'useSharedAddr'):
                    return who, spec
        return None, None

    def generate_shared_addr_specs(self):
        for spec in 'livesWith', 'husband', 'wife', 'spouse', 'father', 'mother':
            yield spec
        yield from self.person.generate_indexed_relat('parent')
