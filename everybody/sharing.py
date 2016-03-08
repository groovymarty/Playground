# everybody.sharing

from body_and_soul import join_key, make_flavored
from everybody import addr

# Set of unflavored keys governed by a "Use Shared Address" key
useSharedAddrKeys = set(addr.addrDefaults.keys())
useSharedAddrKeys.remove('useSharedAddr')
useSharedAddrKeys.add('phone')

# Set of keys governed by each "Use Shared" key
# For example this dictionary maps 'home.useSharedAddr' to a set containing 'home.addrLine1', 'home.phone', etc.
useSharedGroups = {'useSharedAnniv': {'anniversary'}}
useSharedGroups.update({ join_key(flavor, 'useSharedAddr'): make_flavored(flavor, useSharedAddrKeys)
                                for flavor in addr.addrFlavors })
    
# Mapping from key to the corresponding "Use Shared" key, if any
# For example this dictionary maps 'home.addrLine1' to 'home.useSharedAddr'
# But keys with no sharing, like 'birthday', are not in the dictionary
keyToUseShared = { key: usKey
                   for usKey, usGroup in useSharedGroups.items()
                       for key in usGroup }
