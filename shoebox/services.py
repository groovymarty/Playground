# shoebox.services

medits = []
pxs = []

def add_medit(medit):
    global medits
    medits.append(medit)

def remove_medit(medit):
    global medits
    if medit in medits:
        medits.remove(medit)

def get_medits():
    return list(medits)

def add_px(px):
    global pxs
    pxs.append(px)

def remove_px(px):
    global pxs
    if px in pxs:
        pxs.remove(px)

def get_pxs():
    return list(pxs)
