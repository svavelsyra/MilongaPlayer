import configparser
import tkinter
import tkinter.filedialog
import tkinter.ttk

from widgets import Dialog

class PatternBrowser(Dialog):
    """Dialog to edit pattern,"""
    def body(self, master, initial_data=None):
        # Top buttons
        button_bar = tkinter.ttk.Frame(master)
        button_bar.pack(side='top', fill=tkinter.X, expand=1)

        load_button = tkinter.ttk.Button(
            button_bar, command=self.load_patterns, text='Load patterns')
        load_button.pack(side='left')

        save_button = tkinter.ttk.Button(
            button_bar, command=self.save_patterns, text='Save patterns')
        save_button.pack(side='left')

        # Main frame
        top = tkinter.ttk.Frame(master)
        top.pack(side='top')

        # Button frame
        buttons = tkinter.ttk.Frame(top)
        tkinter.ttk.Label(buttons).pack(side='top')
        add_pattern = tkinter.ttk.Button(
            buttons, command=self.add_pattern, text='Add pattern')
        add_pattern.pack(fill=tkinter.X)
        edit_pattern = tkinter.ttk.Button(
            buttons, command=self.edit_pattern, text='Edit pattern')
        edit_pattern.pack(fill=tkinter.X)
        move_up = tkinter.ttk.Button(
            buttons, text='Up', command=self.up)
        move_up.pack(fill=tkinter.X)
        add_to_order = tkinter.ttk.Button(
            buttons, text='<--', command=self.add_order)
        add_to_order.pack(fill=tkinter.X)
        remove_from_order = tkinter.ttk.Button(
            buttons, text='-->', command=self.remove_order)
        remove_from_order.pack(fill=tkinter.X)
        move_down = tkinter.ttk.Button(
            buttons, text='Down', command=self.down)
        move_down.pack(fill=tkinter.X)

        # Pattern frame
        right = tkinter.ttk.Frame(top)
        tkinter.ttk.Label(right, text='Patterns').pack(side='top')
        scrollbar=tkinter.ttk.Scrollbar(right, orient=tkinter.VERTICAL)
        self.patterns = tkinter.Listbox(right, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.patterns.yview)
        scrollbar.pack(side='right', fill=tkinter.Y)
        self.patterns.pack(side='top', fill=tkinter.Y)
        self.patterns.data = {}

        # Order frame
        left = tkinter.ttk.Frame(top)
        tkinter.ttk.Label(left, text='Pattern Order').pack(side='top')
        scrollbar=tkinter.ttk.Scrollbar(left, orient=tkinter.VERTICAL)
        self.order = tkinter.Listbox(left, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.order.yview)
        scrollbar.pack(side='right', fill=tkinter.Y)
        self.order.pack(side='top', fill=tkinter.Y)

        # Pack frames
        left.pack(side='left', fill=tkinter.Y)
        buttons.pack(side='left', fill=tkinter.Y)
        right.pack(side='left', fill=tkinter.Y)
        self.load_initial_data(initial_data)

    def add_pattern(self, pattern=None):
        """Add pattern to list of patterns."""
        pattern = pattern or EditPattern(self, 'Add pattern').result
        if pattern:
            name = pattern['name']
            if not self.name_available(name):
                return
            self.patterns.data[pattern['name']] = pattern
            self.patterns.insert('end', pattern['name'])

    def remove_pattern(self):
        """Removes a pattern from list."""
        index = self.patterns.curselection()
        if index:
            key = self.patterns.get(index[0])
            self.data.pop(key)
            self.order.delete(index)

    def up(self):
        """Moves a pattern up in list."""
        index = self.order.curselection()
        if index and index[0]:
            text=self.order.get(index[0])
            self.order.delete(index[0])
            self.order.insert(index[0]-1, text)
            self.order.select_set(index[0]-1)

    def down(self):
        """Moves a pattern down in list"""
        index = self.order.curselection()
        if index and not index[0] == self.order.size() - 1:
            text=self.order.get(index[0])
            self.order.delete(index[0])
            self.order.insert(index[0]+1, text)
            self.order.select_set(index[0]+1)
        
    def edit_pattern(self):
        """Edits a pattern."""
        index = self.patterns.curselection()
        if index:
            name = self.patterns.get(index)
            p = EditPattern(self, 'Edit pattern', self.patterns.data[name])
            result = p.result
            if result and self.name_available(result['name'], name):
                self.patterns.data.pop(name)
                self.patterns.delete(index)
                self.add_pattern(result)
                if name != result['name']:
                    for index, entry in enumerate(self.order.get(0, tkinter.END)):
                        if entry == name:
                            self.order.delete(index)
                            self.order.insert(index, result['name'])
                            

    def name_available(self, name, ok_name=None):
        """Verify that name is avaliable."""
        # Reserved name
        if name == 'pattern_order':
            return False
        # Other names
        return name not in self.patterns.data or (ok_name and name == ok_name)
    
    def clear(self):
        """Clears all lists."""
        self.order.delete(0, 'end')
        self.patterns.delete(0, 'end')
        self.patterns.data = {}

    def load_initial_data(self, initial_data):
        """Loads initial data."""
        if not initial_data:
            return
        for key in initial_data:
            if key == 'pattern_order':
                for name in initial_data[key]:
                    self.order.insert('end',name)
            else:
                self.add_pattern(initial_data[key])
        
    def load_patterns(self):
        """Load pattern from external file."""
        pattern = configparser.ConfigParser()
        path = tkinter.filedialog.askopenfilename()
        if not path:
            return
        pattern.read(path)
        self.clear()
        for section in pattern.sections():
            if section == 'pattern_order':
                for key in [x.strip() for x in
                            pattern.get('pattern_order', 'order').split(',')]:
                    self.order.insert('end', key)
                continue
            
            paths = [x.strip() for x in
                     pattern.get(section, 'paths').split(',')]
            p = {'name': section,
                 'paths': paths,
                 'number': pattern.getint(section, 'number')}
            self.add_pattern(p)

    def save_patterns(self):
        """Save pattern to external file."""
        path = tkinter.filedialog.asksaveasfilename()
        if path:
            pattern_dict = self.create_pattern_dict()
            patterns = configparser.ConfigParser()
            for key in pattern_dict:
                patterns.add_section(key)
                if key == 'pattern_order':
                    patterns.set('pattern_order', 'order', ', '.join(pattern_dict[key]))
                else:
                    patterns.set(key, 'paths', ', '.join(pattern_dict[key]['paths']))
                    patterns.set(key, 'number', str(pattern_dict[key]['number']))
            with open(path, 'w') as fh:
                patterns.write(fh)

    def add_order(self):
        """Add pattern to order list."""
        for index in self.patterns.curselection():
            self.order.insert('end', self.patterns.get(index))

    def remove_order(self):
        """Remove pattern from order list."""
        index = self.order.curselection()
        if index:
            self.order.delete(index)

    def apply(self):
        """Apply to reslut on OK button press."""
        self.result = self.create_pattern_dict()

    def create_pattern_dict(self):
        """The dict to return or save."""
        p = {'pattern_order': self.order.get(0, 'end')}
        for key in self.patterns.get(0, 'end'):
            p[key] = self.patterns.data[key]
        return p

    
class EditPattern(Dialog):
    """Dialog to edit a pattern."""
    def body(self, master, initial_data=None):
        self.paths = []
        self.name = tkinter.StringVar()
        self.name.set('Name')
        buttonbar = tkinter.ttk.Frame(master)
        buttonbar.pack(side='top', fill=tkinter.X)
        add = tkinter.ttk.Button(buttonbar, command=self.add_path, text='Add path')
        add.pack(side='left')
        
        tkinter.ttk.Entry(master, textvariable=self.name).pack(
            side='top', fill=tkinter.X)
        tkinter.ttk.Label(master, text='Repeat number').pack(
            side='top', fill=tkinter.X)
        self.number = tkinter.IntVar()
        self.number.set(3)
        sb = tkinter.ttk.Spinbox(master, to=100, textvariable=self.number)
        sb.pack(side='top', fill=tkinter.X)
        self.path_frame = tkinter.ttk.Frame(master)
        self.path_frame.pack(side='top', fill=tkinter.BOTH)
        if initial_data:
            self.name.set(initial_data['name'])
            self.number.set(initial_data['number'])
            for path in initial_data['paths']:
                self.add_path(path)

    def add_path(self, path=None):
        """Add path to pattern."""
        path = path or tkinter.filedialog.askdirectory()
        if path:
            # Frame.
            f = tkinter.ttk.Frame(self.path_frame)
            f.path = path
            f.pack(side='top', fill=tkinter.X)
            self.paths.append(f)

            # Label.
            l = tkinter.ttk.Label(f, text=path)
            l.pack(side='left', fill=tkinter.X)

            # Close button.
            # ToDo: change to ttk button when a nice theme for close button exists
            b = tkinter.Button(
                f, text='X', relief='flat', command=lambda f=f: self.remove(f))
            b.pack(side='right')

    def remove(self, widget):
        """Remove path from pattern."""
        for index, w in enumerate(self.paths):
            if w == widget:
                self.paths.pop(index)
                widget.destroy()

    def apply(self):
        """Apply result on OK button press."""
        self.result = {'name': self.name.get(),
                       'paths': [l.path for l in self.paths],
                       'number': self.number.get()}
