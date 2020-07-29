"""
gui elements
"""

import tkinter

def setout(out, dev, disp):
    out["device"] = dev
    out["display"] = disp

def inputwindow(out):
    """ asks for hostname, serial device """

    # create a window
    root = tkinter.Tk()
    root.wm_title("serialshare")

    # a textbox for the hostname
    hostnamebox = tkinter.Text(root)
    hostnamebox.place(anchor='n', relheight=0.5)

    # a button. when pressed, set values from controls
    button = tkinter.Button(
        root,
        text="Start",
        command=lambda:setout(
            # the list reference:
            out,
            # 'end - 1c' strips a trailing newline:
            hostnamebox.get("1.0", 'end - 1c'),
            # dropdown selection
            val2
        )
    )
    button.place(anchor='s', relheight=0.5)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\ncaught ctrl-c while awaiting gui input")
        exit()
