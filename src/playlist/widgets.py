import tkinter
import tkinter.ttk

class ScrollableFrame(tkinter.ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        canvas = tkinter.Canvas(self)
        scrollbar = tkinter.ttk.Scrollbar(
            self, orient="vertical", command=canvas.yview)
        self.interior = tkinter.ttk.Frame(canvas)

        self.interior.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.interior, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

class Dialog(tkinter.Toplevel):
    def __init__(self, parent, title=None, initial_data=None):
        super().__init__(parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent

        self.result = None

        body = tkinter.ttk.Frame(self)
        self.initial_focus = self.body(body, initial_data)
        body.pack(padx=5, pady=5, fill=tkinter.BOTH)

        self.buttonbox()

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.initial_focus.focus_set()

        self.wait_window(self)

    def body(self, master, initial_data=None):
        pass

    def buttonbox(self):
        box = tkinter.ttk.Frame(self)

        w = tkinter.ttk.Button(
            box, text="OK", width=10, command=self.ok, default=tkinter.ACTIVE)
        w.pack(side='left', padx=5, pady=5)
        w = tkinter.ttk.Button(
            box, text="Cancel", width=10, command=self.cancel)
        w.pack(side='left', padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def ok(self, event=None):

        if not self.validate():
            self.initial_focus.focus_set()
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()

        self.cancel()

    def cancel(self, event=None):
        self.parent.focus_set()
        self.destroy()

    def validate(self):
        return 1

    def apply(self):
        pass
