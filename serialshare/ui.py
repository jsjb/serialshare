"""
gui elements
"""

import tkinter
import tkinter.messagebox
import sys


INITIAL_DEVICE = "Select a serial device..."


def error(err):
    root = tkinter.Tk()
    root.withdraw()
    tkinter.messagebox.showinfo("Error", err)


def set_profile(window, profile, new):
    """
    sets `profile` from values in `new` and closes the window
    """

    if new["device"] == INITIAL_DEVICE:
        tkinter.messagebox.showinfo("Invalid input", "Select a device")
        return

    for key in new.keys():
        # check for blank options before returning
        if new[key] == "":
            tkinter.messagebox.showinfo(
                "Invalid input",
                "Field '{}' cannot be blank".format(key)
            )
            return

        profile[key] = new[key]

    window.destroy()


def input_window(profile, devices):
    """
    takes a dict, `profile`; and a list, `devices`
    asks for hostname (text input), serial device (dropdown)
    stores answers in `profile["hostname"]` and `profile["device"]`
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
    input_frame = tkinter.Frame(container)
    # organized into two columns
    input_frame.grid_columnconfigure((0, 1), weight=1)
    input_frame.pack(side=tkinter.TOP)

    # a dictionary of controls with labels
    grid_controls = {}

    # a one-line textbox for the hostname input
    hostname = tkinter.StringVar()
    if profile["hostname"] is not None:
        hostname.set(profile["hostname"])
    grid_controls["Hostname"] = tkinter.Entry(
        input_frame, text=hostname
    )

    # a dropdown for the serial device
    serial_device = tkinter.StringVar()
    serial_device.set(INITIAL_DEVICE)
    if profile["device"] is not None:
        serial_device.set(profile["device"])
    grid_controls["Serial device"] = tkinter.OptionMenu(
        input_frame,
        serial_device,
        *devices
    )

    # another textbox, for device speed
    baudrate = tkinter.IntVar()
    baudrate.set(profile["baudrate"])
    grid_controls["Baudrate"] = tkinter.Entry(
        input_frame, text=baudrate
    )

    # render each of our controls w their labels in a pretty grid
    for num, key in enumerate(grid_controls, start=1):
        tkinter.Label(
            input_frame, text=(key+":")
        ).grid(row=num, column=0, sticky="e")

        grid_controls[key].grid(row=num, column=1, sticky="ew")

    # buttons #
    # a frame for our start/cancel buttons
    button_frame = tkinter.Frame(container)
    button_frame.pack(side=tkinter.BOTTOM)

    def input_values():
        """ returns a dict from which to fill the supplied `profile` ref """
        return {
            "hostname": hostname.get(),
            "device": serial_device.get(),
            "baudrate": baudrate.get(),
        }

    # start button. when pressed, set values from controls
    start_button = tkinter.Button(
        button_frame,
        text="Start",
        command=lambda: set_profile(
            # the window to close:
            root,
            # the dict reference:
            profile,
            # the dict to fill the ref from:
            input_values()
        )
    )
    start_button.pack(side="left")

    # exit button. closes the application without cleanup
    exit_button = tkinter.Button(
        button_frame,
        text="Cancel",
        command=sys.exit
    )
    exit_button.pack(side="left")

    # execution #
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\ncaught ctrl-c while awaiting gui input")
        sys.exit()
