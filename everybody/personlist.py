# everybody.personlist

from tkinter import *
from tkinter import ttk
from basic_services import log_error, log_debug

class PersonList(ttk.Frame):
    # True means label tracks as you edit person and move among versions
    # False means label changes only when you save latest version
    changeyLabel = False

    # True means label always jumps to new position whenever it changes
    # False means label jumps only when you save latest version
    jumpyLabel = False

    def __init__(self, parent, peopleIter):
        super().__init__(parent)
        self.peopleSorted = list(peopleIter)
        self.peopleSorted.sort(key=lambda person: person.label)
        self.people = {person.instId: person for person in self.peopleSorted}
        self.make_widgets()
        self.populate_tree()

    def make_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1, minsize=500)

        self.tree = ttk.Treeview(self, height=5, show='tree')
        self.tree.grid(column=0, row=0, sticky=(N,W,E,S))
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.tag_configure('changed', background='yellow')
        self.tree.tag_configure('error', background='orange')
        self.tree.tag_configure('past', background='lightblue')

        sb = ttk.Scrollbar(self, orient=VERTICAL, command=self.tree.yview)
        sb.grid(column=1, row=0, sticky=(N,S))
        self.tree['yscrollcommand'] = sb.set

    def populate_tree(self):
        for person in self.peopleSorted:
            self.tree.insert("", END, iid=person.instId, text=person.label)

    def add_person(self, person):
        i = self.find_insertion_point(person.label)
        self.peopleSorted.insert(i, person)
        self.people[person.instId] = person
        self.tree.insert("", i, iid=person.instId, text=person.label)
        self.update_tags(person)

    def on_tree_select(self, event):
        self.event_generate("<<PersonSelect>>")

    def select(self, person):
        iid = person.instId
        self.tree.selection_set(iid)
        self.tree.focus(iid)
        self.tree.see(iid)
        self.event_generate("<<PersonSelect>>")

    def get_selected(self):
        sel = self.tree.selection()
        if sel:
            iid = sel[0]
            if iid in self.people:
                return self.people[iid]
            else:
                log_debug("PersonList.get_selected", "No such iid:", iid)
                return None
        else:
            return None

    def on_person_change(self, person):
        self.update_tags(person)
        if self.changeyLabel:
            self.update_label(person)
            if self.jumpyLabel:
                self.update_position(person)

    def on_person_save(self, person):
        self.on_person_change(person)
        if not person.has_version('next'):
            self.update_label(person)
            self.update_position(person)

    def update_tags(self, person):
        iid = person.instId
        if person.is_any_error():
            self.tree.item(iid, tags='error')
        elif person.is_any_changed() or person.is_new():
            self.tree.item(iid, tags='changed')
        elif not person.is_latest():
            self.tree.item(iid, tags='past')
        else:
            self.tree.item(iid, tags="")

    def update_label(self, person):
        iid = person.instId
        if self.tree.item(iid, 'text') != person.label:
            self.tree.item(iid, text=person.label)

    def update_position(self, person):
        if not self.is_correct_position(person):
            self.tree.detach(person.instId)
            self.peopleSorted.remove(person)
            i = self.find_insertion_point(person.label)
            self.tree.move(person.instId, "", i)
            self.peopleSorted.insert(i, person)
            log_debug("PersonList.update_position", "Moved to index {}: {}".format(i, person.label))

    def is_correct_position(self, person):
        i = self.peopleSorted.index(person)
        if i > 0 and person.label < self.peopleSorted[i-1].label:
            return False
        if i < len(self.peopleSorted)-1 and person.label > self.peopleSorted[i+1].label:
            return False
        return True

    def find_insertion_point(self, label):
        return next((i for i, person in enumerate(self.peopleSorted) if label <= person.label),
                    len(self.peopleSorted))
