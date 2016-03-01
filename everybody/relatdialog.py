# everybody.relatdialog

from tkinter import *
from tkinter import ttk
from tkinter import simpledialog
from everybody import clipboard, services, personsearch
from everybody.relat import Relat
from everybody.personsearch import PersonSearch
from tkit.widgethelper import WidgetHelper

class RelatDialog(simpledialog.Dialog, WidgetHelper):
    def __init__(self, parent, genRelats1):
        self.genRelats = genRelats1
        simpledialog.Dialog.__init__(self, parent)

    def body(self, master):
        self.relatKey = ""
        self.personInstId = ""
        ttk.Label(master, text="Relationship").grid(row=0, column=0, sticky=(N,W))
        self.relatCbx = ttk.Combobox(master,
                                     values=[Relat.format_relat(key) for key in self.genRelats])
        self.relatCbx.grid(row=0, column=1, sticky=(N,W,E))
        self.bind_combobox_big_change(self.relatCbx, self.on_relat_big_change)
        ttk.Label(master, text="Person").grid(row=1, column=0, sticky=(N,W))
        self.personCbx = ttk.Combobox(master, width=30,
                                      values=clipboard.recent_people_labels())
        self.personCbx.grid(row=1, column=1, sticky=(N,W,E))
        self.bind_combobox_big_change(self.personCbx, self.on_person_big_change)
        self.searchButton = ttk.Button(master, text="Search", command=self.do_search)
        self.searchButton.grid(row=1, column=2, sticky=(N,W))
        self.message = ttk.Label(master)
        self.message.grid(row=2, column=0, columnspan=2, sticky=(N,W))
        return self.relatCbx

    def buttonbox(self):
        super().buttonbox()
        # remove binding with OK button
        self.unbind('<Return>')
        
    def set_message(self, text, modifier=''):
        self.message['style'] = self.join_style(modifier, 'TLabel')
        self.message['text'] = text

    def update_message(self):
        if self.personInstId:
            self.set_message("(Selected: {})".format(self.personInstId))
        else:
            self.set_message("")

    def on_relat_big_change(self, event):
        try:
            self.relatKey = Relat.check_relat(self.relatCbx.get())
            self.relatCbx.set(Relat.format_relat(self.relatKey))
            self.update_message()
        except ValueError as e:
            self.set_message(str(e), 'Error')

    def set_person(self, instId):
        if instId:
            person = services.database().lookup(instId)
            if person is not None:
                self.personInstId = instId
                self.personCbx.set(person.label)
                clipboard.add_recent_person(person)
                self.personCbx['values'] = clipboard.recent_people_labels()
                self.update_message()
            else:
                self.personInstId = ''
                self.set_message("{} not found".format(instId), 'Error')
        else:
            self.personInstId = ''
            self.personCbx.set("")
            self.update_message()

    def do_search(self):
        instId = PersonSearch(services.tkRoot()).result
        if instId:
            self.set_person(instId)          
          
    def on_person_big_change(self, event):
        label = self.personCbx.get().strip()
        if label:
            instId = clipboard.find_recent_person_by_label(label)
            if instId:
                self.set_person(instId)
            else:
                self.set_message("Searching...")
                self.update_idletasks()
                instId = personsearch.find_person_by_label(label)
                if instId:
                    self.set_person(instId)
                else:
                    self.personInstId = ''
                    self.set_message("{} not found".format(label), 'Error')               
        else:
            self.set_person('')        

    def apply(self):
        self.result = self.personInstId
