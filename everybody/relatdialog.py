# everybody.relatdialog

from tkinter import *
from tkinter import ttk
from tkinter import simpledialog
from everybody import clipboard, services, personsearch
from everybody.relat import check_relat, format_relat
from everybody.personsearch import PersonSearch
from tkit.widgethelper import WidgetHelper

class RelatDialog(simpledialog.Dialog, WidgetHelper):
    def __init__(self, parent, genRelats, initValues=None):
        self.genRelats = genRelats
        self.initValues = initValues
        # we can't set the initial values until body() is called to create the widgets
        self.relatSpec = ""
        self.instId = ""
        self.selector = ""
        self.valueKeys = 'relatSpec', 'instId', 'selector'
        self.valueNames = {
            'relatSpec': "relationship",
            'instId': "person",
            'selector': "version"
        }
        self.errorMsgs = {}
        self.tolerateBlank = True
        simpledialog.Dialog.__init__(self, parent)

    def body(self, master):
        for row in range(0, 4):
            master.rowconfigure(row, pad=10)
        for column in range(0, 3):
            master.columnconfigure(column, pad=10)

        ttk.Label(master, text="Relationship").grid(row=0, column=0, sticky=W)
        self.relatCbx = ttk.Combobox(master,
                                     values=[format_relat(key) for key in self.genRelats])
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

        if self.initValues is not None:
            self.relatSpec, self.instId, self.selector = self.initValues
            self.set_relat(self.relatSpec)
            self.set_person(self.instId)
            self.set_version(self.selector)
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
            messages = (self.errorMsgs[key] for key in self.valueKeys if key in self.errorMsgs)
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

    def update_error_message(self, key):
        if not getattr(self, key) and not self.tolerateBlank:
            self.set_error_message(key, "You must select a {}.".format(self.valueNames[key]))
        else:
            self.set_error_message(key, "")

    def set_relat(self, relatSpec):
        try:
            self.relatSpec = check_relat(relatSpec)
            self.relatCbx.set(format_relat(self.relatSpec))
            self.update_error_message('relatSpec')
        except ValueError as e:
            self.relatSpec = ""
            self.set_error_message('relatSpec', str(e))

    def set_person(self, instId):
        if instId:
            person = services.database().lookup(instId)
            if person is not None:
                # different person?
                change = instId != self.instId
                # set up person
                self.instId = person.instId
                self.personCbx.set(person.label)
                self.set_error_message('instId', "")
                # move to top of recent people list
                clipboard.add_recent_person(person)
                self.personCbx['values'] = clipboard.recent_people_labels()
                # get major version selectors for this person
                selectors = [value for value in person.generate_major_selectors()]
                self.versionCbx['values'] = selectors
                # if different person, set selector for latest version
                if change:
                    self.selector = selectors[-1]
                    self.versionCbx.set(self.selector)
                    self.set_error_message('selector', "")
            else:
                self.instId = ""
                self.set_error_message('instId', "{} not found".format(instId))
        else:
            self.instId = ""
            self.personCbx.set("")
            self.update_error_message('instId')

    def set_version(self, selector):
        try:
            self.selector = services.database().check_selector(selector)
            self.versionCbx.set(self.selector)
            self.update_error_message('selector')
        except ValueError as e:
            self.selector = ""
            self.set_error_message('selector', str(e))
        if self.selector and self.instId:
            person = services.database().lookup(self.instId)
            if person is not None and not person.has_version(self.selector):
                self.set_error_message('selector', "Version {} not found".format(self.selector))

    def on_relat_big_change(self, event):
        self.set_relat(self.relatCbx.get())
        self.update_status()

    def on_person_big_change(self, event):
        label = self.personCbx.get().strip()
        if label:
            # Order of search:
            # 1. Check for match in recent person list
            # 2. Accept database ID if typed perfectly
            # 3. General search by name
            instId = clipboard.find_recent_person_by_label(label)
            if instId:
                self.set_person(instId)
            elif services.database().lookup(label):
                instId, selector = services.database().split_id(label)
                self.set_person(instId)
                if selector:
                    self.set_version(selector)
            else:
                self.set_status("Searching...")
                self.update_idletasks()
                instId = personsearch.find_person_by_label(label)
                if instId:
                    self.set_person(instId)
                else:
                    self.instId = ""
                    self.set_error_message('instId', '"{}" not found'.format(label))
        else:
            self.set_person("")
        self.update_status()

    def do_search(self):
        instId = PersonSearch(services.tkRoot()).result
        if instId:
            self.set_person(instId)
        self.update_status()

    def on_version_big_change(self, event):
        self.set_version(self.versionCbx.get())
        self.update_status()

    def validate(self):
        # Blank is no longer tolerated once you click OK
        self.tolerateBlank = False
        self.on_relat_big_change(None)
        self.on_person_big_change(None)
        self.on_version_big_change(None)
        if self.errorMsgs:
            self.update_status()
            return False
        else:
            return True

    def apply(self):
        self.result = self.relatSpec, self.instId, self.selector
