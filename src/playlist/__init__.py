import logging
import os
import pickle
import tkinter
import tkinter.ttk

from playlist import pattern
from playlist.fileplaylist import FilePlayList
from playlist.patternplaylist import PatternPlayList

class PlayList(tkinter.ttk.Frame):
    def __init__(self, master, player_instance, startup_info, *args, **kwargs):
        self.log = logging.getLogger('MilongaPlayer.PlayList')
        super().__init__(master, *args, **kwargs)
        self.player_instance = player_instance
        self.player_instance.get_track = self.get_track

        # Buttons
        buttonbar = tkinter.ttk.Frame(master)
        tkinter.ttk.Button(buttonbar,
                           command=lambda: self.add_playlist('pattern'),
                           text='Add pattern playlist').pack(side='left')
        tkinter.ttk.Button(buttonbar,
                           command=lambda: self.add_playlist('file'),
                           text='Add file playlist').pack(side='left')

        # Tabs
        self.tabs = tkinter.ttk.Notebook(self)
        self.tabs.bind('<Button-3>', self.popup)

        # Packing
        buttonbar.pack(fill=tkinter.X)
        self.tabs.pack(fill=tkinter.BOTH, expand=1)
        
        self.cashe = {}
        self.on_startup(startup_info)

    def popup(self, event):
        x = event.x
        y = event.y
        menu = tkinter.Menu(self, tearoff=0)
        menu.add_command(label='Rename',
                         command=lambda x=x, y=y : self.rename(x, y))
        menu.add_command(label='Remove',
                         command=lambda x=x, y=y : self.remove(x, y))
        try:
            menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            menu.grab_release()

    def rename(self, x, y):
        clicked_tab = self.tabs.tk.call(
            self.tabs._w, "identify", "tab", x, y)
        name = tkinter.simpledialog.askstring("Input", "Enter Name",
                                              parent=self)
        if name:
            self.tabs.tab(clicked_tab, text=name)
            self.tabs.nametowidget(self.tabs.tabs()[clicked_tab]).name = name

    def remove(self, x, y):
        clicked_tab = self.tabs.tk.call(
            self.tabs._w, "identify", "tab", x, y)
        widget = self.tabs.nametowidget(self.tabs.tabs()[clicked_tab])
        self.tabs.forget(clicked_tab)
        widget.destroy()
              
    def on_startup(self, startup_info):
        playlists = {'Pattern': PatternPlayList,
                     'File': FilePlayList}
        self.cashe = startup_info.get('cashe', {})
        for pl in startup_info.get('playlists', []):
            if not (pl and pl.get('type', '') in playlists):
                continue
            tab = playlists[pl['type']](self.tabs,
                                        self.player_instance,
                                        pl,
                                        self.cashe)
            tab.pack(expand=1, fill=tkinter.BOTH)
            self.tabs.add(tab, text=pl.get('name', 'playlist'))

    def on_close(self):
        playlists = [pl.on_close()
                     for pl in self.tabs.children.values()]
        return {'cashe': self.cashe,
                'playlists': playlists,
                'version': 1}
                
    def get_track(self, index=0):
        tab_name = self.tabs.select()
        widget = self.tabs.nametowidget(tab_name)
        return widget.get_track(index)

    def add_playlist(self, pl_type):
        playlist_types = {'pattern': PatternPlayList,
                          'file': FilePlayList}
        p = playlist_types[pl_type](self.tabs,
                                    self.player_instance,
                                    None,
                                    self.cashe)
        p.pack(expand=1, fill=tkinter.BOTH)
        self.tabs.add(p, text='Playlist')
         
    def key_event(self, target, event):
        tab_name = self.tabs.select()
        widget = self.tabs.nametowidget(tab_name)
        try:
            print(target, event)
            getattr(widget, target)(event)
        except AttributeError:
            pass
        

    def select_all(self, event):
        tab_name = self.tabs.select()
        widget = self.tabs.nametowidget(tab_name)
        try:
            widget.select_all(event)
        except AttributeError:
            pass
