# persondetail

from tkinter import *
from tkinter import ttk
from tkinter import messagebox, simpledialog
from everybody import services, clipboard
from everybody.person import Person
from everybody.relat import Relat
from everybody.relatdialog import RelatDialog
from basic_data import gender, us_state, maritalstatus
from basic_services import log_debug, log_error
from tkit.widgetgarden import WidgetGarden
from PIL import Image, ImageDraw, ImageTk

class PersonDetail(ttk.Frame, WidgetGarden):
    labelText = {
        'namePrefix': "Name Prefix",
        'usePrefix': "Use Prefix",
        'firstName': "First Name",
        'middleName': "Middle Name",
        'useMiddleName': "Use Middle Name",
        'lastName': "Last Name",
        'nameSuffix': "Name Suffix",
        'useSuffix': "Use Suffix",
        'nickName': "Nickname",
        'useNickName': "Use Nickname",
        'gender': "Gender",
        'maidenName': "Maiden Name",
        'birthday': "Birthday",
        'maritalStatus': "Marital Status",
        'anniversary': "Anniversary",
        'deathDate': "DOD",
        'deceased': "Deceased",
        'home.phone': "Home Phone",
        'work.phone': "Work Phone",
        'seasonal.phone': "Seasonal Phone",
        'other.phone': "Other Phone",
        'mobile.phone': "Mobile Phone",
        'email': "Email"
    }
    addrLabelText = {
        'addrLine1': "Address Line 1",
        'addrLine2': "Address Line 2",
        'addrLine3': "Address Line 3",
        'useLine3': "Use Line 3",
        'city': "City",
        'state': "State",
        'zipCode': "ZIP Code",
        'country': "Country",
        'useCountry': "Use Country",
    }
    mappers = {
        'gender': gender.GenderMapper,
    }
    addrMappers = {
        'state': us_state.StateMapper
    }

    # Quantum mode lets you edit and save any version
    quantumMode = False

    def __init__(self, parent, person=None):
        ttk.Frame.__init__(self, parent)
        WidgetGarden.__init__(self)
        self.person = person
        self.diffs = set()
        self.diffVersion = None
        self.readOnly = person is None
        self.addrTabIds = {}
        self.make_styles()
        self.make_images()
        self.make_widgets()
        self.load_all()
        self.update_all()

    def make_styles(self):
        #TODO: How to check if this has already been done?
        s = ttk.Style()
        s.configure('Changed.TLabel', background='yellow')
        s.configure('Changed.TCheckbutton', background='yellow')
        s.configure('Error.TLabel', background='orange')
        s.configure('Error.TCheckbutton', background='orange')
        s.configure('Delta.TLabel', background='lightblue')
        s.configure('Delta.TCheckbutton', background='lightblue')

    def make_images(self):
        self.tabImageChanged = ImageTk.PhotoImage(Image.new('RGB', (15,15), color='yellow'))
        self.tabImageError = ImageTk.PhotoImage(Image.new('RGB', (15,15), color='orange'))
        self.tabImageDelta = ImageTk.PhotoImage(Image.new('RGB', (15,15), color='lightblue'))

    def make_widgets(self):
        self.begin_layout(self, 2)
        self.grid_columnconfigure(0, weight=1)
        self.make_top_frame()
        self.make_relat_heading()
        self.next_row()
        self.make_name_frame()
        self.make_relat_frame()
        self.rowconfigure(self.curRow, pad=15)
        self.next_row()
        self.make_addr_frame()
        self.next_row()
        self.make_msg_frame()
        self.next_row()
        self.make_nav_frame()
        self.end_layout()

    def make_top_frame(self):
        topFrame = ttk.Frame(self.curParent)
        self.grid_widget(topFrame, sticky=(N,W,E))
        topFrame.grid_columnconfigure(0, weight=1)
        self.topLabel = ttk.Label(topFrame, anchor='center', justify='center')
        self.topLabel.grid(row=0, column=0, sticky=(N,W,E))
        self.next_col()

    def make_name_frame(self):
        nameFrame = ttk.Frame(self.curParent)
        self.grid_widget(nameFrame, sticky=(N,W,E))
        self.begin_layout(nameFrame, 3)
        nameFrame.grid_columnconfigure(1, weight=1)
        self.make_entry('namePrefix')
        self.make_checkbutton('usePrefix')
        self.next_row()
        self.make_entry('firstName')
        self.next_row()
        self.make_entry('middleName')
        self.make_checkbutton('useMiddleName')
        self.next_row()
        self.make_entry('lastName')
        self.next_row()
        self.make_entry('nameSuffix')
        self.make_checkbutton('useSuffix')
        self.next_row()
        self.make_entry('nickName')
        self.make_checkbutton('useNickName')
        self.next_row()
        self.make_entry('maidenName')
        self.next_row()
        self.make_combobox('gender', gender.genderNames+["Unknown"], width=10)
        self.next_row()
        self.make_date('birthday')
        self.next_row()
        self.make_combobox('maritalStatus', maritalstatus.maritalStatusNames+["Unknown"], width=10)
        self.next_row()
        self.make_date('anniversary')
        self.next_row()
        self.make_date('deathDate')
        self.make_checkbutton('deceased')
        self.next_row()
        self.make_entry('mobile.phone')
        self.next_row()
        self.make_entry('email')
        self.end_layout()
        self.next_col()

    def make_addr_frame(self):
        self.addrNb = ttk.Notebook(self.curParent)
        self.grid_widget(self.addrNb, sticky=(N,W,E))
        self.addrNb.bind("<<NotebookTabChanged>>", self.on_addr_tab_change)
        for i, flavor in enumerate(Person.addrFlavors):
            childFrame = ttk.Frame(self.addrNb)
            self.addrNb.add(childFrame, text=Person.addrNames[flavor], compound=LEFT)
            self.addrTabIds[flavor] = i
            self.begin_layout(childFrame, 3)
            childFrame.grid_columnconfigure(1, weight=1)
            self.make_entry(Person.join_key(flavor, 'addrLine1'))
            self.next_row()
            self.make_entry(Person.join_key(flavor, 'addrLine2'))
            self.next_row()
            self.make_entry(Person.join_key(flavor, 'addrLine3'))
            self.make_checkbutton(Person.join_key(flavor, 'useLine3'))
            self.next_row()
            self.make_entry(Person.join_key(flavor, 'city'))
            self.next_row()
            self.make_combobox(Person.join_key(flavor, 'state'), us_state.stateNames+["Unknown"], width=20)
            self.next_row()
            self.make_entry(Person.join_key(flavor, 'zipCode'))
            self.next_row()
            self.make_entry(Person.join_key(flavor, 'country'))
            self.make_checkbutton(Person.join_key(flavor, 'useCountry'))
            self.next_row()
            self.make_entry(Person.join_key(flavor, 'phone'))
            self.end_layout()
        self.next_col()

    def make_relat_heading(self):
        self.addRelatButton = ttk.Button(self.curParent, text="Add Relationship", command=self.do_add_relat)
        self.grid_widget(self.addRelatButton, sticky=(S,W))

    def make_relat_frame(self):
        relatFrame = ttk.Frame(self.curParent)
        self.grid_widget(relatFrame, rowspan=2, sticky=(N,W,E,S))
        relatFrame.grid_columnconfigure(0, weight=1)
        relatFrame.grid_rowconfigure(0, weight=1)
        self.relatTree = ttk.Treeview(relatFrame, height=5, show='tree', columns='who')
        self.relatTree.grid(row=0, column=0, sticky=(N,W,E,S))
        self.relatTree.column('#0', width=90)
        #self.relatTree.heading('#0', text="Relationship")
        self.relatTree.column('who', width=200)
        #self.relatTree.heading('who', text="Person")
        #self.relatTree.column('version', width=60)
        #self.relatTree.heading('version', text="Version")
        sb = ttk.Scrollbar(relatFrame, orient=VERTICAL, command=self.relatTree.yview)
        sb.grid(row=0, column=1, sticky=(N,S))
        self.relatTree['yscrollcommand'] = sb.set
        self.next_col()

    def make_msg_frame(self):
        self.errorMsgs = ttk.Label(self.curParent)
        self.grid_widget(self.errorMsgs, columnspan=self.numCols, sticky=(N,W,E))

    def make_nav_frame(self):
        navFrame = ttk.Frame(self.curParent)
        self.grid_widget(navFrame, columnspan=self.numCols, sticky=(N,W,E))
        navFrame.grid_columnconfigure(1, weight=1)

        self.discardButton = ttk.Button(navFrame, text="Discard Changes", command=self.do_discard)
        self.discardButton.grid(row=0, column=0, sticky=W)
        self.quantumSaveButton = ttk.Button(navFrame, text="Quantum Save", command=self.do_save)
        self.saveMinorButton = ttk.Button(navFrame, text="Save Minor", command=self.do_save_minor)
        if self.quantumMode:
            self.quantumSaveButton.grid(row=0, column=1)
            self.saveMinorButton.grid(row=0, column=2)
        else:
            self.saveMinorButton.grid(row=0, column=1, columnspan=2)
        self.saveMajorButton = ttk.Button(navFrame, text="Save Major", command=self.do_save_major)
        self.saveMajorButton.grid(row=0, column=3, sticky=E)

        self.firstButton = ttk.Button(navFrame, text="First", command=self.go_to_first)
        self.firstButton.grid(row=1, column=0, sticky=W)
        verFrame = ttk.Frame(navFrame)
        verFrame.grid(row=1, rowspan=2, column=1, columnspan=2)
        self.latestButton = ttk.Button(navFrame, text="Latest", command=self.go_to_latest)
        self.latestButton.grid(row=1, column=3, sticky=E)

        self.fromLeftLabel = ttk.Label(verFrame)
        self.fromLeftLabel.grid(row=0, column=0)
        self.versionLabel = ttk.Label(verFrame)
        self.versionLabel.grid(row=0, column=1)
        self.fromRightLabel = ttk.Label(verFrame)
        self.fromRightLabel.grid(row=0, column=2)

        self.prevButton = ttk.Button(navFrame, text="Previous", command=self.go_to_previous)
        self.prevButton.grid(row=2, column=0, sticky=W)
        self.nextButton = ttk.Button(navFrame, text="Next", command=self.go_to_next)
        self.nextButton.grid(row=2, column=3, sticky=E)

    def on_var_change(self, key):
        if self.person is not None:
            self.person.set_value(key, self.read_var(key))
            self.update_widget_style(key)
            if key in Person.keyToAddrFlavor:
                self.update_addr_tab(Person.keyToAddrFlavor[key])
            self.update_top()
            self.update_save_buttons()
            self.event_generate('<<PersonChange>>')

    def on_big_change(self, event):
        if self.person is not None:
            key = self.widgetToKey[event.widget]
            self.person.check_one(key)
            # We do want to trigger on_trace_write here...
            self.write_var(key, self.person.get_value(key))
            self.update_error_msgs()

    def update_error(self, key, e):
        if self.person is not None:
            self.person.set_value_error(key, e)
            self.update_error_msgs()

    def update_widgets(self):
        for key in self.vars:
            self.update_widget_style(key)
            self.set_widget_enable(key, not self.readOnly)

    def update_widget_style(self, key):
        if self.person is not None:
            if self.person.is_error(key):
                self.set_widget_style(key, 'Error')
            elif self.person.is_changed(key):
                self.set_widget_style(key, 'Changed')
            elif key in self.diffs:
                self.set_widget_style(key, 'Delta')
            else:
                self.set_widget_style(key)
        else:
            self.set_widget_style(key)

    def on_addr_tab_change(self, event):
        flavor = self.get_cur_addr_tab()
        self.load_addr_vars(flavor)
        # Do this to prevent focus from jumping to first widget in address frame when you click tab
        self.entries[Person.join_key(flavor, 'addrLine1')].state(['!focus'])
        self.update_top()

    def get_cur_addr_tab(self):
        return Person.addrFlavors[self.addrNb.index(self.addrNb.select())]

    def load_addr_vars(self, flavor):
        if self.person is not None:
            self.person.touch_address(flavor)
        self.load_vars(Person.addrDefaultsByFlavor[flavor])

    def update_addr_tabs(self):
        for flavor in Person.addrFlavors:
            self.update_addr_tab(flavor)

    def update_addr_tab(self, flavor):
        if self.person is not None:
            keys = Person.addrKeysByFlavor[flavor]
            if self.person.is_error_set(keys):
                self.set_addr_tab_image(flavor, self.tabImageError)
            elif self.person.is_changed_set(keys):
                self.set_addr_tab_image(flavor, self.tabImageChanged)
            elif keys & self.diffs:
                self.set_addr_tab_image(flavor, self.tabImageDelta)
            else:
                self.set_addr_tab_image(flavor)
        else:
            self.set_addr_tab_image(flavor)

    def set_addr_tab_image(self, flavor, tabImage=None):
        self.addrNb.tab(self.addrTabIds[flavor], image=tabImage or "")

    def get_person(self):
        return self.person

    def set_person(self, person):
        self.person = person
        self.clear_diffs()
        self.load_all()
        self.update_all()
        self.event_generate('<<PersonChange>>')
        clipboard.add_recent_person(self.person)

    def clear_diffs(self):
        self.diffs = set()
        self.diffVersion = None

    def load_vars(self, defaults=Person.defaultValues):
        if self.person is not None:
            # Clear person temporarily to block the activity of on_trace_write()
            person = self.person
            self.person = None
            for key in defaults:
                if key in self.vars:
                    self.write_var(key, person.get_value(key))
            self.person = person
        else:
            for key, value in defaults.items():
                if key in self.vars:
                    self.write_var(key, value)

    def load_relats(self):
        self.relatTree.delete(*self.relatTree.get_children())
        if self.person is not None:
            for relat in Relat.simpleRelats:
                who = self.person.get_value(relat)
                if who is not None:
                    self.relatTree.insert('', END, iid=relat, text=Relat.relatNames[relat], values=who)

    def load_all(self):
        self.load_vars()
        self.load_addr_vars(self.get_cur_addr_tab())
        self.load_relats()

    def do_add_relat(self):
        if self.person is not None:
            RelatDialog(services.tkRoot(), self.person.generate_relats(extra=3))

    def do_discard(self):
        if self.person is not None:
            self.person.discard_changes()
            self.person.check_all()  # Required fields might now be blank
            self.clear_diffs()
            self.load_all()
            self.update_all()
            self.event_generate('<<PersonChange>>')

    def do_save(self, selector="current"):
        if self.person is not None:
            if not self.confirm_save_with_errors():
                return
            self.person.save(selector)
            self.update_all()
            self.event_generate('<<PersonSave>>')
            clipboard.add_recent_person(self.person)

    def do_save_minor(self):
        if self.person is not None:
            self.do_save('advance_minor' if not self.person.is_new() else 'current')

    def do_save_major(self):
        if self.person is not None:
            self.do_save('advance_major' if not self.person.is_new() else 'current')

    def go_to_version(self, selector, diff=False):
        if self.person is not None and self.person.has_version(selector):
            if not self.confirm_unsaved_changes("move to a different version"):
                return
            if diff:
                prior = self.person.copy()
                self.person.load(selector)
                # Make sure both are populated with same addresses before comparing
                self.person.touch_addresses(prior.get_addresses())
                prior.touch_addresses(self.person.get_addresses())
                self.diffs = self.person.compare(prior)
                self.diffVersion = prior.version
            else:
                self.person.load(selector)
                self.clear_diffs()
            self.load_all()
            self.update_all()
            self.event_generate('<<PersonChange>>')

    def go_to_first(self):
        self.go_to_version('first')

    def go_to_latest(self):
        self.go_to_version('latest')

    def go_to_previous(self):
        self.go_to_version('previous', diff=True)

    def go_to_next(self):
        self.go_to_version('next', diff=True)

    def update_top(self):
        if self.person is not None:
            lines = [self.person.fullName]
            lines.extend(self.person.build_address(self.get_cur_addr_tab()))
        else:
            lines = [""]
        if len(lines) < 4:
            blankLines = "\n" * (4 - len(lines))
        else:
            blankLines = ""
        self.topLabel['text'] = "\n".join(lines) + blankLines

    def update_error_msgs(self):
        if self.person is not None:
            if self.person.is_any_error():
                lines = []
                if self.person.loadErrorMsg:
                    lines.append(self.person.loadErrorMsg)
                lines.extend(self.format_error_msg(key, str(e)) for key, e in self.person.valueErrors.items())
                self.errorMsgs['text'] = "\n".join(lines)
                self.errorMsgs['style'] = 'Error.TLabel'
            else:
                self.errorMsgs['text'] = ""
                self.errorMsgs['style'] = 'TLabel'

    def format_error_msg(self, key, msg):
        if key in Person.keyToAddrFlavor:
            return "{} {}: {}".format(Person.addrNames[Person.keyToAddrFlavor[key]], self.labelText[key], msg)
        else:
            return "{}: {}".format(self.labelText[key], msg)

    def update_save_buttons(self):
        if self.person is not None:
            anyChanged = self.person.is_any_changed()
            okToSave = self.person.is_ok_to_save()
            self.enable_widget(self.discardButton, anyChanged)
            self.enable_widget(self.quantumSaveButton, anyChanged and okToSave)
            self.enable_widget(self.saveMinorButton, anyChanged and okToSave)
            self.enable_widget(self.saveMajorButton, okToSave)
        else:
            self.disable_widget(self.discardButton)
            self.disable_widget(self.quantumSaveButton)
            self.disable_widget(self.saveMinorButton)
            self.disable_widget(self.saveMajorButton)

    def update_nav_buttons(self):
        if self.person is not None:
            hasPrev = self.person.has_version('previous')
            hasNext = self.person.has_version('next')
            self.enable_widget(self.prevButton, hasPrev)
            self.enable_widget(self.nextButton, hasNext)
            self.enable_widget(self.firstButton, hasPrev or self.diffVersion is not None)
            self.enable_widget(self.latestButton, hasNext or self.diffVersion is not None)
        else:
            self.disable_widget(self.prevButton)
            self.disable_widget(self.nextButton)
            self.disable_widget(self.firstButton)
            self.disable_widget(self.latestButton)

    def update_version_label(self):
        if self.person is not None:
            self.versionLabel['text'] = "Version "+self.person.format_version(self.person.version)
            if self.diffVersion is not None:
                self.versionLabel['style'] = 'Delta.TLabel'
                if self.diffVersion < self.person.version:
                    self.fromLeftLabel['text'] = self.person.format_version(self.diffVersion)+" --> "
                    self.fromRightLabel['text'] = ""
                else:
                    self.fromLeftLabel['text'] = ""
                    self.fromRightLabel['text'] = " <-- "+self.person.format_version(self.diffVersion)
            else:
                if self.person.has_version('next'):
                    self.versionLabel['style'] = 'Delta.TLabel'
                else:
                    self.versionLabel['style'] = 'TLabel'
                self.fromLeftLabel['text'] = ""
                self.fromRightLabel['text'] = ""
        else:
            self.versionLabel['text'] = "---"
            self.versionLabel['style'] = 'TLabel'
            self.fromLeftLabel['text'] = ""
            self.fromRightLabel['text'] = ""

    def update_relat_buttons(self):
        self.disable_widget(self.addRelatButton, self.readOnly)

    def update_all(self):
        self.readOnly = self.is_read_only()
        self.update_widgets()
        self.update_addr_tabs()
        self.update_top()
        self.update_error_msgs()
        self.update_save_buttons()
        self.update_nav_buttons()
        self.update_version_label()
        self.update_relat_buttons()

    def confirm_save_with_errors(self):
        if self.person is not None and self.person.is_any_error():
            if not self.person.is_ok_to_save():
                messagebox.showwarning(message=
"""There are still some errors you must correct before saving this version.""")
                return False
            elif self.person.loadErrorMsg:
                return messagebox.askokcancel(message=
"""This version was not loaded successfully.

But if you've reentered all the data you want and it looks right, you can go ahead and save it.

Click "OK" to continue saving.
Click "Cancel" to go back without saving.""")
            else:
                return messagebox.askyesno(message=
"""There are still some errors.  Are you sure you want to continue?

Click "Yes" to save anyway, with the errors.
Click "No" to go back without saving.  You can correct the errors and try again.""")
        else:
            return True

    def confirm_unsaved_changes(self, what="do this"):
        if self.person is not None and self.person.is_any_changed():
            answer = messagebox.askyesno(message=
"""You haven't saved your changes to this version.

You'll lose those changes if you {0}.
Are you sure you want to continue?

Click "Yes" to discard your changes and continue.
Click "No" to go back to where you were without losing anything.""".format(what))
            if answer:
                self.do_discard()
            return answer
        else:
            return True

    def is_read_only(self):
        if self.person is None:
            return True
        elif self.quantumMode:
            return False
        else:
            nextVersion = self.person.get_version('next')
            if nextVersion is None:
                return False
            else:
                return self.person.is_same_minor_series(self.person.version, nextVersion)

for flavor in Person.addrFlavors:
    PersonDetail.labelText.update(Person.make_flavored(flavor, PersonDetail.addrLabelText))
    PersonDetail.mappers.update(Person.make_flavored(flavor, PersonDetail.addrMappers))
