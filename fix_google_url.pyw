# fix_google_url

import os, re
from tkinter import *
from tkinter import ttk

root = Tk()
root.title("Fix Google URL")
lab = ttk.Label(root, text="Fix Google URL in clipboard")
lab.pack(side=TOP, expand=True, ipady=10)

clip_in_lab = ttk.Label(root, text="clip_in", background="white")
clip_in_lab.pack(side=TOP, expand=True, ipady=10)

clip_out_lab = ttk.Label(root, text="clip_out")
clip_out_lab.pack(side=TOP, expand=True, ipady=10)

# Google Drive Example:
# https://drive.google.com/file/d/1Lv04ZdJAosgHeIScGB3iltgw8Kl_ny5L/view?usp=drive_link

# Change to:
# https://drive.google.com/uc?export=view&id=1Lv04ZdJAosgHeIScGB3iltgw8Kl_ny5L

# Google Photos Shared Album Example:
# https://photos.google.com/u/1/share/AF1QipO15a-JTXURdX2RmbWfz5JhOkMwcgrVB0d_pONYyDPKxZXwZbNYg_lMTzmDpafa1w/photo/AF1QipND79vwqKWgh7BrdW2HU2JLgbZLjkr9UTFD15nw?key=elFDckZLZkpFQU45NTlRWm5YMERSQ3E3blAtZHdB

# Change to:
# https://photos.google.com/share/AF1QipO15a-JTXURdX2RmbWfz5JhOkMwcgrVB0d_pONYyDPKxZXwZbNYg_lMTzmDpafa1w/photo/AF1QipND79vwqKWgh7BrdW2HU2JLgbZLjkr9UTFD15nw?key=elFDckZLZkpFQU45NTlRWm5YMERSQ3E3blAtZHdB

# KS iTunes Example:
# "D:\Users\msaus\Music\iTunes\iTunes Media\Music\The Kent Singers\Handel_ Messiah (Kent Singers 2022)\1-01 Mendelssohn_ He Watching Over I.m4a"

# Change to:
# "https://kentsingers.com/audio/Handel_ Messiah (Kent Singers 2022)/1-01 Mendelssohn_ He Watching Over I.m4a"

# KS Pictures Example:
# "D:\Users\msaus\Pictures\KS Kent Singers\KS+01 Artwork & Graphics\KS+01-0130-rose-in-winter-AQ-original.jpg"

# Change to:
# "https://kentsingers.com/pictures/KS+01-0130-rose-in-winter-AQ-original.jpg"

def do_fix(export_arg):
    try:
        clip_in = root.clipboard_get()
    except TclError:
        clip_in = ""

    clip_in_lab.config(text=clip_in)
    clip_out = None
    message = "Clipboard does not match URL pattern"

    if clip_in == "":
        message = "Clipboard empty"
    else:
        if export_arg != "":
            if clip_in.startswith("https://drive.google.com/uc?export=" + export_arg):
                message = "Clipboard URL already fixed"
            else:
                mr = re.match(r'https://drive\.google\.com/file/d/([A-Za-z0-9_-]+)/view.*', clip_in)
                if mr:
                    clip_out = "https://drive.google.com/uc?export=" + export_arg + "&id=" + mr.group(1)
        else:
            if clip_in.startswith("https://photos.google.com/share/"):
                message = "Clipboard URL already fixed"
            else:
                mr = re.match(r'https://photos.google.com/u/\d+/share/([A-Za-z0-9_-]+/photo/[A-Za-z0-9_-]+\?key=[A-Za-z0-9_-]+)', clip_in)
                if mr and export_arg == "":
                    clip_out = "https://photos.google.com/share/" + mr.group(1)
                else:
                    mr = re.match(r'.*\\Music\\iTunes\\iTunes Media\\Music\\The Kent Singers\\(.*)?"', clip_in)
                    if mr and export_arg == "":
                        clip_out = "https://kentsingers.com/audio/" + mr.group(1).replace('\\', '/').replace('#', '')
                    else:
                        mr = re.match(r'.*\\Pictures\\.*\\([ A-Za-z0-9_,.+-]+)?"', clip_in)
                        if mr and export_arg == "":
                            clip_out = "https://kentsingers.com/pictures/" + mr.group(1).replace('+', '%2b')
    if clip_out:
        clip_out_lab.config(text=clip_out, background="lime")
        root.clipboard_clear()
        root.clipboard_append(clip_out)
        root.update()
    else:
        clip_out_lab.config(text=message, background="yellow")

def fix_view():
    do_fix("view")
pxButton = ttk.Button(root, text="Pics, Docs: export=view", command=fix_view)
pxButton.pack(side=LEFT, fill=X, expand=True, ipady=10)

def fix_open():
    do_fix("open")
cxButton = ttk.Button(root, text="Audio: export=open", command=fix_open)
cxButton.pack(side=LEFT, fill=X, expand=True, ipady=10)

def fix_photo():
    do_fix("")
cxButton = ttk.Button(root, text="Google Photo", command=fix_photo)
cxButton.pack(side=LEFT, fill=X, expand=True, ipady=10)

def fix_KS_iTunes():
    do_fix("")
cxButton = ttk.Button(root, text="KS iTunes", command=fix_KS_iTunes)
cxButton.pack(side=LEFT, fill=X, expand=True, ipady=10)

def fix_KS_picture():
    do_fix("")
cxButton = ttk.Button(root, text="KS Picture", command=fix_KS_picture)
cxButton.pack(side=LEFT, fill=X, expand=True, ipady=10)

def on_exit():
    root.destroy()
root.protocol("WM_DELETE_WINDOW", on_exit)

root.mainloop()
