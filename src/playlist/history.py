import logging
import tkinter
import tkinter.ttk

class History(tkinter.ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        self.master = master
        super().__init__(master, *args, **kwargs)

        self.previous = tkinter.StringVar()
        self.previous.set('')
        self.current = tkinter.StringVar()
        self.current.set('')
        self.next = tkinter.StringVar()
        self.next.set('')

        for key in ('previous', 'current', 'next'):
            f = tkinter.Frame(self, width=200, height=200)
            f.pack_propagate(0)
            f.pack(side='top', expand=1, fill=tkinter.Y)
            tkinter.ttk.Label(f, text=key.capitalize()).pack(side='top', fill=tkinter.X)
            tkinter.ttk.Label(f, textvariable=getattr(self, key)).pack(side='top', fill=tkinter.X)

    def add(self, entry):
        self.previous.set(self.current.get())
        self.current.set(self.next.get())
        self.next.set(entry)
