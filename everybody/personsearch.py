# everybody.personsearch

from tkinter import *
from tkinter import ttk
from tkinter import simpledialog
from everybody import services, newperson
from everybody.personlist import PersonList
from everybody.newperson import NewPersonDialog

class PersonSearch(simpledialog.Dialog):
    def __init__(self, parent, withAdd=True):
        self.withAdd = withAdd
        self.newPerson = None
        simpledialog.Dialog.__init__(self, parent)

    def body(self, master):
        if self.withAdd:
            self.addButton = ttk.Button(master, text="Add Person", command=self.do_add)
            self.addButton.grid(column=0, columnspan=2, row=0, sticky=(N,W))

        people = services.database().generate_all('Per')
        self.personList = PersonList(master, people)
        self.personList.grid(column=0, row=1, sticky=(N,W,E,S))

        self.grid_columnconfigure(1, weight=1, minsize=500)
        self.grid_rowconfigure(1, weight=1)

        self.personList.tree.bind('<Double-1>', self.on_double_click)
        return None

    def do_add(self):
        result = NewPersonDialog(services.tkRoot()).result
        if result is not None:
            self.newPerson = newperson.make_new_person(result)
            newperson.generate_new_person_event(self.newPerson)
            self.ok()

    def on_double_click(self, event):
        self.ok()
      
    def apply(self):
        person = self.newPerson or self.personList.get_selected()
        if person is not None:
            self.result = person.instId
        else:
            self.result = ''

def find_person_by_label(label):
    people = services.database().generate_all('Per')
    return next((person.instId for person in people if person.label == label), '')
