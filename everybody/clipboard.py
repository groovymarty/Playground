# everybody.clipboard

# tuples of (instId, label)
recentPeople = []

def recent_people():
    return recentPeople
  
def recent_people_inst_ids():
    return [t[0] for t in recentPeople]
  
def recent_people_labels():
    return [t[1] for t in recentPeople]
  
def find_recent_person_by_label(label):
    return next((t[0] for t in recentPeople if t[1] == label), '')

def add_recent_person(person):
    global recentPeople
    newInstId = person.instId
    newList = [t for t in recentPeople if t[0] != newInstId]
    newList.insert(0, (newInstId, person.label))
    recentPeople = newList[0:10]
