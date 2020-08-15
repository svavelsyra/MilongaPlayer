import configparser
import logging
import os
import pickle
import sys
import tkinter
import tkinter.ttk

import player
import playlist
import settings
import statuswindow

VERSION = '1.7.0'

class Gui():
    def __init__(self, master, player_instance):
        self.init_ok = False
        self.master = master
        self.log = logging.getLogger('MilongaPlayer')
        self.config_path = os.path.join(self.data_path, 'config.ini')
        config = self.load_config()
        startup_info = self.on_startup()
        self.master.winfo_toplevel().title(f"Milonga Player {VERSION}")
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        self.player = ContiniousPlayer(self.master, player_instance)

        # Playlists.
        upper = tkinter.ttk.Frame(master)
        tkinter.Button(upper, command=self.configure, text='Settings').pack()
        self.playlist = playlist.PlayList(
            upper, self.player, startup_info.get('playlists', {}))
        
        # Player controlls.
        bottom = tkinter.ttk.Frame(master)
        self.controlls = PlayerControlls(bottom, self.player)

        # Status bar.
        status_bar = StatusBar(master, player_instance)
        status_bar.pack(side='top', fill=tkinter.X)

        upper.pack(fill=tkinter.BOTH, expand=1, side='top')
        bottom.pack(fill=tkinter.X, side='bottom')
        self.playlist.pack(fill=tkinter.BOTH, expand=1, side='left')
        self.controlls.pack()

        self.key_bindings()

        statuswindow.StatusWindow(self.master, player_instance)
        self.init_ok = True
        self.log.info('Initialization done!')

    @property
    def data_path(self):
        """Path to where data is stored."""
        if sys.platform == 'win32':
            path = r'\AppData\Local\MilongaPlayer'
        else:
            path = '/.milongaplayer'
        return os.path.expanduser(f'~{path}')

    def key_bindings(self):
        """Set keybindings."""
        def set_binding(obj, values):
            for name in values:
                binding = self.settings.get('key_bindings', {}).get(name, values[name])
                name = name.lower().replace(' ', '_')
                self.log.debug('Setting {key=} for {binding=}')
                self.master.bind(
                    binding,
                    lambda event, name=name: obj.key_event(name, event))
                    
        for section, values in settings.SettingsDialog.defaults()['key_bindings'].items():
            self.log.debug('Handling keybindings for section: {section}')
            if 'playlist' in section.lower():
                set_binding(self.playlist, values)
            if 'playback' in section.lower():
                set_binding(self.player, values)

    def configure(self):
        """Configure settings."""
        new_settings = settings.SettingsDialog(self.master, 'Settings', self.settings)
        self.log.info(f'New settings: {new_settings.result}')
        if not new_settings.result:
            return
        for key, value in new_settings.result.items():
            self.settings[key] = value
            getattr(self, key)(value)

    def load_config(self):
        """Load saved config from config file."""
        config = configparser.ConfigParser()
        config.read(self.config_path)
        log_level = config.get('logging', 'log_level', fallback='INFO')
        log_format = '{levelname}:{asctime}: {name}.{funcName}: {message}'
        log_format = config.get('logging', 'log_format', fallback=log_format)
        logging.basicConfig(level='INFO', format=log_format, style='{')
        self.log.info(f'Starting MilongaPlayer version {VERSION}')
        self.log.info(f'Loading Config: {self.config_path}')
        self.log.info(f'Set log level: {log_level}')
        self.log.setLevel(log_level)
        state = config.get('window', 'state', fallback='normal')
        height = config.getint('window', 'height', fallback=300)
        width = config.getint('window', 'width', fallback=250)
        posx = config.getint('window', 'posx', fallback=0)
        posy = config.getint('window', 'posy', fallback=0)
        self.log.debug(f'{state=}, {height=}, {width=}, {posx=}, {posy=}')
        # First set saved windowed size and pos then set state.
        self.master.geometry(f'{width}x{height}+{posx}+{posy}')
        self.master.state(state)
        return config

    def on_startup(self, *args, **kwargs):
        """
        Run only once uppon startup.

        Sets various saved states from last run.
        """
        try:
            path = os.path.join(self.data_path, 'startup_info.dat')
            self.log.info(f'Reading startup info from: {path}')
            with open(path, 'br') as fh:
                startup_info = pickle.load(fh)
        except:
            self.log.error('Error during startup:', exc_info=True)
            startup_info = {}
        for key, default in (('settings', settings.SettingsDialog.defaults()),):
            value = startup_info.get('main', {}).get(key, default)
            self.log.debug(f'Setting: self.{key} to {value}')
            setattr(self, key, value)
        return startup_info
            
    def on_close(self, *args, **kwargs):
        """Save state on close."""
        try:
            if not self.init_ok:
                return
            self.log.info('Closing application')
            config = configparser.ConfigParser()
            result = config.read(self.config_path)
            self.log.debug(f'Read config file: {result}')
            for section in ('window',):
                try:
                    config.add_section(section)
                except configparser.DuplicateSectionError:
                    pass
            config.set('window', 'state', self.master.state())
            # First save state, then switch to normal so that we can save
            # those sizes.
            self.master.state('normal')
            config.set('window', 'height', str(self.master.winfo_height()))
            config.set('window', 'width', str(self.master.winfo_width()))
            config.set('window', 'posx', str(self.master.winfo_x()))
            config.set('window', 'posy', str(self.master.winfo_y()))
            self.log.debug('Done gathering close down info, saving...')
            os.makedirs(self.data_path, exist_ok=True)
            with open(self.config_path, 'w') as fh:
                config.write(fh)
                self.log.debug(f'Close down info written to: {self.config_path}')
            with open(os.path.join(self.data_path, 'startup_info.dat'), 'bw') as fh:
                pickle.dump({'main': {'settings': self.settings},
                             'playlists': self.playlist.on_close()},
                            fh)
        except Exception as err:
            self.log.error('Something bad happened during shutdown', exc_info=True)
        else:
            self.log.info('Close down info saved successfully')
        finally:
            self.master.destroy()
            self.log.info('Shutting down!')
            logging.shutdown()

    def add_playlist(self, pl_type):
        """Add playlist of the requested type."""
        self.log.info(f'Addning playlist of type: {pl_type}')
        self.playlist.add_playlist(pl_type)

            
class StatusBar(tkinter.ttk.Frame):
    """Display status of play."""
    def __init__(self, master, player_instance, *args, **kwargs):
        self.log = logging.getLogger('MilongaPlayer.StatusBar')
        self.log.info('initializing Status Bar')
        super().__init__(master, *args, **kwargs)
        self.player_instance = player_instance
        self.name = tkinter.StringVar()
        self.position = tkinter.IntVar()
        self.time = tkinter.StringVar()
        tkinter.ttk.Label(self, textvar=self.time).pack()
        tkinter.Scale(self,
                      to=1000,
                      orient=tkinter.HORIZONTAL,
                      showvalue=0,
                      variable=self.position,
                      command=self.slider_callback).pack(fill=tkinter.X)
        tkinter.ttk.Label(self, textvar=self.name).pack()
        self.log.info('Starting worker in Status Bar')
        self.worker()
        self.log.info('Status Bar initialization done')

    def slider_callback(self, value):
        """
        Callback to be called when user move slider to set position
        in the media.
        """
        self.player_instance.set_position(int(value)/1000)

    def update_time(self, media):
        """
        Update time/duration values.
        """
        def convert_time(ms):
            hours = ms//(60*60*1000)
            minutes = (ms//(1000*60))%(60*60)
            secs = (ms//1000)%60
            return ':'.join([str(x).zfill(2) for x in (hours, minutes, secs)])
        duration = convert_time(media.get_duration())
        current_time = convert_time(max(0, self.player_instance.get_time()))
        self.time.set(f'{current_time}/{duration}')

    def worker(self):
        """Continiously update the status."""
        media = self.player_instance.get_media()
        if media:
            name = os.path.basename(self.player_instance.current_track)
            self.name.set(name)
            self.position.set(self.player_instance.get_position()*1000)
            self.update_time(media)
        self.after(100, self.worker)

class ContiniousPlayer():
    """
    Play music tracks continously.
    """
    def __init__(self, master, player_instance):
        self.log = logging.getLogger('MilongaPlayer.ContiniousPlayer')
        self.log.info('Initializing ContiniousPlayer')
        self.master = master
        self.player_instance = player_instance
        self.playing = False
        self.paused = False
        self.log.info('initialization of ContinousPlayer done')

    def play(self, track=None):
        """
        Start to play current track.
        Toggles Pause status if paused.
        """
        self.log.info(f'Play: {track=}, {self.playing=}, {self.paused=}')
        if self.playing and not track:
            self.paused = not self.paused
            self.log.debug(f'Setting pause to: {self.paused}')
            self.player_instance.set_pause(self.paused)
            return
        else:
            self.playing = True
            self.paused = False
            self.player_instance.set_pause(False)
            track = track or self.get_track()
            if not track:
                self.log.warning('Play unable to get track')
                return
            self.player_instance.play(track)
            self.worker()

    def stop(self):
        """
        Stops playback.
        """
        self.log.info('Stop')
        self.playing = False
        self.paused = False
        self.player_instance.stop()

    def next(self):
        """
        Change to next track.
        """
        self.log.info('Next')
        track = self.get_track(1)
        self.log.debug(f'Next track: {track}')
        self.set_track(track)

    def previous(self):
        """
        Change to previous track.
        """
        self.log.info('Previous')
        track = self.get_track(-1)
        self.log.debug(f'Previous track: {track}')
        self.set_track(track)


    def set_track(self, track):
        """
        Set track to the specified track.
        """
        if not track:
            self.log.warning('Could not find next track')
            return
        if self.playing:
            self.log.debug('Is already playing, continue with next track')
            self.player_instance.stop()
            self.player_instance.play(track)
        else:
            self.log.debug('Is not playing, set next track without playing')
            self.player_instance.set_mrl(track)
        

    def worker(self):
        """
        Worker "thread" to continiously play.
        """
        if not self.playing:
            self.log.info('Worker stopping')
            self.player_instance.stop()
            return
        if self.paused or self.player_instance.is_playing():
            self.master.after(100, self.worker)
            return
        track = self.get_track(1)
        if not track:
            self.log.warning('Worker unable to get next track')
            return
        self.log.info(f'Worker playing track: {track}')
        self.player_instance.play(track)
        self.master.after(100, self.worker)

    def key_event(self, target, event):
        """Set keybinding"""
        self.log.info(f'Key event: {target}({event})')
        try:
            getattr(self, target)()
        except AttributeError:
            self.log.info(f'Missing attribute: self.{target}')

class PlayerControlls(tkinter.ttk.Frame):
    """
    Player controll buttons.
    """
    def __init__(self, master, player_instance, *args, **kwargs):
        self.log = logging.getLogger('MilongaPlayer.PlayerControlls')
        self.log.info('Initializing PlayerControlls')
        super().__init__(master, *args, **kwargs)
        self.player = player_instance
        tkinter.ttk.Button(
            self, text='Play', command=self.player.play).pack(side='left')
        tkinter.ttk.Button(
            self, text='Stop', command=self.player.stop).pack(side='left')
        tkinter.ttk.Button(
            self, text='Next', command=self.player.next).pack(side='left')
        self.log.info('Done initializing PlayerControlls')
        

if __name__ == '__main__':
    errors = []
    version = sys.version_info
    if not (version.major >= 3 and version.minor >= 8):
        errors.append(f"Python version has to be 3.8 or above, it's currently {sys.version}")
    if not 'vlc' in sys.modules:
        errors.append('VLC module is required, see readme on how to install')
    if errors:
        tk = tkinter.Tk()
        tk.withdraw()
        tkinter.messagebox.showerror("Error", '\n'.join(errors))
        tk.destroy()
    else:
        try:
            with player.Player() as p:
                tk = tkinter.Tk()
                gui = Gui(tk, p)
                tk.mainloop()
        except Exception as error:
            tk = tkinter.Tk()
            tk.withdraw()
            tkinter.messagebox.showerror("Error", error)
            tk.destroy()
            logging.getLogger('MilongaPlayer').error(error, exc_info=True)
