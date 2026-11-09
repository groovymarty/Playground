# trim_image_to_size.pyw

import sys
import tkinter
from tkinter import filedialog, messagebox
from trim_to_size import trim_transparent_to_size

docs_dir ="C:\\Users\\Msaus\\Documents"

root = tkinter.Tk()
root.withdraw()

image_file  = filedialog.askopenfilename(title='Select image file', defaultextension='png', initialdir=docs_dir)
if not image_file:
    sys.exit(0)

try:
    width, height = trim_transparent_to_size(image_file, image_file)
except Exception as exc:
    messagebox.showerror("Trim failed", str(exc))
    sys.exit(1)

messagebox.showinfo("Done", f"Trim complete: {width} x {height} pixels")
