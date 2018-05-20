# tkit.tkit

def make_array(x):
    try:
        len(x)
    except TypeError:
        x = [x]
    return x
