# tkit.widgethelper

from tkinter import *

class WidgetHelper:
    @staticmethod
    def enable_widget(widget, enable=True, recursive=False):
        if hasattr(widget, 'state'):
            # ttk themed widget
            if enable:
                widget.state(['!disabled'])
            else:
                widget.state(['disabled'])
        else:
            widget.config(state=NORMAL if enable else DISABLED)
        if recursive:
            for child in widget.winfo_children():
                WidgetHelper.enable_widget(child, enable)

    @staticmethod
    def disable_widget(widget, disable=True, recursive=False):
        if hasattr(widget, 'state'):
            # ttk themed widget
            if disable:
                widget.state(['disabled'])
            else:
                widget.state(['!disabled'])
        else:
            widget.config(state=DISABLED if disable else NORMAL)
        if recursive:
            for child in widget.winfo_children():
                WidgetHelper.disable_widget(child, disable)

    @staticmethod
    def join_style(modifier, name):
        if modifier:
            return ".".join((modifier, name))
        else:
            return name

    @staticmethod
    def bind_entry_big_change(widget, func):
        widget.bind('<Return>', func)
        widget.bind('<FocusOut>', func)

    @staticmethod
    def bind_combobox_big_change(widget, func):
        widget.bind('<Return>', func)
        widget.bind('<FocusOut>', func)
        widget.bind('<<ComboboxSelected>>', func)

    @staticmethod
    def setup_canvas_mousewheel(canvas):
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind('<MouseWheel>', on_mousewheel)
