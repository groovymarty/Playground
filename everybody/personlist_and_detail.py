# personlist_and_detail

from tkinter import *
from tkinter import ttk, messagebox
from everybody import services
from everybody.personlist import PersonList
from everybody.persondetail import PersonDetail

class PersonListAndDetail(ttk.Frame):
    def __init__(self, parent, peopleIter):
        super().__init__(parent)
        self.make_widgets(peopleIter)

    def make_widgets(self, peopleIter):
        self.addButton = ttk.Button(self, text="Add Person", command=self.do_add)
        self.addButton.grid(column=0, columnspan=2, row=0, sticky=(N,W))

        self.personList = PersonList(self, peopleIter)
        self.personList.grid(column=0, row=1, sticky=(N,W,E,S))

        self.personDetail = PersonDetail(self)
        self.personDetail.grid(column=1, row=1, sticky=(N,W,E,S))

        self.personList.bind("<<PersonSelect>>", self.on_person_select)
        self.personDetail.bind("<<PersonChange>>", self.on_person_change)
        self.personDetail.bind("<<PersonSave>>", self.on_person_save)

        self.grid_columnconfigure(1, weight=1, minsize=500)
        self.grid_rowconfigure(1, weight=1)

    def on_person_select(self, event):
        person = self.personList.get_selected()
        if person is not None:
            self.personDetail.set_person(person)

    def on_person_change(self, event):
        person = self.personDetail.get_person()
        if person is not None:
            self.personList.on_person_change(person)

    def on_person_save(self, event):
        person = self.personDetail.get_person()
        if person is not None:
            self.personList.on_person_save(person)

    def do_add(self):
        person = services.database().make_new("Per", "New Person")
        self.personList.add_person(person)
        self.personList.select(person)

    def check_unsaved_changes(self):
        unsaved = self.personList.get_all_unsaved()
        if not unsaved:
            return True
        else:
            names = [person.label for person in unsaved]
            return messagebox.askyesno(message=
"""The following people have unsaved changes:

{}

If you exit now, these changes will be lost.  Are you sure you want to continue?

Click "Yes" to discard your changes and exit the program.
Click "No" to go back to where you were without losing anything.""".format("\n".join(names)))
