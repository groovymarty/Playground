# tkit.widgetgarden

from tkinter import *
from tkinter import ttk
from tkit.layouthelper import LayoutHelper
from tkit.widgethelper import WidgetHelper
from tkit.datechooser import DateChooser

class WidgetGarden(LayoutHelper, WidgetHelper):
    labelText = {}
    mappers = {}

    def __init__(self):
        LayoutHelper.__init__(self)
        self.vars = {}
        self.labels = {}
        self.entries = {}
        self.comboboxes = {}
        self.checkbuttons = {}
        self.dates = {}
        self.tkNameToKey = {}
        self.widgets = {}
        self.widgetToKey = {}

    def make_var(self, key, varClass):
        newVar = varClass()
        self.vars[key] = newVar
        self.tkNameToKey[newVar._name] = key
        return newVar

    def make_label(self, key, **kwargs):
        newLabel = ttk.Label(self.curParent, text=self.labelText[key], **kwargs)
        self.labels[key] = newLabel
        self.grid_widget(newLabel)
        self.next_col()
        return newLabel

    def make_entry(self, key, **kwargs):
        self.make_label(key)
        var = self.make_var(key, StringVar)
        var.trace('w', self.on_trace_write)
        widget = ttk.Entry(self.curParent, textvariable=var, **kwargs)
        self.entries[key] = widget
        self.widgets[key] = widget
        self.widgetToKey[widget] = key
        if 'width' in kwargs:
            self.grid_widget(widget)
        else:
            self.grid_widget(widget, sticky=(N,W,E))
        self.bind_entry_big_change(widget, self.on_big_change)
        self.next_col()
        return widget

    def make_combobox(self, key, values, **kwargs):
        self.make_label(key)
        var = self.make_var(key, StringVar)
        var.trace('w', self.on_trace_write)
        widget = ttk.Combobox(self.curParent, textvariable=var, values=values, **kwargs)
        self.comboboxes[key] = widget
        self.widgets[key] = widget
        self.widgetToKey[widget] = key
        if 'width' in kwargs:
            self.grid_widget(widget)
        else:
            self.grid_widget(widget, sticky=(N,W,E))
        self.bind_combobox_big_change(widget, self.on_big_change)
        self.next_col()
        return widget

    def make_checkbutton(self, key, **kwargs):
        var = self.make_var(key, BooleanVar)
        var.trace('w', self.on_trace_write)
        widget = ttk.Checkbutton(self.curParent, text=self.labelText[key], variable=var, **kwargs)
        self.checkbuttons[key] = widget
        self.widgets[key] = widget
        self.widgetToKey[widget] = widget
        self.grid_widget(widget)
        self.next_col()
        return widget

    def make_date(self, key):
        self.make_label(key)
        var = self.make_var(key, StringVar)
        var.trace('w', self.on_trace_write)
        def my_update_error(e, key=key):
            self.update_error(key, e)
        widget = DateChooser(self.curParent, textvariable=var, updateerror=my_update_error)
        self.dates[key] = widget
        self.widgets[key] = widget
        self.widgetToKey[widget] = key
        self.grid_widget(widget)
        self.next_col()
        return widget

    def set_widget_style(self, key, modifier=""):
        if key in self.labels:
            self.labels[key]['style'] = self.join_style(modifier, 'TLabel')
        elif key in self.checkbuttons:
            self.checkbuttons[key]['style'] = self.join_style(modifier, 'TCheckbutton')

    def set_widget_enable(self, key, enable=True):
        if key in self.widgets:
            self.enable_widget(self.widgets[key], enable, recursive=True)

    def set_widget_disable(self, key, disable=True):
        if key in self.widgets:
            self.disable_widget(self.widgets[key], disable, recursive=True)

    def read_var(self, key):
        var = self.vars[key]
        if key in self.mappers:
            return self.mappers[key].map_in(var.get())
        else:
            return var.get()

    def write_var(self, key, value):
        var = self.vars[key]
        if key in self.mappers:
            var.set(self.mappers[key].map_out(value))
        else:
            var.set(value)

    def on_trace_write(self, tkName, tkIndx, mode):
        self.on_var_change(self.tkNameToKey[tkName])

    def on_var_change(self, key):
        pass

    def on_big_change(self, event):
        pass

    def update_error(self, key, e):
        pass
