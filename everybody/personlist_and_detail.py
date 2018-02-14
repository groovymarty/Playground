# personlist_and_detail

from tkinter import *
from tkinter import ttk, messagebox
from everybody import services, newperson
from everybody.personlist import PersonList
from everybody.persondetail import PersonDetail
from basic_services import log_debug
from basic_data import date

class PersonListAndDetail(ttk.Frame):
    def __init__(self, parent, peopleIter):
        super().__init__(parent)
        self.make_widgets(peopleIter)

    def make_widgets(self, peopleIter):
        self.topBar = Frame(self)
        self.topBar.grid(column=0, columnspan=2, row=0, sticky=(N,W))
        self.addButton = ttk.Button(self.topBar, text="Add Person", command=self.do_add)
        self.addButton.pack(side=LEFT)
        self.printButton = ttk.Button(self.topBar, text="Print", command=self.do_print)
        self.printButton.pack(side=LEFT)

        self.personList = PersonList(self, peopleIter)
        self.personList.grid(column=0, row=1, sticky=(N,W,E,S))

        self.personDetail = PersonDetail(self)
        self.personDetail.grid(column=1, row=1, sticky=(N,W,E,S))

        self.personList.bind("<<PersonSelect>>", self.on_person_select)
        self.personDetail.bind("<<PersonChange>>", self.on_person_change)
        self.personDetail.bind("<<PersonSave>>", self.on_person_save)
        services.tkRoot().bind("<<NewPerson>>", self.on_new_person)

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
        newperson.generate_new_person_event(person)

    def do_print(self):
        top = Toplevel()
        top.title("Everybody - Print")
        text = Text(top)
        text.pack(fill=BOTH, expand=True)
        text.configure(font=("helvetica", 12), tabs=("3i", "6i"))
        def print_person(person):
            addrLines = person.build_address()
            addrLines.extend([""] * (3 - len(addrLines)))
            text.insert(END, person.sortName+"\t"+addrLines[0]+"\tBDay:  "+date.format(person.birthday, slash=True)+"\n")
            text.insert(END, "\t"+addrLines[1]+"\tAnniv:  "+date.format(person.anniversary, slash=True)+"\n")
            text.insert(END, "\t"+addrLines[2]+"\n")
            text.insert(END, "\n")
        self.personList.for_each_person(print_person)

    def on_new_person(self, event):
        log_debug("Events", "got new person event")
        person = newperson.get_person_from_event(event)
        if person is not None and not self.personList.has_person(person):
            self.personList.add_person(person)

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
