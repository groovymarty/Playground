# everybody.relat

from body_and_soul import BodyHelper
from basic_services import log_error

class Relat:
    simpleRelats = 'father', 'mother', 'husband', 'wife', 'spouse'
    indexedRelats = 'parent', 'child', 'son', 'daughter'
    relatNames = {
        'father': "Father",
        'mother': "Mother",
        'husband': "Husband",
        'wife': "Wife",
        'spouse': "Spouse",
        'parent': "Parent",
        'child': "Child",
        'son': "Son",
        'daughter': "Daughter"
    }
    # see below...
    maxIndexKeys = None
    ucNameToRelat = None

    @staticmethod            
    def format_relat(key):
        if not key:
            return ""
        elif "." in key:
            (relat, index) = key.split(".", 2)
            return "{} {}".format(Relat.relatNames[relat], index)
        else:
            return Relat.relatNames[key]
          
    @staticmethod
    def check_relat(value):
        # accept relat key names (dotted) as well as formatted ones (space separated)
        if "." in value:
            parts = value.strip().split(".", 2)
        else:
            # split used this way will split at whitespace and strip extra whitespace
            parts = value.split(maxsplit=2)
        if len(parts) == 0:
            return ""
        elif len(parts) == 1:
            (name,) = parts
            index = None
        else:
            (name, index) = parts
        if name in Relat.relatNames:
            # relat key names may be used if typed perfectly
            relat = name
        else:
            ucName = name.upper()
            if ucName in Relat.ucNameToRelat:
                relat = Relat.ucNameToRelat[ucName]
            else:
                raise ValueError('"{}" is not a valid relationship'.format(value))
        if index is None:
            if relat in Relat.simpleRelats:
                return relat
            else:
                raise ValueError("{} is not a simple relationship (index missing)".format(Relat.relatNames[relat]))
        else:
            if relat in Relat.indexedRelats:
                try:
                    i = int(index)
                except ValueError:
                    raise ValueError('"{}" is not a valid indexed relationship'.format(value))
                if i > BodyHelper.maxIndex:
                    raise ValueError('"{}" index is too high'.format(value))
                return BodyHelper.join_key(relat, str(i))
            else:
                raise ValueError("{} is not an indexed relationship".format(Relat.relatNames[relat]))

Relat.maxIndexKeys = {relat: relat+"_N" for relat in Relat.indexedRelats}
Relat.ucNameToRelat = {name.upper(): relat for relat, name in Relat.relatNames.items()}

# Adds relationship methods to Person    
class RelatHelper:
    # to be called from post_load
    def count_indexed_relats(self):
        maximums = {Relat.maxIndexKeys[relat]: 0 for relat in Relat.indexedRelats}
        for key in self.soul.values:
            if key not in self.keyToAddrFlavor and "." in key:
                relat, index = key.split(".", 2)
                if relat in Relat.indexedRelats:
                    maxKey = Relat.maxIndexKeys[relat]
                    try:
                        index = int(index)
                        if index > maximums[maxKey]:
                            maximums[maxKey] = index
                    except ValueError:
                        log_error("RelatHelper.count_indexed_relats: index is not a number, ignoring: {}".format(key))
        self.soul.values.update(maximums)

    # to be called from pre_save
    def remove_deleted_relats(self):
        for key in Relat.simpleRelats:
            if key in self.soul.values and self.soul.values[key] is None:
                del self.soul.values[key]
                
    def generate_relats(self, extra=0):
        yield 'father'
        yield 'mother'
        yield from self.generate_indexed_relat('parent', extra, maximum=2)
        yield 'husband'
        yield 'wife'
        yield 'spouse'
        yield from self.generate_indexed_relat('son', extra)
        yield from self.generate_indexed_relat('daughter', extra)
        yield from self.generate_indexed_relat('child', extra)

    def generate_indexed_relat(self, relat, extra=0, maximum=None):
        n = int(self.get_value(Relat.maxIndexKeys[relat])) + extra
        if maximum is not None and n > maximum:
            n = maximum
        for i in range(1, n+1):
            yield self.join_key(relat, str(i))
