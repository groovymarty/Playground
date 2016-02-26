# basic_data.checkers

# A "checker" is a function that tests if its argument is a legal data value.
# If so, it returns its argument in standard form.
# If not, it raises a ValueError with a suitable error message.
# Conversion to standard form can include stripping leading and trailing whitespace,
# fixing capitalization, etc.

# A "mapper" lets you translate values back and forth to an alternate form.
# For example you may store states as two-letter codes, but want to display them
# as fully spelled-out names.
# A mapper is an object (usually a class) with two methods:
# map_out(value) performs the "output" mapping (from the internal value to the alternate form)
# For example StateMapper.map_out returns the spelled-out name for a given two-letter state code.
# map_in(value) performs the "input" mapping (from the alternate form to the internal value)
# For example StateMapper.map_in returns the two-letter state code for a spelled-out name.
# When the value cannot be mapped, both methods return their arguments unchanged.
# map_in is usually implemented using a checker function

def check_required_str(value):
    val = value.strip()
    if len(val) == 0:
        raise ValueError('This field may not be left blank')
    else:
        return val
