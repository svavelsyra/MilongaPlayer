import logging
import os
import tkinter
import tkinter.simpledialog
import tkinter.ttk

import pattern
import patternbrowser

class PlayList(tkinter.Frame):
    def __init__(self, master, player_instance, config, *args, **kwargs):
        self.log = logging.getLogger('MilongaPlayer.PlayList')
        super().__init__(master, *args, **kwargs)
        self.config = config
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
        self.on_startup()

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
              
    def on_startup(self):
        playlists = {'Pattern': PatternPlayList,
                     'File': FilePlayList}
        try:
            with open('playlists.dat', 'br') as fh:
                data = pickle.load(fh)
                self.cashe = data['cashe']
                for pl in data['playlists']:
                    if not pl:
                        continue
                    print(playlists)
                    tab = playlists[pl['type']](self.tabs,
                                                self.player_instance,
                                                pl,
                                                self.cashe)
                    tab.pack(expand=1, fill=tkinter.BOTH)
                    self.tabs.add(tab, text=pl['name'])
                
        except FileNotFoundError:
            self.log.warning('Could not find playlist data')

    def on_close(self, config):
        playlists = [pl.on_close()
                     for pl in self.tabs.children.values()]

        with open('playlists.dat', 'bw') as fh:
            pickle.dump({'cashe': self.cashe,
                         'playlists': playlists,
                         'version': 1},
                        fh)
                
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
         
    def load_playlists(self):
        playlist_types = {'pattern': PatternPlayList}
        if self.config.has_section('playlists'):
            self.log.info('Loading playlists')
            for playlist in self.config.options('playlists'):
                self.log.debug(f'Loading playlist entry: {playlist}')
                pl = self.config.get('playlists', playlist).split(',')
                name, playlist_type, *args = [x.strip() for x in pl]
                try:
                    self.log.debug(f'Loading playlist: {name}')
                    p = playlist_types[playlist_type](
                        self.tabs, self.player_instance, name, *args, cashe=self.cashe)
                    p.pack(expand=1, fill=tkinter.BOTH)
                    self.tabs.add(p, text=name)
                    self.playlists.append(p)
                except KeyError:
                    self.log.warning(f'Faulty playlist type: {playlist_type}')
            
class FilePlayList(tkinter.ttk.Frame):
    def __init__(
        self, master, player_instance, startup_info, cashe, *args, **kwargs):
        self.log = logging.getLogger('MilongaPlayer.PlayList.FilePlayList')
        self.log.info('Initialization of PlayList')
        self.player = player_instance
        self.cashe = cashe
        super().__init__(master, *args, **kwargs)

        buttons = tkinter.ttk.Frame(self)
        buttons.pack(fill=tkinter.X, side='top')
        tkinter.ttk.Button(
            buttons, text='Add file', command=self.add_file).pack(side='left')
        tkinter.ttk.Button(
            buttons, text='Add folder', command=self.add_folder).pack(side='left')
        

        self.view = tkinter.ttk.Treeview(self, show='headings')
        self.view.bind('<Double-1>', self.on_dclick)
        self.view.pack(side='left', expand=1, fill=tkinter.BOTH)
        scrollbar = tkinter.ttk.Scrollbar(
            self, orient='vertical', command=self.view.yview)
        scrollbar.pack(side='left', fill=tkinter.Y)
        self.view.configure(yscrollcommand=scrollbar.set)

        self.on_startup(startup_info)
        self.add_columns(('name',))

    def on_startup(self, startup_info):
        if not startup_info:
            self.files = {}
            self.current_index = None

    def on_close(self):
        pass

    def add_folder(self, path=None):
        path = path or tkinter.filedialog.askdirectory()
        if not path:
            return
        for root, dirs, files in os.walk(path):
            for file in files:
                self.add_file(os.path.join(root, file))

    def add_file(self, path=None):
        path = path or tkinter.filedialog.askopenfilename()
        if not path or not os.path.splitext(path)[1].lower() in ('.mp3', ):
            return
        self.files[path] = {'name': os.path.splitext(os.path.basename(path))[0]}
        item = self.view.insert('', 'end', text=path)
        for key in self.view['columns']:
            try:
                self.view.set(item, key, self.files[path][key])
            except KeyError:
                pass
        
    def add_columns(self, columns, **kwargs):
        # Preserve current column headers and their settings
        current_columns = list(self.view['columns'])
        current_columns = {key:self.view.heading(key) for key in current_columns}

        self.view['columns'] = list(current_columns.keys()) + list(columns)
        for column in columns:
            self.view.heading(column, text=column.capitalize(), **kwargs)

        # Set saved column values for the already existing columns
        for key in current_columns:
            # State is not valid to set with heading
            state = current_columns[key].pop('state')
            self.view.heading(key, **current_columns[key])

        for item in self.view.get_children(''):
            key = self.view.item(item, 'text')
            for column in columns:
                value = self.files[key].get(column, '')
                self.view.set(item, column, value)

    def get_track(self, index=0):
        selection = self.view.selection()
        self.current_index = self.current_index or self.view.get_children()[0]
        if index == 0:
            self.view.selection_set(self.current_index)
            self.view.see(self.current_index)
            return self.view.item(self.current_index, 'text')
        else:
            self.current_index = self.view.next(self.current_index) or self.view.get_children()[0]
            return self.get_track(index-1)
            

    def on_dclick(self, event):
        pass    

                
class PatternPlayList(tkinter.Frame):
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
        self.on_startup(startup_info)
        self.current_track = None
        self.player = player_instance
        self.cashe = cashe
        self.log.info('PlayList initialization Done')

    def on_startup(self, startup_info):
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
        self.log.info(f'Get track with index: {index}')
        if index == 0:
            track = self.current_track or self.playlist[0].next()
            self.current_track = track
            self.log.info(f'Found track {track}')
            return track
        else:
            if not self.playlist[0]:
                self.move_to_last()
                self.current_track = self.playlist[0].next()
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
        pattern =  patternbrowser.PatternBrowser(
            self, 'Pattern Browser', self.pattern).result
        if pattern:
            self.pattern = pattern
            self.log.debug(f'Pattern: {pattern}')
            self.load_pattern()

    def load_pattern(self):
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
        for pattern in self.playlist:
            for path in pattern['paths']:
                self.cashe.pop(path, None)
        self.load_pattern()

    def on_dclick(self, event):
        """
        On double click play the clicked song.
        """
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
            self.current_track = self.playlist[0].playlist.pop(0)
            self.player.play(self.current_track)
        # User has clicked a pattern item
        else:
            self.log.info(f'Double click on pattern {iid}')
            self.move_to_item(iid)
            self.current_track = self.playlist[0].playlist.pop(0) 
            self.player.play(self.current_track)
