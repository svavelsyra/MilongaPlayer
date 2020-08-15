import tkinter
import tkinter.ttk

class StatusWindow():
    def __init__(self, master, player_instance):
        self.player_instance = player_instance
        self.top = tkinter.Toplevel(master)
        self.current_track = tkinter.StringVar()
        tkinter.ttk.Label(self.top, textvariable=self.current_track).pack()
        self.worker()

    def worker(self):
        current_track = self.player_instance.current_track or ''
        self.current_track.set(current_track)
        self.top.after(500, self.worker)
