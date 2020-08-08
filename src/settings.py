import tkinter
import tkinter.ttk

from widgets import Dialog, SetKey

class SettingsDialog(Dialog):
    """
    Settings dialog, set settings for the application.
    """
    @staticmethod
    def defaults():
        return {'general': General.defaults(),
                'key_bindings': KeyBindings.defaults()}
    
    def body(self, master, initial_data=None):
        """Body of the dialog."""
        top = tkinter.ttk.Frame(master)
        top.pack(side='top')
        
        self.view = tkinter.ttk.Treeview(top)
        self.view.pack(side='left', fill=tkinter.Y, expand=1)
        self.settings_frame = tkinter.ttk.Frame(top)
        self.settings_frame.pack(side='left', fill=tkinter.BOTH, expand=1)
        self.frames = {
            'general': General(
                self.settings_frame, initial_data['general']),
            'key_bindings': KeyBindings(
                self.settings_frame, initial_data['key_bindings'])}
        self.setup_view()

    def setup_view(self):
        """Add the different views to the dialog"""
        def add_categories(root, categories):
            for name in categories:
                if isinstance(name, str):
                    self.view.insert(root, 'end', text=name)
                else:
                    iid = self.view.insert(root, 'end', text=name)
                    self.add_categories(iid, name[1:])

        add_categories('', ('General', 'Key bindings'))
        self.view.bind('<Button-1>', self.switch_frame)

    def switch_frame(self, event):
        """Switch between frames on mouse click."""
        iid = self.view.identify_row(event.y)
        for child in self.settings_frame.winfo_children():
            child.pack_forget()
        frame = self.frames[self.view.item(iid, 'text').lower().replace(' ', '_')]
        frame.pack(expand=1, fill=tkinter.BOTH)

    def apply(self):
        '''Apply result if OK has been pressed.'''
        self.result = {}
        for key in self.frames:
            if self.frames[key].changed:
                self.result[key] = self.frames[key].result

class General(tkinter.ttk.Frame):
    """General preferences frame."""
    def __init__(self, master, initial_data, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.changed = False

    @property
    def result(self):
        return {}
    
    @staticmethod
    def defaults():
        return {}

class KeyBindings(tkinter.ttk.Frame):
    """Keybindings frame."""
    def __init__(self, master, initial_data, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.changed = False
        self.view = tkinter.ttk.Treeview(self, columns=('Binding'))
        self.view.pack(fill=tkinter.BOTH, expand=1)
        for col in self.view['columns']:
            self.view.heading(col, text=col)
        self.view.heading('#0', text='Action')
        self.view.bind('<Button-1>', self.set_key)
        self.set_bindings(initial_data)

    @property
    def result(self):
        """Result of dialog."""
        result = {}
        for c_iid in self.view.get_children(''):
            category = self.view.item(c_iid, 'text')
            result[category] = tuple((self.view.item(key, 'text'),
                                      self.view.set(key, 'Binding'))
                                     for key in self.view.get_children(c_iid))
        return result

    @staticmethod
    def defaults():
        """Default keybindings."""
        return {'Playlist': (('Select all', '<Control-a>'),
                             ('Delete', '<Delete>'))}

    def set_bindings(self, bindings):
        """Create view of all bindings."""
        for category, action_list in bindings.items():
            iid = self.view.insert('', 'end', text=category)
            for action, default in action_list:
                sub_iid = self.view.insert(
                    iid, 'end', text=action, values=(default, ))
                self.view.see(sub_iid)
        self.view.see('')

    def set_key(self, event):
        """Ask user for new keybinding."""
        tw = event.widget
        iid = tw.identify_row(event.y)
        if not self.view.get_children(iid):
            current = self.view.set(iid, 'Binding')
            result = SetKey(self, 'Set key', current).result
            if result is not None and current != result:
                self.changed = True
                self.view.set(iid, 'Binding', result)
