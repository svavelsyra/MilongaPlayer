import logging
import os
import pickle
import tkinter
import tkinter.ttk

from playlist import pattern
from playlist.fileplaylist import FilePlayList
from playlist.patternplaylist import PatternPlayList

class PlayList(tkinter.ttk.Frame):
    """Root playlist frame."""
    def __init__(self, master, player_instance, startup_info, *args, **kwargs):
        self.log = logging.getLogger('MilongaPlayer.PlayList')
        super().__init__(master, *args, **kwargs)
        self.player_instance = player_instance
        self.player_instance.get_track = self.get_track
        self.player_instance.set_playlist = self.set_playlist

        # Buttons
        buttonbar = tkinter.ttk.Frame(master)
        tkinter.ttk.Button(buttonbar,
                           command=lambda: self.add_playlist('pattern'),
                           text='Add pattern playlist').pack(side='left')
        tkinter.ttk.Button(buttonbar,
                           command=lambda: self.add_playlist('file'),
                           text='Add file playlist').pack(side='left')

        # Tabs
        # Initialize to 1x1 So that bottom bar is visible on verry
        # small screans. expands to take availbe space during packing.
        self.tabs = tkinter.ttk.Notebook(self, width=1, height=1)
        self.tabs.bind('<Button-3>', self.popup)

        # Packing
        buttonbar.pack(fill=tkinter.X)
        self.tabs.pack(fill=tkinter.BOTH, expand=1)
        
        self.cashe = {}
        self.on_startup(startup_info)

    def popup(self, event):
        """Popup menu on right click on tab."""
        self.log.debug(f'Popup event: {event}')
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
        """Rename tab."""
        clicked_tab = self.tabs.tk.call(
            self.tabs._w, "identify", "tab", x, y)
        name = tkinter.simpledialog.askstring("Input", "Enter Name",
                                              parent=self)
        if name:
            self.log.info(f'Renaming tab to: {name}')
            self.tabs.tab(clicked_tab, text=name)
            self.tabs.nametowidget(self.tabs.tabs()[clicked_tab]).name = name

    def remove(self, x, y):
        """Remove tab and the accociated playlist."""
        clicked_tab = self.tabs.tk.call(
            self.tabs._w, "identify", "tab", x, y)
        widget = self.tabs.nametowidget(self.tabs.tabs()[clicked_tab])
        self.tabs.forget(clicked_tab)
        widget.destroy()
              
    def on_startup(self, startup_info):
        """Run once on startup to load playlists and set state."""
        playlists = {'Pattern': PatternPlayList,
                     'File': FilePlayList}
        self.cashe = startup_info.get('cashe', {})
        self.current_playlist = None
        for pl in startup_info.get('playlists', []):
            if not (pl and pl.get('type', '') in playlists):
                continue
            self.log.debug('Adding playlist of type: {pl[type]}')
            tab = playlists[pl['type']](self.tabs,
                                        self.player_instance,
                                        pl,
                                        self.cashe)
            tab.pack(expand=1, fill=tkinter.BOTH)
            self.tabs.add(tab, text=pl.get('name', 'playlist'))

        current_tab = startup_info.get('current_tab', None)
        if current_tab in self.tabs.tabs():
            self.tabs.select(current_tab)

    def on_close(self):
        """Run on close to save playlists and state."""
        playlists = [pl.on_close()
                     for pl in self.tabs.children.values()]
        return {'cashe': self.cashe,
                'current_tab': self.tabs.select(),
                'playlists': playlists,
                'version': 1}

    def set_playlist(self, pl):
        self.current_playlist = pl
            
    def get_track(self, index=0):
        """Get track from currently selected tab."""
        if not self.current_playlist in self.tabs.tabs():
            self.current_playlist = self.tabs.select()
        widget = self.tabs.nametowidget(self.current_playlist)
        return widget.get_track(index)

    def add_playlist(self, pl_type):
        """Add a new playlist of the selected type."""
        playlist_types = {'pattern': PatternPlayList,
                          'file': FilePlayList}
        p = playlist_types[pl_type](self.tabs,
                                    self.player_instance,
                                    None,
                                    self.cashe)
        p.pack(expand=1, fill=tkinter.BOTH)
        self.tabs.add(p, text='Playlist')
         
    def key_event(self, target, event):
        """
        Pass keyevent to currently selected tab, ignore atribute errors.
        """
        self.log.info(f'Key event: {target}({event})')
        tab_name = self.tabs.select()
        widget = self.tabs.nametowidget(tab_name)
        try:
            getattr(widget, target)(event)
        except AttributeError:
            pass
