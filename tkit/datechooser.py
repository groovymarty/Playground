# tkit.datechooser

from tkinter import *
from tkinter import ttk
from basic_data import date
from basic_services import log_debug
from tkit.widgethelper import WidgetHelper

class DateChooser(ttk.Frame, WidgetHelper):
    def __init__(self, parent, textvariable=None, updateerror=None):
        ttk.Frame.__init__(self, parent)
        self.dateVar = textvariable
        self.updateError = updateerror
        self.monthVar = StringVar()
        self.monthVar.trace('w', self.on_part_write)
        self.monthCbx = ttk.Combobox(self, textvariable=self.monthVar, values=date.monthNames+["Unknown"], width=10)
        self.monthCbx.grid(column=0, row=0, sticky=(N,W))
        self.bind_combobox_big_change(self.monthCbx, self.on_big_change)
        self.dayVar = StringVar()
        self.dayVar.trace('w', self.on_part_write)
        self.dayCbx = ttk.Combobox(self, textvariable=self.dayVar, values=list(range(1,32)), width=3)
        self.dayCbx.grid(column=1, row=0, sticky=(N,W))
        self.bind_combobox_big_change(self.dayCbx, self.on_big_change)
        self.yearVar = StringVar()
        self.yearVar.trace('w', self.on_part_write)
        self.yearCbx = ttk.Combobox(self, textvariable=self.yearVar, values=list(range(1900,2050)), width=5)
        self.yearCbx.grid(column=2, row=0, sticky=(N,W))
        self.bind_combobox_big_change(self.yearCbx, self.on_big_change)
        self.ignoreWrite = False
        if self.dateVar is not None:
            self.dateVar.trace('w', self.on_date_write)
            self.load_date(self.dateVar.get())

    def on_date_write(self, tkName, tkIndx, mode):
        if not self.ignoreWrite:
            self.load_date(self.dateVar.get())

    def load_date(self, value):
        dc = date.DateChecker()
        try:
            dc.check_date(value)
            err = None
        except ValueError as e:
            err = e
        if self.updateError is not None:
            self.updateError(err)
        self.load_vars_from_checker(dc)

    def load_vars_from_checker(self, dc):
        self.ignoreWrite = True
        if dc.unknown:
            self.monthVar.set("Unknown")
            self.dayVar.set("")
            self.yearVar.set("")
        else:
            if dc.imonth is not None:
                self.monthVar.set(date.monthNames[dc.imonth-1])
                self.dayCbx['values'] = list(range(1, date.days_in_month(dc.imonth, dc.iyear)+1))
            else:
                self.monthVar.set(dc.month)
                self.dayCbx['values'] = list(range(1, 32))
            if dc.iday is not None:
                self.dayVar.set(str(dc.iday))
            else:
                self.dayVar.set(dc.day)
            if dc.iyear is not None:
                self.yearVar.set(str(dc.iyear))
            else:
                self.yearVar.set(dc.year)
        self.ignoreWrite = False

    def on_part_write(self, tkName, tkIndx, mode):
        if not self.ignoreWrite and self.dateVar is not None:
            self.ignoreWrite = True
            self.dateVar.set(self.join_parts())
            self.ignoreWrite = False

    def join_parts(self):
        return "-".join(var.get() for var in (self.yearVar, self.monthVar, self.dayVar))

    def on_big_change(self, event):
        dc = date.DateChecker()
        try:
            dc.check_date(self.join_parts(), fixDay=True, tolerateIncomplete=False)
            err = None
        except ValueError as e:
            err = e
        if self.updateError is not None:
            self.updateError(err)
        if self.dateVar is not None:
            self.ignoreWrite = True
            self.dateVar.set(dc.format(asEntered=err is not None))
            self.ignoreWrite = False
        self.load_vars_from_checker(dc)
