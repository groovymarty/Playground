# tkit.tkit

def make_array(x):
    if isinstance(x, str):
        return [x]
    else:
        try:
            len(x)
        except TypeError:
            x = [x]
        return x
