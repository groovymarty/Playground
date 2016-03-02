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
        self.instId = ""
        self.selector = ""
        self.errorMsgs = {}
        self.errorMsgKeys = 'relat', 'person', 'version'
        
        for row in range(0, 4):
            master.rowconfigure(row, pad=10)
        for column in range(0, 3):
            master.columnconfigure(column, pad=10)

        ttk.Label(master, text="Relationship").grid(row=0, column=0, sticky=W)
        self.relatCbx = ttk.Combobox(master,
                                     values=[Relat.format_relat(key) for key in self.genRelats])
        self.relatCbx.grid(row=0, column=1, sticky=(W,E))
        self.bind_combobox_big_change(self.relatCbx, self.on_relat_big_change)

        ttk.Label(master, text="Person").grid(row=1, column=0, sticky=W)
        self.personCbx = ttk.Combobox(master, width=30,
                                      values=clipboard.recent_people_labels())
        self.personCbx.grid(row=1, column=1, sticky=(W,E))
        self.bind_combobox_big_change(self.personCbx, self.on_person_big_change)

        self.searchButton = ttk.Button(master, text="Search", command=self.do_search)
        self.searchButton.grid(row=1, column=2, sticky=E)
        
        ttk.Label(master, text="Version").grid(row=2, column=0, sticky=W)
        self.versionCbx = ttk.Combobox(master)
        self.versionCbx.grid(row=2, column=1, sticky=(W,E))
        self.bind_combobox_big_change(self.versionCbx, self.on_version_big_change)

        self.statusLabel = ttk.Label(master)
        self.statusLabel.grid(row=3, column=0, columnspan=3, sticky=W)
        return self.relatCbx

    def buttonbox(self):
        simpledialog.Dialog.buttonbox(self)
        # remove binding with OK button and Enter key
        self.unbind('<Return>')
        
    def set_status(self, text, modifier=""):
        self.statusLabel['style'] = self.join_style(modifier, 'TLabel')
        self.statusLabel['text'] = text

    def update_status(self):
        if self.errorMsgs:
            messages = (self.errorMsgs[key] for key in self.errorMsgKeys if key in self.errorMsgs)
            self.set_status("\n".join(messages), 'Error')
        elif self.instId:
            self.set_status("(Selected: {})".format(self.instId))
        else:
            self.set_status("")

    def set_error_message(self, key, text):
        if text:
            self.errorMsgs[key] = text
        elif key in self.errorMsgs:
            del self.errorMsgs[key]

    def set_person(self, instId):
        if instId:
            person = services.database().lookup(instId)
            if person is not None:
                self.instId = instId
                self.personCbx.set(person.label)
                clipboard.add_recent_person(person)
                self.personCbx['values'] = clipboard.recent_people_labels()
                selectors = [value for value in person.generate_major_selectors()]
                self.versionCbx['values'] = selectors
                self.versionCbx.set(selectors[-1])
                self.set_error_message('person', "")
            else:
                self.instId = ""
                self.clear_versions()
                self.set_error_message('person', "{} not found".format(instId))
        else:
            self.instId = ""
            self.personCbx.set("")
            self.clear_versions()
            self.set_error_message('person', "")

    def clear_versions(self):
        self.versionCbx['values'] = []
        self.versionCbx.set("")
        self.set_error_message('version', "")

    def do_search(self):
        instId = PersonSearch(services.tkRoot()).result
        if instId:
            self.set_person(instId)
        self.update_status()
          
    def on_relat_big_change(self, event):
        try:
            self.relatKey = Relat.check_relat(self.relatCbx.get())
            self.relatCbx.set(Relat.format_relat(self.relatKey))
            self.set_error_message('relat', "")
        except ValueError as e:
            self.set_error_message('relat', str(e))
        self.update_status()

    def on_person_big_change(self, event):
        label = self.personCbx.get().strip()
        if label:
            instId = clipboard.find_recent_person_by_label(label)
            if instId:
                self.set_person(instId)
            else:
                self.set_status("Searching...")
                self.update_idletasks()
                instId = personsearch.find_person_by_label(label)
                if instId:
                    self.set_person(instId)
                else:
                    self.instId = ""
                    self.clear_versions()
                    self.set_error_message('person', '"{}" not found'.format(label))
        else:
            self.set_person("")
        self.update_status()
            
    def on_version_big_change(self, event):
        try:
            self.selector = services.database().check_selector(self.versionCbx.get())
            self.versionCbx.set(self.selector)
            self.set_error_message('version', "")
        except ValueError as e:
            self.selector = ""
            self.set_error_message('version', str(e))
        if self.selector and self.instId:
            person = services.database().lookup(self.instId)
            if person is not None and not person.has_version(self.selector):
                self.set_error_message('version', "Version {} not found".format(self.selector))
        self.update_status()

    def apply(self):
        self.result = self.instId
