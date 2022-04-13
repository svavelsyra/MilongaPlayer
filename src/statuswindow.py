import os
import tkinter
import tkinter.font
import tkinter.ttk

class StatusWindow():
    def __init__(self, master, player_instance):
        self.player_instance = player_instance
        self.top = tkinter.Toplevel(master)
        self.top.bind('<Configure>', self.resize)

        # Container
        f = tkinter.Frame(self.top, width=400, height=200)

        # Label
        self.current_track = tkinter.StringVar()
        self.label_font = tkinter.font.Font(
            self.top, family='Arial', size=10, weight='bold')
        self.label = tkinter.ttk.Label(
            f, textvariable=self.current_track, font=self.label_font)
        self.label.pack(fill=tkinter.BOTH, expand=1)
        f.pack(fill=tkinter.BOTH, expand=1)

        self.worker()

    def worker(self):
        current_track = self.player_instance.current_track or ''
        current_track = os.path.splitext(os.path.basename(current_track))[0]
        self.current_track.set(current_track)
        self.top.after(500, self.worker)

    def resize(self, *args, **kwargs):
        current = self.current_track.get()
        if not current:
            return
        height = self.label.winfo_height()
        width = self.label.winfo_width()
        self.label_font['size'] = 4
        font = self.label_font
        while (current and
               font.measure(current) < width and
               font.metrics('linespace') < height):
            self.label_font['size'] += 1
        self.label_font['size'] -= 1
