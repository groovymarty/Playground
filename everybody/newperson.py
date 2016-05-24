# everybody.newperson

from tkinter import *
from tkinter import ttk
from tkinter import simpledialog
from everybody import services
from tkit.widgethelper import WidgetHelper

class NewPersonDialog(simpledialog.Dialog, WidgetHelper):
    def __init__(self, parent):
        simpledialog.Dialog.__init__(self, parent)

    def body(self, master):
        for row in range(0, 3):
            master.rowconfigure(row, pad=10)

        ttk.Label(master, text="First Name").grid(row=0, column=0, sticky=W)
        self.firstNameEntry = ttk.Entry(master, width=30)
        self.firstNameEntry.grid(row=0, column=1, sticky=(W,E))

        ttk.Label(master, text="Last Name").grid(row=1, column=0, sticky=W)
        self.lastNameEntry = ttk.Entry(master, width=30)
        self.lastNameEntry.grid(row=1, column=1, sticky=(W,E))

        self.statusLabel = ttk.Label(master)
        self.statusLabel.grid(row=2, column=0, columnspan=2, sticky=W)
        return self.firstNameEntry

    def buttonbox(self):
        simpledialog.Dialog.buttonbox(self)
        # remove binding with OK button and Enter key
        self.unbind('<Return>')
        
    def set_status(self, text, modifier=""):
        self.statusLabel['style'] = self.join_style(modifier, 'TLabel')
        self.statusLabel['text'] = text

    def get_result(self):
        return self.firstNameEntry.get().strip(), self.lastNameEntry.get().strip()

    def validate(self):
        result = self.get_result()
        if not result[0] or not result[1]:
            self.set_status("Please enter first and last name", 'Error')
            return False
        else:
            return True

    def apply(self):
        self.result = self.get_result()

def make_new_person(dialogResult):
    person = services.database().make_new("Per", " ".join(dialogResult))
    person.set_value('firstName', dialogResult[0])
    person.set_value('lastName', dialogResult[1])
    person.save('current')
    return person

def generate_new_person_event(person):
    services.tkRoot().event_generate("<<NewPerson>>", x=person.instNum)

def get_person_from_event(event):
    services.database().lookup_with_tag_and_num("Per", event.x)
