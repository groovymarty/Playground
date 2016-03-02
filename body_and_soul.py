# body_and_soul

"""
Body is base class for all application domain objects.
Soul provides database connection for loading and saving values.
Values are stored in three dictionaries: Soul.values, Body.newValues and Body.protoValues
Soul.values are the original values read from the database,
Body.newValues represent local changes that haven't yet been saved.
Body.protoValues are new values that were not read from database, but we want
it to look like they were.  They are folded into newValues on saving.
Body always has soul, but soul is loaded on demand (on first access to a value).
Prior to loading, Soul.values is None.
Label is a special property (not in dictionary) that can be read without triggering load.
If not loaded, soul provides "hint label" (which comes from file name).
Otherwise body provides "real label", typically based on other values.
Because soul is loaded on demand, Body.save() might be called before soul
is loaded.  Body.save() detects this case and loads soul before saving.
Therefore soul.save() can assume soul has been loaded.
Default soul methods are for testing and illustration only.
"""

from basic_services import log_debug

class Body:
    defaultValues = {}
    checkers = {}

    def __init__(self, soul):
        self.soul = soul
        self.newValues = {}
        self.protoValues = {}
        self.valueErrors = {}

    def copy(self):
        dup = self.__class__(self.soul.copy())
        dup.newValues = self.newValues.copy()
        dup.protoValues = self.protoValues.copy()
        return dup

    def load(self, selector='current', check=True):
        log_debug("Body.load", "Loading {} {}".format(self.instId, selector))
        freshLoad = self.soul.load(self.defaultValues, selector)
        self.newValues.clear()
        self.protoValues.clear()
        self.valueErrors.clear()
        # Do post-load processing on initial load
        if freshLoad:
            self.post_load()
        # Check and silently update soul.values on loading
        # This takes care of minor things like stripping white space from strings
        # Leave bad values in place and save exceptions in self.valueErrors
        if freshLoad or check:
            for key, checker in self.checkers.items():
                if key in self.soul.values:
                    try:
                        self.soul.values[key] = checker(self.soul.values[key])
                    except ValueError as e:
                        self.valueErrors[key] = e

    # Allows subclass to process values after they are loaded but before optional check
    def post_load(self):
        pass

    # Allows subclass to process values after they are updated but before writing to storage
    def pre_save(self):
        pass

    def save(self, selector='advance'):
        log_debug("Body.save", "Saving {} {}".format(self.instId, selector))
        if self.soul.values is None:
            self.soul.load(self.defaultValues)
        # Fold protoValues into newValues
        self.newValues.update((key, value) for key, value in self.protoValues.items() if key not in self.newValues)
        self.protoValues.clear()
        # save has two steps
        # step 1, update soul.values with newValues
        self.soul.save_update(self.newValues, selector)
        self.newValues.clear()
        self.pre_save()
        # step 2, write values to persistent storage
        self.soul.save_write(self.label)

    def ensure_loaded(self):
        if self.soul.values is None:
            self.load()

    def is_new(self):
        return self.soul.is_new()

    @property
    def instId(self):
        return self.soul.get_inst_id()

    def __eq__(self, other):
        return self.instId == other.instId

    def __ne__(self, other):
        return not self == other

    @property
    def loadErrorMsg(self):
        return self.soul.get_load_error_msg()

    @property
    def label(self):
        if self.soul.values is None:
            return self.soul.get_hint_label()
        else:
            return self.get_real_label()

    def get_real_label(self):
        return ""

    @property
    def version(self):
        return self.soul.get_version()

    def is_latest(self):
        return not self.has_version('next')

    def has_version(self, selector):
        return self.soul.get_version(selector) is not None

    def get_version(self, selector='current'):
        return self.soul.get_version(selector)
      
    def get_all_versions(self):
        return self.soul.get_all_versions()

    def check_version(self, value):
        return self.soul.check_version(value)

    def format_version(self, version):
        return self.soul.format_version(version)

    def is_same_minor_series(self, version1, version2):
        return self.soul.is_same_minor_series(version1, version2)

    def has_value(self, key):
        self.ensure_loaded()
        return key in self.newValues or key in self.protoValues or key in self.soul.values

    def get_value(self, key):
        self.ensure_loaded()
        # Since we don't allow a key to occur in protoValues if it's already in soul.values,
        # we can check soul.values second as this is the more common case.
        if key in self.newValues:
            return self.newValues[key]
        elif key in self.soul.values:
            return self.soul.values[key]
        elif key in self.protoValues:
            return self.protoValues[key]
        else:
            return None

    def set_value(self, key, value):
        self.ensure_loaded()
        if key not in self.soul.values or value != self.soul.values[key]:
            if key not in self.protoValues or value != self.protoValues[key]:
                self.newValues[key] = value
            else:
                # Value just written matches proto value, so delete new value if any
                if key in self.newValues:
                    del self.newValues[key]
        else:
            # Value just written matches soul value, so delete our value if any
            # No worry about proto value because key in soul.values means key not in protoValues
            if key in self.newValues:
                del self.newValues[key]

    # Proto values must be set to their default value (can be changed with set_value)
    # Note you cannot set a proto value for an existing field!
    def set_proto_value(self, key, defaultValue):
        self.ensure_loaded()
        if self.has_value(key):
            raise KeyError("Proto value may not be set for an existing field:", key)
        else:
            self.protoValues[key] = defaultValue

    def check_value(self, key, value):
        if key in self.checkers:
            return self.checkers[key](value)
        else:
            return value

    def check_one(self, key):
        if key in self.checkers:
            try:
                self.set_value(key, self.checkers[key](self.get_value(key)))
                if key in self.valueErrors:
                    del self.valueErrors[key]
            except ValueError as e:
                self.valueErrors[key] = e

    def check_all(self):
        # Check all values and put all changes in self.newValues
        # Leave bad values in place and save exceptions in self.valueErrors
        self.valueErrors.clear()
        for key, checker in self.checkers.items():
            if key in self.soul.values or key in self.newValues:
                try:
                    self.set_value(key, checker(self.get_value(key)))
                except ValueError as e:
                    self.valueErrors[key] = e

    def set_value_error(self, key, e):
        if e is None:
            if key in self.valueErrors:
                del self.valueErrors[key]
        else:
            self.valueErrors[key] = e

    def is_changed(self, key):
        return key in self.newValues

    def is_changed_set(self, keys):
        return bool(keys & self.newValues.keys())

    def is_any_changed(self):
        return bool(self.newValues)

    def discard_changes(self):
        self.newValues.clear()
        self.protoValues.clear()

    def is_error(self, key):
        return key in self.valueErrors

    def is_error_set(self, keys):
        return bool(keys & self.valueErrors.keys())

    def is_any_error(self):
        return self.loadErrorMsg or self.valueErrors

    @classmethod
    def make_property(classObj, key):
        def getter(self):
            return self.get_value(key)
        def setter(self, value):
            self.set_value(key, value)
        setattr(classObj, key, property(getter, setter))

    @classmethod
    def make_all_properties(classObj):
        for key in classObj.defaultValues:
            if not "." in key:
                classObj.make_property(key)

    def compare_keys(self):
        # omit protoValues because, if present, they are defaults and therefore unchanged
        return self.newValues.keys() | self.soul.values.keys()

    def compare(self, other):
        return {key for key in self.compare_keys() | other.compare_keys()
                if self.get_value(key) != other.get_value(key)}

class Soul:
    def __init__(self):
        self.values = None

    def copy(self):
        dup = Soul()
        dup.values = self.values
        return dup

    def load(self, defaultValues, selector='current'):
        if self.values is None or selector != 'current':
            self.values = defaultValues.copy()
            return True #Really did pretend to load
        else:
            return False #Already loaded

    # save has two steps
    # step 1, update values with newValues
    def save_update(self, newValues, selector='advance'):
        if self.values is None:
            raise Exception("Soul must be loaded before saving")
        self.values.update(newValues)

    # step 2, write values to persistent storage
    def save_write(self, label=""):
        pass

    def is_new(self):
        return False

    def get_inst_id(self):
        return ""

    def get_hint_label(self):
        return ""

    def get_load_error_msg(self):
        return ""

    def get_version(self, selector='current'):
        if selector == 'current':
            return 1,0
        else:
            return None
          
    def get_all_versions(self):
        return [(1,0)]

    @staticmethod
    def check_version(value):
        return len(value.split(".")) == 2

    @staticmethod
    def format_version(version):
        return "%d.%d" % version

    @staticmethod
    def is_same_minor_series(version1, version2):
        return version1[0] == version2[0]

# Adds some methods for handling structured keys like "work.phone" and "child.3"
class BodyHelper:
    maxIndex = 100

    @staticmethod
    def join_key(*parts):
        return ".".join(parts)

    @staticmethod
    def make_flavored(flavor, d):
        return {BodyHelper.join_key(flavor, key): value for key, value in d.items()}
