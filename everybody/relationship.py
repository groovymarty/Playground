# everybody.relationship

from body_and_soul import join_key
from basic_services import log_error

# A relationship specifier string can be a simple relat name (like 'father' or 'spouse')
# or a dotted form for indexed relationships (like "son.1" or "parent.2")
# Relationship specs are directly used as value keys in Person objects

simpleRelats = 'father', 'mother', 'husband', 'wife', 'spouse', 'livesWith'
indexedRelats = 'parent', 'child', 'son', 'daughter'
relatNames = {
    'father': "Father",
    'mother': "Mother",
    'husband': "Husband",
    'wife': "Wife",
    'spouse': "Spouse",
    'livesWith': "Lives With",
    'parent': "Parent",
    'child': "Child",
    'son': "Son",
    'daughter': "Daughter"
}

maxIndexKeys = {relat: relat+"_N" for relat in indexedRelats}
ucNameToRelat = {name.upper(): relat for relat, name in relatNames.items()}

def extract_relat(spec):
    return spec.split(".", 1)[0]

def format_relat(spec):
    if not spec:
        return ""
    elif "." in spec:
        (relat, index) = spec.split(".", 1)
        return "{} {}".format(relatNames[relat], index)
    else:
        return relatNames[spec]
      
def check_relat(value, maxIndex=100):
    # accept relat key names (dotted) as well as formatted ones (space separated)
    if "." in value:
        parts = value.strip().split(".", 1)
    else:
        # split used this way will split at whitespace and strip extra whitespace
        parts = value.rsplit(maxsplit=1)
    if len(parts) == 0:
        return ""
    elif len(parts) == 1:
        (name,) = parts
        index = None
    else:
        (name, index) = parts
    if name in relatNames:
        # relat key names may be used if typed perfectly
        relat = name
    else:
        ucName = name.upper()
        if ucName in ucNameToRelat:
            relat = ucNameToRelat[ucName]
        else:
            # Might be a simple relationship written as two words, like "Lives With",
            # in which case splitting was a mistake.  Join again and see if name is recognized.
            ucName = " ".join(parts).upper()
            if ucName in ucNameToRelat:
                relat = ucNameToRelat[ucName]
                index = None
            else:
                raise ValueError('"{}" is not a valid relationship'.format(value))
    if index is None:
        if relat in simpleRelats:
            return relat
        else:
            raise ValueError("{} is not a simple relationship (index missing)".format(relatNames[relat]))
    else:
        if relat in indexedRelats:
            try:
                i = int(index)
            except ValueError:
                raise ValueError('"{}" index is not a number'.format(value))
            if i > maxIndex:
                raise ValueError('"{}" index is too high'.format(value))
            return join_key(relat, str(i))
        else:
            raise ValueError("{} is not an indexed relationship".format(relatNames[relat]))

# Adds relationship methods to Person    
class RelatHelper:
    # to be called from post_load
    def count_indexed_relats(self):
        maximums = {maxIndexKeys[relat]: 0 for relat in indexedRelats}
        for key in self.soul.values:
            if "." in key:
                relat, index = key.split(".", 1)
                if relat in indexedRelats:
                    maxKey = maxIndexKeys[relat]
                    try:
                        index = int(index)
                        if index > maximums[maxKey]:
                            maximums[maxKey] = index
                    except ValueError:
                        log_error("RelatHelper.count_indexed_relats: index is not a number, ignoring: {}".format(key))
        self.soul.values.update(maximums)

    # to be called from pre_save
    def remove_deleted_relats(self):
        for key in simpleRelats:
            if key in self.soul.values and self.soul.values[key] is None:
                del self.soul.values[key]
                
    def generate_relat_specs(self, extra=0):
        yield 'father'
        yield 'mother'
        yield from self.generate_indexed_relat('parent', extra, maximum=2)
        yield 'husband'
        yield 'wife'
        yield 'spouse'
        yield 'livesWith'
        yield from self.generate_indexed_relat('son', extra)
        yield from self.generate_indexed_relat('daughter', extra)
        yield from self.generate_indexed_relat('child', extra)

    def generate_indexed_relat(self, relat, extra=0, maximum=None):
        n = self.get_value(maxIndexKeys[relat]) + extra
        if maximum is not None and n > maximum:
            n = maximum
        for i in range(1, n+1):
            yield join_key(relat, str(i))

    def set_relat(self, spec, whoId):
        self.set_value(spec, whoId)
        if "." in spec:
            relat, index = spec.split(".", 1)
            if relat in indexedRelats:
                maxKey = maxIndexKeys[relat]
                try:
                    index = int(index)
                    if index > self.get_value(maxKey):
                        self.set_value(maxKey, index)
                except ValueError:
                    log_error("RelatHelper.set_relat: index is not a number, ignoring: {}".format(spec))

    def find_max_index(self):
        return max(self.get_value(maxIndexKeys[relat]) for relat in indexedRelats)
