# everybody.clipboard

# tuples of (instId, label)
recentPeople = []

def recent_people():
    return recentPeople

def add_recent_person(person):
    global recentPeople
    newInstId = person.instId
    newList = [t for t in recentPeople if t[0] != newInstId]
    newList.insert(0, (newInstId, person.label))
    recentPeople = newList[0:10]
