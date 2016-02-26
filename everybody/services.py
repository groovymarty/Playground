# everybody.services

db = None
root = None

def set_database(db1):
    global db
    db = db1

def database():
    return db

def set_tkRoot(root1):
    global root
    root = root1

def tkRoot():
    return root
