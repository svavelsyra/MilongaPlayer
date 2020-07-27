import configparser
import logging
import os
import pickle
import tkinter
import tkinter.ttk

import convert
import player
import playlist

VERSION = '1.0.0'

class Gui():
    def __init__(self, master, player_instance):
        self.init_ok = False
        self.master = master
        self.log = logging.getLogger('MilongaPlayer')
        self.config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        config = self.load_config()
        self.master.winfo_toplevel().title(f"Milonga Player {VERSION}")
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        p = ContiniousPlayer(self.master, player_instance)

        # Playlists.
        upper = tkinter.ttk.Frame(master)
        self.playlist = playlist.PlayList(upper, p, config)
        
        # Player controlls.
        bottom = tkinter.ttk.Frame(master)
        self.controlls = PlayerControlls(bottom, p)

        # Status bar.
        status_bar = StatusBar(master, player_instance)
        status_bar.pack(side='top', fill=tkinter.X)

        upper.pack(fill=tkinter.BOTH, expand=1, side='top')
        bottom.pack(fill=tkinter.X, side='bottom')
        self.playlist.pack(fill=tkinter.BOTH, expand=1, side='left')
        self.controlls.pack()
        self.init_ok = True
        self.log.info('Initialization done!')

    def load_config(self):
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

    def on_close(self, *args, **kwargs):
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
            self.log.debug('Done gathering close down info')
            self.playlist.on_close(config)
            with open(self.config_path, 'w') as fh:
                config.write(fh)
                self.log.debug(f'Close down info written to: {self.config_path}')
        except Exception as err:
            self.log.error('Something bad happened during shutdown', exc_info=True)
        finally:
            self.master.destroy()
            self.log.info('Shutdown')
            logging.shutdown()

    def add_playlist(self, pl_type):
        self.playlist.add_playlist(pl_type)

            
class StatusBar(tkinter.Frame):
    def __init__(self, master, player_instance, *args, **kwargs):
        self.log = logging.getLogger('MilongaPlayer.StatusBar')
        self.log.info('initializing Status Bar')
        super().__init__(master, *args, **kwargs)
        self.player_instance = player_instance
        self.name = tkinter.StringVar()
        self.position = tkinter.IntVar()
        self.time = tkinter.StringVar()
        tkinter.Label(self, textvar=self.time).pack()
        tkinter.Scale(self,
                      to=1000,
                      orient=tkinter.HORIZONTAL,
                      showvalue=0,
                      variable=self.position,
                      command=self.slider_callback).pack(fill=tkinter.X)
        tkinter.Label(self, textvar=self.name).pack()
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

    def replace(self, text):
        """
        Replace various quotings with correct values.
        """
        for old, new in (('%20', ' '), ('%27', "'")):
            text = text.replace(old, new)
        return text

    def worker(self):
        """Continiously update the status."""
        media = self.player_instance.get_media()
        if media:
            path = self.replace(media.get_mrl())
            name = os.path.basename(path)
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
        track = self.get_next_track()
        self.log.debug(f'Next track: {track}')
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

    def get_next_track(self):
        """
        Get next track from playlist.
        """
        self.log.info('Get next track')
        return self.get_track(1)

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
        track = self.get_next_track()
        if not track:
            self.log.warning('Worker unable to get next track')
            return
        self.log.info(f'Worker playing track: {track}')
        self.player_instance.play(track)
        self.master.after(100, self.worker)

class PlayerControlls(tkinter.Frame):
    """
    Player controll buttons.
    """
    def __init__(self, master, player_instance, *args, **kwargs):
        self.log = logging.getLogger('MilongaPlayer.PlayerControlls')
        self.log.info('Initializing PlayerControlls')
        super().__init__(master, *args, **kwargs)
        self.player = player_instance
        tkinter.Button(self, text='Play', command=self.player.play).pack(side='left')
        tkinter.Button(self, text='Stop', command=self.player.stop).pack(side='left')
        tkinter.Button(self, text='Next', command=self.player.next).pack(side='left')
        self.log.info('Done initializing PlayerControlls')



if __name__ == '__main__':
    convert.convert()
    with player.Player() as p:
        tk = tkinter.Tk()
        gui = Gui(tk, p)
        tk.mainloop()
