# everybody.main

import os
from tkinter import *
from tkinter import ttk
import basic_services
from basic_logger import BasicLogger
from file_city import FileCity
from everybody import services
from everybody.person import Person
from everybody.personlist_and_detail import PersonListAndDetail

debugMode = False

baseDir = os.path.join(os.path.expanduser("~"), "Documents", "Everybody")

with BasicLogger(baseDir, "Everybody.log", echoStdout=debugMode) as logger:
    logger.log_info("Everybody: starting")
    if debugMode:
        logger.enable_debug("PersonList", "PersonDetail", "FileCity", "Events")
        logger.enable_debug("DateChooser", "Body")
    basic_services.set_logger(logger)

    db = FileCity()
    db.add_type("Per", Person)
    db.open(baseDir)
    services.set_database(db)

    root = Tk()
    root.title("Everybody")
    #root.geometry("750x650")
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)
    services.set_tkRoot(root)

    people = db.generate_all('Per')
    personListAndDetail = PersonListAndDetail(root, people)
    personListAndDetail.grid(column=0, row=0, sticky=(N,W,E,S))

    def on_exit():
        if personListAndDetail.check_unsaved_changes():
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_exit)
    root.mainloop()
    logger.log_info("Everybody: exiting")
