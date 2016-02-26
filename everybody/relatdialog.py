# everybody.relatdialog

from tkinter import *
from tkinter import ttk
from tkinter import simpledialog
from everybody import clipboard, services, personsearch
from everybody.person import Person
from tkit.widgethelper import WidgetHelper

class RelatDialog(simpledialog.Dialog, WidgetHelper):
    def body(self, master):
        ttk.Label(master, text="Relationship").grid(row=0, column=0, sticky=(N,W))
        self.relatCbx = ttk.Combobox(master,
                                     values=[Person.relatNames[relat] for relat in Person.relatKeys])
        self.relatCbx.grid(row=0, column=1, sticky=(N,W,E))
        ttk.Label(master, text="Person").grid(row=1, column=0)
        self.personInstId = ''
        self.personCbx = ttk.Combobox(master, width=30,
                                      values=[t[1] for t in clipboard.recent_people()])
        self.personCbx.grid(row=1, column=1, sticky=(N,W,E))
        self.bind_combobox_big_change(self.personCbx, self.on_person_big_change)
        self.message = ttk.Label(master)
        self.message.grid(row=2, column=0, columnspan=2, pady=5, sticky=(N,W))
        return self.relatCbx

    def buttonbox(self):
        super().buttonbox()
        # remove binding with OK button
        self.unbind('<Return>')

    def on_person_big_change(self, event):
        self.message['style'] = 'TLabel'
        self.message['text'] = ""
        self.personInstId = ''
        person = None
        value = self.personCbx.get().strip()
        if value:
            for instId, label in clipboard.recent_people():
                if value == label:
                    person = services.database().lookup(instId)
                    break
            if person is None:
                self.message['text'] = "Searching..."
                self.update_idletasks()
                person = personsearch.find_person_by_label(value)
            if person is None:
                self.message['style'] = 'Error.TLabel'
                self.message['text'] = "{} not found".format(value)
            else:
                self.personInstId = person.instId
                self.message['text'] = "(Selected: {})".format(self.personInstId)
                clipboard.add_recent_person(person)

    def apply(self):
        self.result = None
