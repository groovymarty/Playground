# everybody.relat

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
    maxIndexKeys = None #see below

    @staticmethod            
    def format_relat(key):
        if "." in key:
            relat, index = key.split(".", 2)
            return "{} {}".format(Relat.relatNames[relat], index)
        else:
            return Relat.relatNames[key]
          
    @staticmethod
    def check_relat(value):
        pass

# Max index key for each indexed relationship
Relat.maxIndexKeys = {relat: relat+"_N" for relat in Relat.indexedRelats}

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

