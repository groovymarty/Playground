# shoebox.services

medits = []

def add_medit(medit):
    global medits
    print("adding", medit)
    medits.append(medit)

def remove_medit(medit):
    global medits
    if medit in medits:
        print("removing", medit)
        medits.remove(medit)

def get_medits():
    return list(medits)
