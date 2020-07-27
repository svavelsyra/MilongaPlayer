import logging
import os
import tkinter
import tkinter.simpledialog
import tkinter.ttk

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
            buttons, text='Add files', command=self.add_files).pack(side='left')
        tkinter.ttk.Button(
            buttons, text='Add folder', command=self.add_folder).pack(side='left')
        

        self.view = tkinter.ttk.Treeview(self, show='headings')
        self.view.bind('<ButtonPress-1>', self.on_click)
        self.view.bind('<Control-ButtonPress-1>', self.on_ctrl_click)
        self.view.bind('<Control-a>', self.select_all)
        self.view.bind('<B1-Motion>', self.on_move)
        self.view.bind('<Double-1>', self.on_dclick)
        self.view.bind('<Delete>', self.on_delete)
        self.view.pack(side='left', expand=1, fill=tkinter.BOTH)
        scrollbar = tkinter.ttk.Scrollbar(
            self, orient='vertical', command=self.view.yview)
        scrollbar.pack(side='left', fill=tkinter.Y)
        self.view.configure(yscrollcommand=scrollbar.set)

        self.on_startup(startup_info)

    def on_startup(self, startup_info):
        if not startup_info:
            startup_info = {'name': 'Playlist',
                            'files': {},
                            'current_index': None,
                            'playlist': [],
                            'columns': ['name']}
        for key in ('files', 'current_index', 'name'):
            setattr(self, key, startup_info[key])
        self.add_columns(startup_info['columns'])
        for iid, path, values in startup_info['playlist']:
            self.view.insert('', 'end', iid=iid, text=path)
            for key, value in values.items():
                self.view.set(iid, key, value)
        try:
            self.view.selection_set(self.current_index)
            self.view.see(self.current_index)
        except:
            pass
            
    def on_close(self):
        startup_info = {'type': 'File'}
        for key in ('files', 'current_index', 'name'):
            startup_info[key] = getattr(self, key)
        startup_info['playlist'] = []
        startup_info['columns'] = self.view['columns']
        for child in self.view.get_children():
            text = self.view.item(child, 'text')
            values = {key: self.view.set(child, key) for key in startup_info['columns']}
            startup_info['playlist'].append((child, text, values))
        return startup_info

    def add_folder(self, path=None):
        path = path or tkinter.filedialog.askdirectory()
        if not path:
            return
        for root, dirs, files in os.walk(path):
            if files:
                self.add_files([os.path.join(root, file) for file in files])

    def add_files(self, paths=None):
        paths = paths or tkinter.filedialog.askopenfilename(multiple=True,
                                                            filetypes=(('MP3', '*.mp3'),))
        for path in paths:
            if not os.path.splitext(path)[1].lower() in ('.mp3', ):
                continue
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
        self.current_index = self.current_index or self.view.get_children()[0]
        if index == 0:
            self.view.selection_set(self.current_index)
            self.view.see(self.current_index)
            return self.view.item(self.current_index, 'text')
        else:
            self.current_index = self.view.next(self.current_index) or self.view.get_children()[0]
            return self.get_track(index-1)
            
    def on_click(self, event):
        tv = event.widget
        tv.selection_set(tv.identify_row(event.y))

    def on_ctrl_click(self, event):
        iid = self.view.identify_row(event.y)
        current_selection = self.view.selection()
        return
        if iid in current_selection:
            self.view.selection_remove((iid, ))
        else:
            self.view.selection_add((iid, ))

    def on_move(self, event):
        tv = event.widget
        moveto = tv.index(tv.identify_row(event.y))
        tv.move(tv.selection(), '', moveto)

    def on_dclick(self, event):
        iid = self.view.identify('item', event.x, event.y)
        self.current_index = iid
        path = self.view.item(iid, 'text')
        self.player.play(path)

    def on_delete(self, event):
        to_delete = self.view.selection()
        if self.current_index in to_delete:
            self.current_index = self.view.next(to_delete[-1]) or self.view.get_children()[0]
        self.view.delete(*to_delete)

    def select_all(self, event):
        self.view.selection_set(self.view.get_children())
            
