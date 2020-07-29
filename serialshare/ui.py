"""
gui elements
"""

import tkinter
import tkinter.messagebox
import sys


INITIAL_DEVICE = "Select a serial device..."


def setout(window, out, options):
    """
    closes window, sets out["device"] to dev and out["hostname"] to host
    """

    if options["device"] == INITIAL_DEVICE:
        tkinter.messagebox.showinfo("Invalid input", "Select a device")
        return

    for key in options.keys():
        # check for blank options before returning
        if options[key] == "":
            tkinter.messagebox.showinfo(
                "Invalid input",
                "Field '{}' cannot be blank" % key
            )
            return

        out[key] = options[key]

    window.destroy()


def inputwindow(out, devices):
    """
    takes a dict, `out`; and a list, `devices`
    asks for hostname (text input), serial device (dropdown)
    stores answers in `out["hostname"]` and `out["device"]`
    """

    # main window #
    # create a window
    root = tkinter.Tk()
    root.title("serialshare")
    root.geometry("320x120")
    root.eval(
        "tk::PlaceWindow %s center" % root.winfo_pathname(root.winfo_id())
    )

    # a frame for padding
    container = tkinter.Frame(root)
    container.place(relx=0.05, rely=0.05, relwidth=0.90, relheight=0.90)

    # inputs #
    # a frame to hold our input controls
    inputframe = tkinter.Frame(container)
    # organized into two columns
    inputframe.grid_columnconfigure((0, 1), weight=1)
    inputframe.pack(side=tkinter.TOP)

    # a label for the hostname input
    hostnamelabel = tkinter.Label(inputframe, text="Hostname:")
    hostnamelabel.grid(row=1, column=0)
    # a one-line textbox for the hostname input
    hostnamebox = tkinter.Entry(inputframe)
    hostnamebox.grid(row=1, column=1, sticky="ew")

    # a label for the device dropdown
    devicelabel = tkinter.Label(inputframe, text="Serial device:")
    devicelabel.grid(row=2, column=0)
    # a dropdown for the device selection, populated by devices
    deviceboxstring = tkinter.StringVar()
    deviceboxstring.set(INITIAL_DEVICE)
    devicebox = tkinter.OptionMenu(inputframe, deviceboxstring, *devices)
    devicebox.grid(row=2, column=1, sticky="ew")

    # a label for the baudrate input
    baudratelabel = tkinter.Label(inputframe, text="Baudrate:")
    baudratelabel.grid(row=3, column=0)
    # a one-line textbox for the hostname input
    baudratebox = tkinter.Entry(inputframe)
    baudratebox.grid(row=3, column=1, sticky="ew")

    # buttons #
    # a frame for out start/cancel buttons
    buttonframe = tkinter.Frame(container)
    buttonframe.pack(side=tkinter.BOTTOM)

    def input_values():
        """ returns a dict from which to fill the supplied `out` arg """
        return {
            "hostname": hostnamebox.get(),
            "device": deviceboxstring.get(),
            "baudrate": baudratebox.get(),
        }

    # start button. when pressed, set values from controls
    startbutton = tkinter.Button(
        buttonframe,
        text="Start",
        command=lambda: setout(
            # the window to close:
            root,
            # the dict reference:
            out,
            # the dict to fill the ref from:
            input_values()
        )
    )
    startbutton.pack(side="left")

    # exit button. closes the application without cleanup
    exitbutton = tkinter.Button(
        buttonframe,
        text="Cancel",
        command=sys.exit
    )
    exitbutton.pack(side="left")

    # execution #
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\ncaught ctrl-c while awaiting gui input")
        sys.exit()
