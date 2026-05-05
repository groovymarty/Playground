# trim_image_to_size.pyw

import sys, os, shutil, tkinter
from tkinter import filedialog, messagebox
from trim_to_size import trim_transparent_to_size

docs_dir ="C:\\Users\\Msaus\\Documents"

image_file  = filedialog.askopenfilename(title='Select image file', defaultextension='png', initialdir=docs_dir)
if not image_file:
    sys.exit(0)

trim_transparent_to_size(image_file, image_file, 1125, 1000)

messagebox.showinfo("Done", "Trim complete")
