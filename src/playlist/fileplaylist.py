import logging
import os
import random
import tkinter
import tkinter.simpledialog
import tkinter.ttk

class FilePlayList(tkinter.ttk.Frame):
    """Standard playlist."""
    def __init__(
        self, master, player_instance, startup_info, cashe, *args, **kwargs):
        self.log = logging.getLogger('MilongaPlayer.PlayList.FilePlayList')
        self.log.info('Initialization of PlayList')
        self.player = player_instance
        self.cashe = cashe
        self.queue = []
        super().__init__(master, *args, **kwargs)

        buttons = tkinter.ttk.Frame(self)
        buttons.pack(fill=tkinter.X, side='top')
        tkinter.ttk.Button(
            buttons, text='Add files', command=self.add_files).pack(side='left')
        tkinter.ttk.Button(
            buttons, text='Add folder', command=self.add_folder).pack(side='left')
        self.random = tkinter.IntVar()
        tkinter.ttk.Checkbutton(
            buttons, variable=self.random, text='Random').pack(side='left')
        

        self.view = tkinter.ttk.Treeview(self, show='headings')
        self.view.bind('<ButtonPress-1>', self.on_click)
        self.view.bind('<ButtonPress-3>', self.on_right_click)
        self.view.bind('<Control-ButtonPress-1>', self.on_ctrl_click)
        self.view.bind('<B1-Motion>', self.on_move)
        self.view.bind('<Double-1>', self.on_dclick)
        self.view.pack(side='left', expand=1, fill=tkinter.BOTH)
        scrollbar = tkinter.ttk.Scrollbar(
            self, orient='vertical', command=self.view.yview)
        scrollbar.pack(side='left', fill=tkinter.Y)
        self.view.configure(yscrollcommand=scrollbar.set)
        self.add_columns(('queue', 'name'))
        self.view.column('queue', width=60, stretch=False)
        self.view.heading('queue', text='')

        self.on_startup(startup_info)

        # Development stuff
        for iid in self.view.get_children():
            self.view.set(iid, 'queue', '')
        self.queue = []

    def on_startup(self, startup_info):
        """Run once on startup to set files and settings."""
        if not startup_info:
            startup_info = {'name': 'Playlist',
                            'files': {},
                            'current_index': None,
                            'playlist': [],
                            'columns': ['name'],
                            'settings': {}}
        for key, default in (('files', {}),
                             ('current_index', None),
                             ('name', 'Playlist'),
                             ('queue', [])):
            value = startup_info.get(key, default)
            setattr(self, key, value)
        value = startup_info.get('columns', ['queue', 'name'])
        self.log.info(f'Showing columns: {value}')
        self.view['displaycolumns'] = value
        for iid, path, values in startup_info.get('playlist', []):
            self.view.insert('', 'end', iid=iid, text=path)
            for key, value in values.items():
                self.view.set(iid, key, value)
        for setting, default in (('random', False),):
            value = startup_info.get('settings', {}).get(setting, default)
            self.log.info(f'Setting self.{setting} to {value}')
            getattr(self, setting).set(value)
        try:
            self.view.selection_set(self.current_index)
            self.view.see(self.current_index)
        except:
            pass
            
    def on_close(self):
        """Run on close to save state and settings."""
        startup_info = {'type': 'File'}
        for key in ('files', 'current_index', 'name', 'queue'):
            startup_info[key] = getattr(self, key)
        startup_info['playlist'] = []
        startup_info['columns'] = self.view['columns']
        for child in self.view.get_children():
            text = self.view.item(child, 'text')
            values = {key: self.view.set(child, key) for key in startup_info['columns']}
            startup_info['playlist'].append((child, text, values))
        startup_info['settings'] = {}
        for setting in ('random',):
            startup_info['settings'][setting] = getattr(self, setting).get()
        return startup_info

    def add_folder(self, path=None):
        """Add the files from folder to playlist."""
        path = path or tkinter.filedialog.askdirectory()
        if not path:
            self.log.info('User canceled')
            return
        for root, dirs, files in os.walk(path):
            files = [os.path.join(root, file) for file in
                     files if file.endswith('.mp3')]
            if files:
                self.add_files(files)

    def add_files(self, paths=None):
        """Add one or more files to playlist."""
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
        """Add data columns."""
        # Preserve current column headers and their settings
        current_columns = list(self.view['columns'])
        current_columns = {key:self.view.heading(key) for key in current_columns}
        self.log.info(f'Current columns: {current_columns}')

        self.view['columns'] = list(current_columns.keys()) + list(columns)
        for column in columns:
            self.log.info('Adding column: {column}')
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
        """
        Get track to play.

        Index > 0 gets that amount of tracks forward in list."""
        if self.queue:
            self.decrement_queue_index()
            iid = self.queue.pop(0)
            self.view.selection_set(iid)
            self.view.see(iid)
            return self.view.item(iid, 'text')
        if not self.current_index:
            self.current_index = (self.view.get_children() or [None])[0]
        if not self.current_index:
            return ''
        if self.random.get():
            self.current_index = random.choice(self.view.get_children())
            index = 0
        
        if index == 0:
            self.view.selection_set(self.current_index)
            self.view.see(self.current_index)
            return self.view.item(self.current_index, 'text')
        elif index > 0:
            self.current_index = self.view.next(self.current_index) or self.view.get_children()[0]
            return self.get_track(index-1)
        else:
            self.current_index = self.view.prev(self.current_index) or self.view.get_children()[-1]
            return self.get_track(index+1)
        
    def on_click(self, event):
        """
        On left click in view.

        Select single element in list.
        """
        region = self.view.identify("region", event.x, event.y)
        if region == 'heading':
            # Do Sorting here
            return
        tv = event.widget
        tv.selection_set(tv.identify_row(event.y))

    def on_ctrl_click(self, event):
        """
        On ctrl-leftclick in view.

        Multiselect.
        """
        region = self.view.identify("region", event.x, event.y)
        if region == 'heading':
            return
        iid = self.view.identify_row(event.y)
        current_selection = self.view.selection()
        return
        if iid in current_selection:
            self.view.selection_remove((iid, ))
        else:
            self.view.selection_add((iid, ))

    def on_right_click(self, event):
        """Right click context menu."""
        region = self.view.identify('region', event.x, event.y)
        if region == 'heading':
            return
        
        iid = self.view.identify('item', event.x, event.y)
        if not iid in self.view.selection():
            self.view.selection_set(iid)

        menu = tkinter.Menu(self, tearoff=0)
        menu.add_command(label='Enqueue', command=self.enqueue)
        menu.add_command(label='Dequeue', command=self.dequeue)
        menu.add_command(label='Delete', command=self.delete)
        try:
            menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            menu.grab_release()

    def on_move(self, event):
        """Move element in list."""
        tv = event.widget
        moveto = tv.index(tv.identify_row(event.y))
        tv.move(tv.selection(), '', moveto)

    def on_dclick(self, event):
        """On double click play that track."""
        region = self.view.identify('region', event.x, event.y)
        if region == 'heading':
            return
        iid = self.view.identify('item', event.x, event.y)
        self.current_index = iid
        path = self.view.item(iid, 'text')
        self.player.play(path)

    def delete(self, event=None):
        """Delete selection key binding."""
        to_delete = self.view.selection()
        if self.current_index in to_delete:
            self.current_index = self.view.next(to_delete[-1]) or self.view.get_children()[0]
        self.view.delete(*to_delete)

    def select_all(self, event):
        """Select all keybinding."""
        self.view.selection_set(self.view.get_children())

    def decrement_queue_index(self):
        for iid in set(self.queue):
            indexes = self.view.set(iid, 'queue').split(',')
            new_indexes = []
            for index in indexes:
                if index:
                    index = int(index) - 1
                if index:
                    new_indexes.append(str(index))
            self.view.set(iid, 'queue', ','.join(new_indexes))

    def dequeue(self, event=None):
        self.queue.reverse()
        for iid in self.view.selection():
            try:
                self.queue.remove(iid)
            except ValueError:
                pass
            else:
                new = ','.join(self.view.set(iid, 'queue').split(',')[:-1])
                self.view.set(iid, 'queue', new)
        self.queue.reverse()
            

    def enqueue(self, event=None):
        """Enque file to play"""
        for iid in self.view.selection():
            self.queue.append(iid.strip())
            current = self.view.set(iid, 'queue')
            if current:
                current += ','
            current += str(len(self.queue))
            self.view.set(iid, 'queue', current)
            
            
