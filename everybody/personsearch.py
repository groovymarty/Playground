# everybody.personsearch

from everybody import services

def find_person_by_label(label):
    for person in services.database().generate_all('Per'):
        if person.label == label:
            return person
    return None
