# tkit.layouthelper

from tkinter import *
from tkinter import ttk

class LayoutHelper:
    def __init__(self, parent=None, numCols=1):
        self.curParent = parent
        self.numCols = numCols
        self.curRow = 0
        self.curCol = 0
        self.stack = []

    def begin_layout(self, newParent, numCols):
        self.stack.append((self.curParent, self.numCols, self.curRow, self.curCol))
        self.curParent = newParent
        self.numCols = numCols
        self.curRow = 0
        self.curCol = 0

    def grid_widget(self, widget, **kwargs):
        if 'sticky' in kwargs:
            widget.grid(row=self.curRow, column=self.curCol, **kwargs)
        else:
            widget.grid(row=self.curRow, column=self.curCol, sticky=(N,W), **kwargs)

    def end_layout(self):
        self.curParent, self.numCols, self.curRow, self.curCol = self.stack.pop()

    def next_row(self):
        self.curRow += 1
        self.curCol = 0

    def next_col(self):
        self.curCol += 1
