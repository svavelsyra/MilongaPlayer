import logging
import os
import tkinter
import tkinter.ttk

from playlist import history
from playlist import pattern
from playlist import patternbrowser

class PatternPlayList(tkinter.ttk.Frame):
    """
    Pattern playlist.
    """
    def __init__(self, master, player_instance, startup_info, cashe, *args, **kwargs):
        self.log = logging.getLogger('MilongaPlayer.PlayList.PatternPlayList')
        self.log.info('Initialization of PlayList')
        super().__init__(master, *args, **kwargs)

        buttons = tkinter.ttk.Frame(self)
        buttons.pack(fill=tkinter.X, side='top')
        pb = tkinter.ttk.Button(
            buttons, text='Pattern browser', command=self.edit_patterns)
        pb.pack(side='left')
        uf = tkinter.ttk.Button(
            buttons, text='Update files', command=self.update_files)
        uf.pack(side='left')
        
        self.view = tkinter.ttk.Treeview(self, show='tree')
        self.view.bind('<Double-1>', self.on_dclick)
        self.view.pack(side='left', expand=1, fill=tkinter.BOTH)
        scrollbar = tkinter.ttk.Scrollbar(
            self, orient='vertical', command=self.view.yview)
        scrollbar.pack(side='left', fill=tkinter.Y)
        self.view.configure(yscrollcommand=scrollbar.set)
        self.history = history.History(self)
        self.history.pack(side='left', fill=tkinter.Y)
        self.on_startup(startup_info)
        self.current_track = None
        self.player = player_instance
        self.cashe = cashe
        self.log.info('PlayList initialization Done')

    def on_startup(self, startup_info):
        """Run once on startup to set playlist and state."""
        if not startup_info:
            startup_info = {'name': 'Playlist',
                            'playlist': [],
                            'pattern': None}
        for key in ('name', 'playlist', 'pattern'):
            try:
                self.log.info(f'Loading: {key=}: {startup_info[key]}')
                setattr(self, key, startup_info[key])
            except KeyError as err:
                self.log.error(f'Error loading: KeyError: {err}')
                setattr(self, key, None)
        self.create_playlist_view()

    def on_close(self):
        """Save state and playlist."""
        dict_to_save = {}
        if self.current_track:
            self.playlist[0].insert_file(self.current_track)
        for key in ('name', 'playlist', 'pattern'):
            dict_to_save[key] = getattr(self, key)
        dict_to_save['type'] = 'Pattern'
        return dict_to_save
            
    def move_to_last(self):
        """
        Moves playlist entry to last in the list.
        """
        p = self.playlist.pop(0)
        self.log.info(f'Move to last: {p}')
        p.select_files()
        self.playlist.append(p)
        iid = self.view.get_children()[0]
        children = self.view.get_children(iid)
        self.log.debug(f'Removing children {children}')
        self.view.delete(*children)
        self.view.move(iid, '', 'end')
        self.add_tracks(iid, p)

    def move_to_item(self, iid):
        """
        Moves the playlist ahead untill iid is found.
        Works on toplevel iid:s only.
        """
        for c_iid  in self.view.get_children():
            if not iid == c_iid:
                self.log.info(f'Moving {c_iid}')
                self.move_to_last()
                continue
            break
        
    def remove_first_child(self, iid):
        """
        Removes first child from list.
        """
        self.log.info(f'Removing first child from: {iid}')
        self.view.delete(self.view.get_children(iid)[0])
        
    def add_tracks(self, iid, p):
        """
        Add tracks to playlist.
        """
        self.log.info(f'Adding tracks to tree item {iid}')
        for path in p.playlist:
            track = os.path.basename(path)
            self.log.debug(f'Adding track: {track} to {iid}')
            self.view.insert(iid, 'end', text=track, values=(path,))

    def get_track(self, index=0):
        """
        If called with index==0 or no index then return current track if its set,
        otherwise set next track as current and return that.
        Otherwise step next track to current track and countdown index with one.
        """
        def pl_info(pl):
            name = pl.name
            playlist = [os.path.splitext(os.path.basename(filename))[0] for
                        filename in pl.playlist]
            playlist = '\n\t'.join(playlist)
            return f'{name}\n\t{playlist}'

        if not self.history.current.get():
            self.history.add(self.playlist[0])
            self.history.add(self.playlist[1])
        
        self.log.info(f'Get track with index: {index}')
        if index == 0:
            track = self.current_track or self.playlist[0].next()
            self.current_track = track
            self.log.info(f'Found track {track}')
            return track
        elif index < 0:
            # Previous not implemented
            pass
        else:
            if not self.playlist[0]:
                self.move_to_last()
                self.current_track = self.playlist[0].next()
                self.history.add(self.playlist[1])
            else:
                self.current_track = self.playlist[0].next()
                parent_iid = self.view.get_children()[0]
                self.remove_first_child(parent_iid)
            return self.get_track(index - 1)
        
    def create_playlist_view(self):
        """
        Creates a playlist view.
        """
        for p in self.playlist:
            self.log.debug(f'Adding {p.name} to playlist')
            iid = self.view.insert('', 'end', text=p.name)
            self.log.debug(f'{iid} added to playlist')
            self.add_tracks(iid, p)

    def edit_patterns(self):
        """Edit pattern."""
        pattern =  patternbrowser.PatternBrowser(
            self, 'Pattern Browser', self.pattern).result
        if pattern:
            self.pattern = pattern
            self.log.debug(f'Pattern: {pattern}')
            self.load_pattern()

    def load_pattern(self):
        """Load a pattern from file."""
        for child in self.view.get_children():
            self.view.delete(child)
        self.playlist = []
        for key in self.pattern['pattern_order']:
            name = self.pattern[key]['name']
            paths = self.pattern[key]['paths']
            number = self.pattern[key]['number']
            self.log.debug(f'{name=}, {paths=}, {number=}')
            p = pattern.Pattern(name, paths, number, cashe=self.cashe)
            self.playlist.append(p)
        self.create_playlist_view()

    def update_files(self):
        """
        Update files in patterns, clear cashe.
        """
        for pattern in self.playlist:
            for path in pattern['paths']:
                self.cashe.pop(path, None)
        self.load_pattern()

    def on_dclick(self, event):
        """
        On double click play the clicked song.
        """
        def update_history():
            self.history.add(self.history.current.get())
            self.history.add(self.playlist[0])
            self.history.add(self.playlist[1])
            
        iid = self.view.identify('item', event.x, event.y)
        values = self.view.item(iid, 'values')
        # User has clicked track item
        if values:
            self.log.info(f'Double click on track {iid}')
            parent_iid = self.view.parent(iid) 
            self.move_to_item(parent_iid)
            while True:
                prev = self.view.prev(iid)
                if not prev:
                    break
                self.view.delete(prev)
                self.playlist[0].playlist.pop(0)
        # User has clicked a pattern item
        else:
            self.log.info(f'Double click on pattern {iid}')
            self.move_to_item(iid)

        update_history()
        self.current_track = self.playlist[0].playlist.pop(0)
        self.player.set_playlist(self)
        self.player.play(self.current_track)



