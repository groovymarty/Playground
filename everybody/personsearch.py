# everybody.personsearch

from tkinter import *
from tkinter import ttk
from tkinter import simpledialog
from everybody import services
from everybody.personlist import PersonList

class PersonSearch(simpledialog.Dialog):
    def body(self, master):
        people = services.database().generate_all('Per')
        self.personList = PersonList(master, people)
        self.personList.pack(fill=BOTH, expand=1)
        self.personList.tree.bind('<Double-1>', self.on_double_click)
        master.pack(fill=BOTH, expand=1)
        return None
      
    def on_double_click(self, event):
        self.ok()
      
    def apply(self):
        person = self.personList.get_selected()
        if person is not None:
            self.result = person.instId
        else:
            self.result = ''

def find_person_by_label(label):
    people = services.database().generate_all('Per')
    return next((person.instId for person in people if person.label == label), '')
